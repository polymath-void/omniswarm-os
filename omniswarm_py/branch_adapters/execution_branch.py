import sys
import os
import asyncio
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_fastembed_model = None

def get_embedding_model():
    global _fastembed_model
    if _fastembed_model is None:
        try:
            from fastembed import TextEmbedding
            _fastembed_model = TextEmbedding(model_name=MODEL_NAME)
        except Exception as e:
            print(f"[ExecutionBranch:ComputeRes] Notice loading FastEmbed: {e}")
    return _fastembed_model

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ComputeResHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet HTTP logging
        pass

    def do_GET(self):
        if self.path in ["/health", "/healthz", "/"]:
            payload = {
                "status": "ok",
                "service": "ComputeRes-OS Shared Compute Host",
                "model": MODEL_NAME,
                "dimension": 384,
                "timestamp": time.time()
            }
            res_bytes = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res_bytes)))
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res_bytes)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            body = {}

        if self.path in ["/v1/embeddings", "/embeddings"]:
            input_data = body.get("input", "")
            texts = [input_data] if isinstance(input_data, str) else (input_data if isinstance(input_data, list) else [str(input_data)])
            model = get_embedding_model()
            t0 = time.time()
            if model:
                embeddings_iter = model.embed(texts)
                data_items = [
                    {"object": "embedding", "embedding": vec.tolist() if hasattr(vec, "tolist") else list(vec), "index": idx}
                    for idx, vec in enumerate(embeddings_iter)
                ]
            else:
                data_items = [{"object": "embedding", "embedding": [0.0]*384, "index": idx} for idx, _ in enumerate(texts)]
            elapsed_ms = round((time.time() - t0) * 1000, 2)

            response = {
                "object": "list",
                "data": data_items,
                "model": MODEL_NAME,
                "usage": {"prompt_tokens": len(texts), "total_tokens": len(texts)},
                "compute_time_ms": elapsed_ms
            }
            res_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res_bytes)))
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res_bytes)

        elif self.path in ["/completion", "/v1/completions"]:
            prompt = body.get("prompt", "")
            response = {
                "content": f"[ComputeRes Shared Compute: Processed prompt length {len(prompt)}]",
                "model": MODEL_NAME,
                "finish_reason": "stop"
            }
            res_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res_bytes)))
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res_bytes)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()

