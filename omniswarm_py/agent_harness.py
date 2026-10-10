import sys
import asyncio

# [Windows Compatibility Patch] Force UTF-8 for Emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


import os
import json
import asyncio
import time
import zmq
import zmq.asyncio
from typing import Dict, List, Any, Optional

class OmniOSAgentHarness:
    """
    Advanced Universal SDK for AI Agents traversing the OmniOS ecosystem.
    
    Provides highly optimized, non-blocking ZMQ communication, 
    LLM-native capability discovery (JSON Schemas), and asynchronous event subscriptions.
    """
    
    def __init__(self, agent_id: str, workspace_root: Optional[str] = None, host: Optional[str] = None, rpc_port: Optional[int] = None, pub_port: Optional[int] = None):
        self.agent_id = agent_id
        self.workspace_root = workspace_root or os.getcwd()
        self.workflow_file = os.path.join(self.workspace_root, "workflow.json")
        
        # Dynamic Mesh Configuration fallback from mesh_config.json or environment
        from omniswarm_py.mesh_config import load_mesh_config
        cfg = load_mesh_config(self.workspace_root)
        
        self.host = host if host is not None else cfg.get("hub_host", "127.0.0.1")
        self.rpc_port = rpc_port if rpc_port is not None else cfg.get("rpc_port", 5565)
        self.pub_port = pub_port if pub_port is not None else cfg.get("pub_port", 5566)
        
        # Optimized ZMQ Context Pooling
        self.ctx = zmq.asyncio.Context.instance()
        self.req_socket = None
        self.sub_socket = None
        self._connected = False

    async def __aenter__(self):
        """Context manager support for clean socket initialization and teardown."""
        await self.connect(host=self.host, rpc_port=self.rpc_port, pub_port=self.pub_port)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    async def connect(self, host: Optional[str] = None, rpc_port: int = 5565, pub_port: int = 5566):
        """Establishes optimized, non-blocking connections to the OmniOS Kernel."""
        target_host = host or self.host
        if not self._connected:
            self.req_socket = self.ctx.socket(zmq.REQ)
            
            # [Tailscale Userspace Networking Patch] 
            # If on Android and connecting to a Tailscale IP (100.x.x.x), use the local SOCKS5 proxy
            is_android = hasattr(sys, 'getandroidapilevel') or "com.termux" in os.environ.get("PREFIX", "")
            if is_android and target_host.startswith("100."):
                print(f"[Harness:{self.agent_id}] Android detected. Tunneling ZMQ via Tailscale SOCKS5 (127.0.0.1:1055)...")
                self.req_socket.setsockopt_string(zmq.SOCKS_PROXY, "127.0.0.1:1055")
                
            self.req_socket.connect(f"tcp://{target_host}:{rpc_port}")
            
            self.sub_socket = self.ctx.socket(zmq.SUB)
            if is_android and target_host.startswith("100."):
                self.sub_socket.setsockopt_string(zmq.SOCKS_PROXY, "127.0.0.1:1055")
            self.sub_socket.connect(f"tcp://{target_host}:{pub_port}")
            
            self._connected = True
            print(f"[Harness:{self.agent_id}] Linked to OmniOS Matrix.")

    def disconnect(self):
        """Safely tears down the harness sockets to prevent ZMQ memory leaks."""
        if self._connected:
            if self.req_socket: self.req_socket.close()
            if self.sub_socket: self.sub_socket.close()
            self._connected = False

    def get_llm_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Agent Understanding: Returns available capabilities formatted strictly 
        as OpenAI/Anthropic compatible JSON Function Schemas.
        An agent can dynamically inject this array directly into its LLM context!
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_holographic_ast",
                    "description": "Performs a mathematical semantic vector search across the entire AST codebase.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "intent": {"type": "string", "description": "The semantic concept to search for (e.g., 'database connection logic')"},
                            "top_k": {"type": "integer", "description": "Number of AST nodes to return", "default": 3}
                        },
                        "required": ["intent"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compute_res_execute_bash",
                    "description": "Executes a bash command statefully within the ComputeRes Wasmtime environment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cmd": {"type": "string", "description": "The bash command to execute"}
                        },
                        "required": ["cmd"],
                        "cwd": {"type": "string", "description": "Optional working directory"}
                    }
                }
            }
        ]

    async def execute_in_swarm(self, tool_name: str, args: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """
        Highly optimized RPC dispatcher with timeout protection and non-blocking I/O.
        """
        if not self._connected:
            await self.connect()
            
        if tool_name == "compute_res_execute_bash" and "cwd" not in args:
            args["cwd"] = os.getcwd()
        payload = json.dumps({"agent_id": self.agent_id, "tool": tool_name, "args": args})
        await self.req_socket.send_string(payload)
        
        try:
            response = await asyncio.wait_for(self.req_socket.recv_string(), timeout=timeout)
            return json.loads(response)
        except asyncio.TimeoutError:
            # Recreate socket to prevent ZMQ REQ/REP state machine lockup on timeout
            self.req_socket.close()
            self._connected = False
            return {"status": "error", "message": "OmniOS Kernel Timeout. Mesh congested."}

    async def subscribe_to_events(self, topic: str = ""):
        """
        Allows an agent to listen to the global OS pub/sub bus asynchronously.
        Useful for listening to 'sys.memory.critical' warnings.
        """
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, topic)
        print(f"[Harness:{self.agent_id}] Subscribed to OS Events: '{topic}'")
        while True:
            try:
                recv_topic, msg = await self.sub_socket.recv_multipart()
                yield recv_topic.decode(), json.loads(msg.decode())
            except asyncio.CancelledError:
                break

    async def suspend_intent_safely(self, current_state: Dict[str, Any]):
        """
        Optimized file I/O for intent serialization using asyncio.to_thread 
        to prevent blocking the agent's main event loop during disk writes.
        """
        def _write_state():
            dump = {
                "agent_id": self.agent_id,
                "status": "suspended_by_agent",
                "saved_state": current_state,
                "timestamp": time.time()
            }
            if os.path.exists(self.workflow_file):
                try:
                    with open(self.workflow_file, 'r') as f:
                        workflow = json.load(f)
                except json.JSONDecodeError:
                    workflow = {"intents": []}
            else:
                workflow = {"intents": []}
                
            workflow["intents"].append(dump)
            
            # Atomic-style write to prevent corruption
            tmp_file = self.workflow_file + ".tmp"
            with open(tmp_file, 'w') as f:
                json.dump(workflow, f, indent=2)
            os.replace(tmp_file, self.workflow_file)
            
        await asyncio.to_thread(_write_state)
        print(f"[Harness:{self.agent_id}] Intent cleanly serialized to workflow.json")
        # Also sync across the network to the Hub's central workflow ledger!
        try:
            dump_dict = {
                "agent_id": self.agent_id,
                "status": "suspended_by_agent",
                "saved_state": current_state,
                "timestamp": time.time()
            }
            await self.execute_in_swarm("swarm_sync_intent", {"intent": dump_dict}, timeout=3.0)
        except Exception:
            pass

    # =========================================================================
    # SyntyChat Zero-HIL Communication Methods (Room & Topic Based)
    # =========================================================================

    async def chat_post(self, room: str, content: Any, msg_type: str = "chat", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Post a message or log to a SyntyChat room."""
        return await self.execute_in_swarm("synty_chat_post", {
            "room": room,
            "sender": self.agent_id,
            "content": content,
            "type": msg_type,
            "metadata": metadata or {}
        })

    async def chat_read(self, room: str, since_timestamp: float = 0.0, limit: int = 50) -> List[Dict[str, Any]]:
        """Read recent messages from a SyntyChat room."""
        res = await self.execute_in_swarm("synty_chat_read", {
            "room": room,
            "since_timestamp": since_timestamp,
            "limit": limit
        })
        return res.get("messages", [])

    # =========================================================================
    # SwarmComms Direct P2P Messaging Methods (Agent-to-Agent)
    # =========================================================================

    async def send_agent_message(self, recipient: str, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sends a direct message to another agent in the swarm across devices."""
        return await self.execute_in_swarm("swarm_send_message", {
            "sender": self.agent_id,
            "recipient": recipient,
            "message": message,
            "data": data or {}
        })

    async def read_my_messages(self, since_id: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Reads all incoming messages addressed to this agent."""
        res = await self.execute_in_swarm("swarm_read_messages", {
            "agent_id": self.agent_id,
            "since_id": since_id,
            "limit": limit
        })
        return res.get("messages", [])

    async def chat_stream_log(self, room: str, log_line: str, level: str = "INFO") -> Dict[str, Any]:
        """Stream an operations log line to the room in real time."""
        return await self.chat_post(
            room=room,
            content=log_line,
            msg_type="OPERATION_LOG",
            metadata={"level": level, "platform": sys.platform}
        )

    async def chat_send_directive(self, room: str, target_agent: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch an autonomous task directive to another agent without HIL."""
        return await self.chat_post(
            room=room,
            content={"action": action, "target": target_agent, "payload": payload},
            msg_type="TASK_DIRECTIVE",
            metadata={"target_agent": target_agent, "action": action}
        )

    # =========================================================================
    # SwarmComms Direct P2P Log Streaming Methods (Agent-to-Agent)
    # =========================================================================

    async def post_agent_log(self, message: str, level: str = "INFO") -> Dict[str, Any]:
        """Streams an operational log to the swarm so other agents can see live progress."""
        return await self.execute_in_swarm("swarm_post_log", {
            "agent_id": self.agent_id,
            "log_level": level,
            "message": message
        })

    async def stream_agent_logs(self, agent_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Reads live operational logs from another agent or all swarm agents."""
        res = await self.execute_in_swarm("swarm_stream_logs", {
            "agent_id": agent_id,
            "limit": limit
        })
        return res.get("logs", [])

    async def get_latest_ids(self) -> Dict[str, int]:
        """Gets the latest message ID and log ID from the swarm."""
        res = await self.execute_in_swarm("swarm_get_latest_ids", {})
        return {
            "latest_message_id": res.get("latest_message_id", 0),
            "latest_log_id": res.get("latest_log_id", 0)
        }

