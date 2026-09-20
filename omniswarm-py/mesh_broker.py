import json
import asyncio
import time
import socket
from typing import Dict, Any, List
import zmq
import zmq.asyncio

class MCPMeshBroker:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.local_tools: Dict[str, dict] = {}
        self.mesh_peers: Dict[str, dict] = {}
        
        self.ctx = zmq.asyncio.Context.instance()
        
        # UPGRADE: REQ/REP replaced with ROUTER for true async multiplexing
        self.rpc_server = self.ctx.socket(zmq.ROUTER)
        self.rpc_port = 5565
        self.rpc_server.bind(f"tcp://*:{self.rpc_port}")
        
        self.discovery_pub = self.ctx.socket(zmq.PUB)
        self.discovery_pub.bind("tcp://*:5566")
        
        self.discovery_sub = self.ctx.socket(zmq.SUB)
        self.discovery_sub.connect("tcp://127.0.0.1:5566")
        self.discovery_sub.setsockopt_string(zmq.SUBSCRIBE, "OMNI_DISCOVERY")
        self.discovery_sub.setsockopt_string(zmq.SUBSCRIBE, "OS_EVENT")
        
        print(f"[{self.node_id}] ZMQ Asynchronous ROUTER Engine Online. RPC Port: {self.rpc_port}")

    def register_tool(self, name: str, schema: dict):
        self.local_tools[name] = schema

    async def _listen_for_rpc(self):
        """Asynchronous ROUTER listener. Multiplexes incoming tasks without blocking."""
        while True:
            try:
                # ROUTER receives [identity, empty (for REQ clients), payload]
                msg_parts = await self.rpc_server.recv_multipart()
                
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
            
            # Send back to the exact client identity
            await self.rpc_server.send_multipart([identity, empty, json.dumps(response).encode()])
        except Exception as e:
            await self.rpc_server.send_multipart([identity, empty, json.dumps({"status": "error", "message": str(e)}).encode()])

    async def _listen_for_discovery(self):
        while True:
            try:
                topic, msg = await self.discovery_sub.recv_multipart()
                if topic == b"OMNI_DISCOVERY":
                    peer_info = json.loads(msg.decode())
                    if peer_info["node_id"] != self.node_id:
                        self.mesh_peers[peer_info["node_id"]] = peer_info
            except Exception:
                pass

    async def start_mdns_broadcast(self):
        asyncio.create_task(self._listen_for_rpc())
        asyncio.create_task(self._listen_for_discovery())
        
        async def broadcast_loop():
            while True:
                payload = json.dumps({
                    "node_id": self.node_id, 
                    "rpc_port": self.rpc_port, 
                    "tools": list(self.local_tools.keys())
                })
                await self.discovery_pub.send_multipart([b"OMNI_DISCOVERY", payload.encode()])
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
            return {"status": "success", "result": f"Executed natively: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
