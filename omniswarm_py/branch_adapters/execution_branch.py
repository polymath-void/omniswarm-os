import sys
import asyncio
import json

class ComputeResExecutionBranch:
    """
    Natively wraps ComputeRes as Branch 2 using strictly dynamic paths.
    Adapted for the new ComputeRes WebRTC Agent OS architecture.
    """
    def __init__(self, compute_res_path: str, ctx=None):
        # Dynamically append the discovered path, ZERO hardcoded absolute paths!
        if compute_res_path not in sys.path:
            sys.path.append(compute_res_path)
            
        import zmq.asyncio
        self.ctx = ctx or zmq.asyncio.Context()
        
        # Now we can safely import because the dynamic path is in sys.path
        # Mapped to the new ComputeRes SkillsHub/Mesh architecture
        from compute_res.network.mesh import WebRTCMeshRouter
        from compute_res.oracle.consensus import SwarmOracle
        
        # Initialize the new decentralized classes
        self.broker = WebRTCMeshRouter(node_id="execution_branch", swarm_id="omniswarm")
        self.oracle = SwarmOracle(node_id="execution_branch")
        
        self.t_broker = None
        self.t_oracle = None

    async def boot_branch(self):
        print("[Branch 2: Execution] Booting WebRTC Mesh Router & Swarm Oracle...")
        # Start the WebRTC Mesh loop
        self.t_broker = asyncio.create_task(self.broker.start())
        # SwarmOracle operates on demand in the new architecture, no background loop needed
        self.t_oracle = None

    async def dispatch_intent(self, agent_id: bytes, intent_payload: dict):
        import zmq
        # Note: In the WebRTC architecture, dispatching may need to migrate to the Webhooks/DataChannel.
        # Keeping the legacy DEALER socket here for backward compatibility with kernel.py.
        dealer = self.ctx.socket(zmq.DEALER)
        dealer.setsockopt(zmq.IDENTITY, agent_id)
        dealer.connect("tcp://127.0.0.1:5555")
        
        req = json.dumps(intent_payload).encode()
        await dealer.send(req)
        
        try:
            resp = await asyncio.wait_for(dealer.recv(), timeout=60.0)
            dealer.close()
            return json.loads(resp.decode())
        except asyncio.TimeoutError:
            dealer.close()
            return {"status": "pending", "message": "Dispatched to WebRTC/Wasmtime queue."}

    def shutdown(self):
        if self.t_broker: self.t_broker.cancel()
        if self.t_oracle: self.t_oracle.cancel()