class ComputeResExecutionBranch:
    """
    Natively integrates ComputeRes as Branch 2 in OmniSwarm.
    Provides ZeroMQ IPC Broker, WASM/Python sandboxed execution,
    SkillsHub registry routing, and HTTP Model Offloading for edge nodes.
    """
    def __init__(self, compute_res_path: str, ctx=None):
        self.compute_res_path = compute_res_path
        if compute_res_path not in sys.path:
            sys.path.insert(0, compute_res_path)

        import zmq.asyncio
        self.ctx = ctx or zmq.asyncio.Context()

        from compute_res.network.mesh import WebRTCMeshRouter
        from compute_res.oracle.consensus import SwarmOracle

        self.broker = WebRTCMeshRouter(node_id="execution_branch", swarm_id="omniswarm")
        self.oracle = SwarmOracle(node_id="execution_branch")

        self.ipc_broker = None
        self.t_broker = None
        self.t_ipc_broker = None
        self.t_worker = None
        self.httpd = None
        self.http_thread = None

    async def boot_branch(self):
        print("[Branch 2: ComputeRes Execution] Booting IPC Broker, Worker & WebRTC Mesh...")
        
        # 1. Boot ComputeRes ZeroMQ IPC Broker (tcp://127.0.0.1:5557 / 5558)
        try:
            from compute_res.core.broker import IPCBroker
            from compute_res.orchestration.kernel import worker_backend
            self.ipc_broker = IPCBroker()
            self.t_ipc_broker = asyncio.create_task(self.ipc_broker.start())
            await asyncio.sleep(0.1)
            self.t_worker = asyncio.create_task(worker_backend())
            print("[Branch 2: ComputeRes Execution] ZeroMQ IPC Broker active on :5557/:5558")
        except Exception as e:
            print(f"[Branch 2: ComputeRes Execution] Notice on IPC Broker: {e}")

        # 2. Boot WebRTC Mesh Router
        try:
            self.t_broker = asyncio.create_task(self.broker.start())
        except Exception as e:
            print(f"[Branch 2: ComputeRes Execution] Notice on WebRTC Router: {e}")

        # 3. Boot Shared Model HTTP Gateway (0.0.0.0:57161)
        try:
            self.httpd = ThreadedHTTPServer(("0.0.0.0", 57161), ComputeResHTTPHandler)
            self.http_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.http_thread.start()
            print("[Branch 2: ComputeRes Execution] Shared Compute Model Gateway online on http://0.0.0.0:57161")
        except Exception as e:
            print(f"[Branch 2: ComputeRes Execution] Notice on HTTP Gateway: {e}")

        # Preload embedding model in background
        asyncio.create_task(asyncio.to_thread(get_embedding_model))

    async def dispatch_intent(self, agent_id: bytes, intent_payload: dict):
        intent_type = intent_payload.get("type")
        args = intent_payload.get("args", {})

        # 1. Dynamic Python Execution via ComputeRes Worker
        if intent_type in ["EXECUTE_DYNAMIC", "DYNAMIC_CODE"]:
            code = args.get("code") or args.get("cmd") or ""
            c_args = args.get("args") or {}
            from compute_res.sdk.client import ComputeResClient
            try:
                client = ComputeResClient()
                res = await client.execute_dynamic_code(code, c_args)
                return res
            except Exception as e:
                return {"status": "error", "error": f"ComputeRes dynamic execution error: {e}"}

        # 2. Shared AI Model Embeddings / Inference
        if intent_type in ["AI_MODEL_COMPUTE", "EMBED"]:
            texts = args.get("input") or args.get("texts") or [""]
            if isinstance(texts, str):
                texts = [texts]
            model = get_embedding_model()
            if model:
                t0 = time.time()
                vectors = [v.tolist() if hasattr(v, "tolist") else list(v) for v in model.embed(texts)]
                return {
                    "status": "success",
                    "model": MODEL_NAME,
                    "dimension": len(vectors[0]) if vectors else 384,
                    "count": len(vectors),
                    "embeddings": vectors,
                    "compute_time_ms": round((time.time() - t0) * 1000, 2)
                }
            return {"status": "error", "error": "Model engine uninitialized"}

        # 3. ComputeRes System Status
        if intent_type == "STATUS":
            skills_dir = os.path.join(self.compute_res_path, "compute_res", "tools", "evolved_skills")
            skills = os.listdir(skills_dir) if os.path.exists(skills_dir) else []
            return {
                "status": "success",
                "engine": "ComputeRes Shared Operating System",
                "active_model": MODEL_NAME,
                "dimension": 384,
                "skills_count": len(skills),
                "ipc_broker_port": 5557,
                "model_gateway_port": 57161,
                "webrtc_mesh": "active"
            }

        # 4. Skills Hub Invocation (query, execute, publish)
        if intent_type == "SKILL_ROUTER_INVOKE":
            skills_dir = os.path.join(self.compute_res_path, "compute_res", "tools", "evolved_skills")
            if "query" in args:
                if os.path.exists(skills_dir):
                    skills = os.listdir(skills_dir)
                    return {"status": "success", "skills_found": skills, "message": "Queried local ComputeRes skills registry."}
                return {"status": "success", "skills_found": [], "message": "Skills registry empty."}

            if args.get("action") == "execute":
                skill_name = args.get("skill_name")
                if skill_name:
                    if not skill_name.endswith(".py"):
                        skill_name += ".py"
                    skill_path = os.path.join(skills_dir, skill_name)
                    if os.path.exists(skill_path):
                        # Dispatch directly through ComputeRes client for high performance
                        from compute_res.sdk.client import ComputeResClient
                        try:
                            client = ComputeResClient()
                            tool_id = skill_name[:-3]
                            res = await client._send_request({"tool": tool_id, "args": args.get("skill_args", {})})
                            return res
                        except Exception:
                            # Fallback to subprocess
                            proc = await asyncio.create_subprocess_shell(
                                f"{sys.executable} {skill_path}",
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout, stderr = await proc.communicate()
                            return {"status": "success", "stdout": stdout.decode(), "stderr": stderr.decode()}
                    return {"status": "error", "message": f"Skill {skill_name} not found."}

            if args.get("action") == "publish" or "data" in args:
                try:
                    import zmq
                    ctx = zmq.asyncio.Context.instance()
                    pub = ctx.socket(zmq.PUB)
                    pub.connect("tcp://127.0.0.1:5566")
                    await asyncio.sleep(0.05)
                    payload = json.dumps({"event": "SKILL_AVAILABLE", "data": args})
                    await pub.send_multipart([b"OS_EVENT", payload.encode()])
                    pub.close()
                    return {"status": "success", "message": "Skill successfully published to WebRTC swarm."}
                except Exception as e:
                    return {"status": "error", "message": f"Failed to publish skill: {e}"}

        return {"status": "pending", "message": "Dispatched intent to ComputeRes Execution Branch."}

    def shutdown(self):
        if self.t_broker: self.t_broker.cancel()
        if self.t_ipc_broker: self.t_ipc_broker.cancel()
        if self.t_worker: self.t_worker.cancel()
        if self.ipc_broker: self.ipc_broker.stop()
        if self.httpd: self.httpd.shutdown()
