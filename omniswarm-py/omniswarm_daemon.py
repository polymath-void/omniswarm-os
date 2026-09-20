import sys
import asyncio
from kernel import OmniOSRootKernel

# Cross-platform compatibility for Windows (PyZMQ and Unicode)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
if sys.stdout and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class OmniOSDaemon:
    def __init__(self):
        print("===========================================")
        print("   OMNIOS: ROOT KERNEL INITIALIZING...     ")
        print("===========================================\n")
        
        self.kernel = OmniOSRootKernel()
        self.running = True

    async def _handle_suspend(self):
        print(f"\n[{self.kernel.node_id}] ⚠️ Void-Governor triggered hibernation sequence...")
        self.kernel.governor.serialize_intent("omniswarm_daemon_loop", {"status": "hibernating"})
        self.running = False

    async def run(self):
        governor = await self.kernel.boot()
        governor_task = asyncio.create_task(governor.monitor_lmk_pressure(self._handle_suspend))
        
        role = f"OmniOS Root (Managing {len(self.kernel.branches)} branches)"
        print(f"\n[{self.kernel.node_id} | {role}] System Online. Mesh listening...\n")
        
        # True Infinite Daemon Loop (No Simulation Cutoff)
        while self.running:
            try:
                await asyncio.sleep(10)
                # print(f"[{self.kernel.node_id}] Heartbeat | Mesh Peers Active")
            except asyncio.CancelledError:
                break
                
        if not governor_task.done():
            governor_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(OmniOSDaemon().run())
    except KeyboardInterrupt:
        print("\n[OmniOS] Kernel manually terminated.")
