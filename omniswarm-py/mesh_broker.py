import json
import asyncio
import time
import subprocess
import socket
from typing import Dict, Any, List
import zmq
import zmq.asyncio

class MCPMeshBroker:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.local_tools: Dict[str, dict] = {}
        self.mesh_peers: Dict[str, dict] = {}
        
        self.ctx = zmq.asyncio.Context()
        # Real ZMQ REP socket for incoming tool execution requests
        self.rpc_server = self.ctx.socket(zmq.REP)
        self.rpc_port = 5565
        self.rpc_server.bind(f"tcp://*:{self.rpc_port}")
        
        # Real ZMQ PUB socket for broadcasting existence
        self.discovery_pub = self.ctx.socket(zmq.PUB)
        self.discovery_pub.bind("tcp://*:5566")
        
        # Real ZMQ SUB socket for listening to other nodes
        self.discovery_sub = self.ctx.socket(zmq.SUB)
        self.discovery_sub.connect("tcp://127.0.0.1:5566") # In reality, connect to subnet broadcast
        self.discovery_sub.setsockopt_string(zmq.SUBSCRIBE, "OMNI_DISCOVERY")
        
        print(f"[{self.node_id}] ZMQ P2P Mesh Engine Online. RPC Port: {self.rpc_port}")

    def register_tool(self, name: str, schema: dict):
        self.local_tools[name] = schema

    async def _listen_for_rpc(self):
        """Real ZMQ background listener for incoming tool execution."""
        while True:
            try:
                request = await self.rpc_server.recv_string()
                payload = json.loads(request)
                
                tool_name = payload.get("tool")
                args = payload.get("args", {})
                
                response = await self.handle_incoming_request(tool_name, args)
                await self.rpc_server.send_string(json.dumps(response))
            except Exception as e:
                pass
                
    async def _listen_for_discovery(self):
        """Real ZMQ listener mapping other nodes on the network."""
        while True:
            try:
                topic, msg = await self.discovery_sub.recv_multipart()
                peer_info = json.loads(msg.decode())
                
                if peer_info["node_id"] != self.node_id:
                    self.mesh_peers[peer_info["node_id"]] = peer_info
            except Exception:
                pass

    async def start_mdns_broadcast(self):
        """Replaced simulated mDNS with real ZMQ background threads."""
        asyncio.create_task(self._listen_for_rpc())
        asyncio.create_task(self._listen_for_discovery())
        
        # Broadcast our existence periodically
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
                result = subprocess.run(args.get("cmd", ""), shell=True, capture_output=True, text=True)
                return {"status": "success", "stdout": result.stdout, "stderr": result.stderr}
            elif tool_name == "ping_edge_node":
                return {"status": "success", "message": "pong"}
            return {"status": "success", "result": f"Executed natively: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def execute_remote_tool(self, target_node_id: str, target_port: int, tool_name: str, args: dict):
        """Real ZMQ REQ socket sending a payload over TCP."""
        req_socket = self.ctx.socket(zmq.REQ)
        req_socket.connect(f"tcp://127.0.0.1:{target_port}") # In production, use target IP
        
        payload = json.dumps({"tool": tool_name, "args": args})
        await req_socket.send_string(payload)
        
        resp = await req_socket.recv_string()
        req_socket.close()
        return json.loads(resp)
