import sys
import asyncio
import json

class ComputeResExecutionBranch:
    """
    Natively wraps ComputeRes as Branch 2 using strictly dynamic paths.
    """
    def __init__(self, compute_res_path: str, ctx=None):
        # Dynamically append the discovered path, ZERO hardcoded absolute paths!
        if compute_res_path not in sys.path:
            sys.path.append(compute_res_path)
            
        import zmq.asyncio
        self.ctx = ctx or zmq.asyncio.Context()
        
        # Now we can safely import because the dynamic path is in sys.path
        from compute_res.network.zmq_broker import HyperSwarmBroker
        from compute_res.oracle.master import OracleMaster
        
        self.broker = HyperSwarmBroker(self.ctx)
        self.oracle = OracleMaster(self.ctx)
        self.t_broker = None
        self.t_oracle = None

    async def boot_branch(self):
        print("[Branch 2: Execution] Booting ZeroMQ Router & Oracle Master...")
        self.t_broker = asyncio.create_task(self.broker.start_anarchy_queue())
        self.t_oracle = asyncio.create_task(self.oracle.run_governance_loop())

    async def dispatch_intent(self, agent_id: bytes, intent_payload: dict):
        import zmq
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
            return {"status": "pending", "message": "Dispatched to async Wasmtime queue."}

    def shutdown(self):
        if self.t_broker: self.t_broker.cancel()
        if self.t_oracle: self.t_oracle.cancel()
        self.broker.close()
        self.oracle.close()
