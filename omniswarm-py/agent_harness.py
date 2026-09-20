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
    
    def __init__(self, agent_id: str, workspace_root: Optional[str] = None):
        self.agent_id = agent_id
        self.workspace_root = workspace_root or os.getcwd()
        self.workflow_file = os.path.join(self.workspace_root, "workflow.json")
        
        # Optimized ZMQ Context Pooling
        self.ctx = zmq.asyncio.Context.instance()
        self.req_socket = None
        self.sub_socket = None
        self._connected = False

    async def __aenter__(self):
        """Context manager support for clean socket initialization and teardown."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    async def connect(self, rpc_port: int = 5565, pub_port: int = 5567):
        """Establishes optimized, non-blocking connections to the OmniOS Kernel."""
        if not self._connected:
            self.req_socket = self.ctx.socket(zmq.REQ)
            self.req_socket.connect(f"tcp://127.0.0.1:{rpc_port}")
            
            self.sub_socket = self.ctx.socket(zmq.SUB)
            self.sub_socket.connect(f"tcp://127.0.0.1:{pub_port}")
            
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
                        "required": ["cmd"]
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
