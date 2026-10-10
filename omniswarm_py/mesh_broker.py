import json
import asyncio
import os
from typing import Dict
import threading
import queue
import zmq

class MCPMeshBroker:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.local_tools: Dict[str, dict] = {}
        self.mesh_peers: Dict[str, dict] = {}
        
        # Deferred — set when start_mdns_broadcast() is called inside a running loop
        self.main_loop = None
        
        # Queues for receiving messages (created lazily when loop is available)
        self.rpc_queue = None
        self.discovery_queue = None
        
        # Thread-safe queue for sending messages to ZMQ thread
        self.send_queue = queue.Queue()
        
        self.rpc_port = 5565
        self.pub_port = 5566
        self._zmq_started = False

    def register_tool(self, name: str, schema: dict):
        self.local_tools[name] = schema

    def _zmq_polling_loop(self):
        context = zmq.Context()
        
        rpc_server = context.socket(zmq.ROUTER)
        rpc_server.bind(f"tcp://*:{self.rpc_port}")
        
        discovery_pub = context.socket(zmq.PUB)
        discovery_pub.bind(f"tcp://*:{self.pub_port}")
        
        discovery_sub = context.socket(zmq.SUB)
        discovery_sub.connect(f"tcp://127.0.0.1:{self.pub_port}")
        discovery_sub.setsockopt_string(zmq.SUBSCRIBE, "OMNI_DISCOVERY")
        discovery_sub.setsockopt_string(zmq.SUBSCRIBE, "OS_EVENT")
        
        poller = zmq.Poller()
        poller.register(rpc_server, zmq.POLLIN)
        poller.register(discovery_sub, zmq.POLLIN)
        
        while True:
            # Process outbound messages first
            while not self.send_queue.empty():
                try:
                    msg_type, data = self.send_queue.get_nowait()
                    if msg_type == 'rpc_reply':
                        rpc_server.send_multipart(data)
                    elif msg_type == 'pub_bcast':
                        discovery_pub.send_multipart(data)
                except Exception:
                    pass
            
            # Poll with timeout to allow checking send_queue
            socks = dict(poller.poll(100)) # 100ms timeout
            
            if rpc_server in socks and socks[rpc_server] == zmq.POLLIN:
                msg_parts = rpc_server.recv_multipart()
                self.main_loop.call_soon_threadsafe(self.rpc_queue.put_nowait, msg_parts)
                
            if discovery_sub in socks and socks[discovery_sub] == zmq.POLLIN:
                msg_parts = discovery_sub.recv_multipart()
                self.main_loop.call_soon_threadsafe(self.discovery_queue.put_nowait, msg_parts)

    async def _listen_for_rpc(self):
        """Listens for RPC messages pushed from the ZMQ polling thread."""
        while True:
            try:
                msg_parts = await self.rpc_queue.get()
                if len(msg_parts) >= 3:
                    identity = msg_parts[0]
                    empty = msg_parts[1]
                    payload_str = msg_parts[2].decode()
                    
                    # Spawn a background task for each request to prevent deadlocks
                    asyncio.create_task(self._process_and_reply(identity, empty, payload_str))
            except Exception as e:
                pass

    async def _process_and_reply(self, identity: bytes, empty: bytes, payload_str: str):
        """Processes the request natively and returns the payload via ROUTER."""
        try:
            payload = json.loads(payload_str)
            tool_name = payload.get("tool")
            args = payload.get("args", {})
            
            response = await self.handle_incoming_request(tool_name, args)
            
            # Send back to the exact client identity via the synchronous thread
            self.send_queue.put(('rpc_reply', [identity, empty, json.dumps(response).encode()]))
        except Exception as e:
            self.send_queue.put(('rpc_reply', [identity, empty, json.dumps({"status": "error", "message": str(e)}).encode()]))

    async def _listen_for_discovery(self):
        while True:
            try:
                msg_parts = await self.discovery_queue.get()
                if len(msg_parts) >= 2:
                    topic = msg_parts[0]
                    msg = msg_parts[1]
                    if topic == b"OMNI_DISCOVERY":
                        peer_info = json.loads(msg.decode())
                        if peer_info["node_id"] != self.node_id:
                            self.mesh_peers[peer_info["node_id"]] = peer_info
            except Exception:
                pass

    async def start_mdns_broadcast(self):
        # Deferred initialization — only now are we inside a running event loop
        if not self._zmq_started:
            self.main_loop = asyncio.get_running_loop()
            self.rpc_queue = asyncio.Queue()
            self.discovery_queue = asyncio.Queue()
            
            self.zmq_thread = threading.Thread(target=self._zmq_polling_loop, daemon=True)
            self.zmq_thread.start()
            self._zmq_started = True
            print(f"[{self.node_id}] ZMQ Thread-Isolated Engine Online. RPC Port: {self.rpc_port}")
        
        asyncio.create_task(self._listen_for_rpc())
        asyncio.create_task(self._listen_for_discovery())
        
        async def broadcast_loop():
            while True:
                payload = json.dumps({
                    "node_id": self.node_id, 
                    "rpc_port": self.rpc_port, 
                    "tools": list(self.local_tools.keys())
                })
                self.send_queue.put(('pub_bcast', [b"OMNI_DISCOVERY", payload.encode()]))
                await asyncio.sleep(5)
                
        asyncio.create_task(broadcast_loop())

    async def handle_incoming_request(self, tool_name: str, args: dict) -> dict:
        print(f"[{self.node_id}] Real Mesh Executing -> Tool: {tool_name} | Args: {args}")
        if tool_name not in self.local_tools:
            return {"status": "error", "message": f"Tool {tool_name} missing."}
        try:
            if tool_name == "compute_res_execute_bash":
                # Ensure execution is non-blocking to protect the asyncio loop!
                cmd = args.get("cmd", "")
                exec_cwd = args.get("cwd", os.getcwd())
                process = await asyncio.create_subprocess_shell(
                    cmd, cwd=exec_cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                return {"status": "success", "stdout": stdout.decode(), "stderr": stderr.decode()}
            elif tool_name == "ping_edge_node":
                return {"status": "success", "message": "pong"}
            elif tool_name in ["synty_chat_post", "synty_chat_read", "synty_chat_rooms"]:
                try:
                    from synty_bridge import SyntySwarmBridge
                except ImportError:
                    from omniswarm_py.synty_bridge import SyntySwarmBridge
                bridge = SyntySwarmBridge(broker=self)
                return await bridge.handle_chat_rpc(tool_name, args)
            return {"status": "success", "result": f"Executed natively: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
