import os
import sys
import asyncio
import subprocess
import shutil

from mesh_broker import MCPMeshBroker
from holographic_ast import HolographicASTGraph
from void_governor import VoidGovernor
from fall_detector import SystemFallDetector
from intent_gc import IntentGarbageCollector

class OmniOSRootKernel:
    def __init__(self, workspace_root=None):
        self.workspace_root = workspace_root or os.getcwd()
        self.node_id = f"OmniOS-Kernel-{os.getpid()}"
        
        self.mesh = MCPMeshBroker(self.node_id)
        self.governor = VoidGovernor(critical_memory_threshold_percent=10.0)
        self.fall_detector = SystemFallDetector(self.node_id)
        self.intent_gc = IntentGarbageCollector(self.workspace_root)
        
        self.branches = {}
        self._ensure_os_dependencies()
        self._mount_branches()

    def _is_termux(self):
        return "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')

    def _run_cmd(self, cmd: str, description: str):
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[{self.node_id}] ✅ Auto-Installed {description}.")
        except subprocess.CalledProcessError:
            pass

    def _ensure_os_dependencies(self):
        if not shutil.which("nodeos"):
            pip_cmd = "pip install polymath-nodeos" + (" --break-system-packages" if self._is_termux() else "")
            self._run_cmd(pip_cmd, "polymath-nodeos (Cognition Branch)")
            
        if not shutil.which("jage") and not os.path.exists(os.path.join(self.workspace_root, "polymath-jage")):
            self._run_cmd("npm install -g polymath-jage", "polymath-jage (Time Branch)")
            
        compute_res_path = os.path.join(self.workspace_root, "ComputeRes")
        if not os.path.exists(compute_res_path):
            self._run_cmd(f"git clone https://github.com/polymath-void/ComputeRes.git {compute_res_path}", "Execution Branch")

    def _mount_branches(self):
        db_path = os.path.join(self.workspace_root, "agy_nodeos.db")
        if os.path.exists(db_path) or shutil.which("nodeos"):
            self.branches["Cognition"] = self.fall_detector.safe_mount(
                "Cognition", lambda: HolographicASTGraph(db_path)
            )

        compute_res_path = os.path.join(self.workspace_root, "ComputeRes")
        if os.path.isdir(compute_res_path):
            from branch_adapters.execution_branch import ComputeResExecutionBranch
            self.branches["Execution"] = self.fall_detector.safe_mount(
                "Execution", lambda: ComputeResExecutionBranch(compute_res_path)
            )
            
        jage_path = os.path.join(self.workspace_root, "polymath-jage")
        if os.path.isdir(jage_path):
            from branch_adapters.time_branch import JageTimeBranch
            self.branches["Time"] = self.fall_detector.safe_mount(
                "Time", lambda: JageTimeBranch(jage_path)
            )

    def register_mesh_tools(self):
        self.mesh.register_tool(name="ping_edge_node", schema={"returns": "pong"})
        
        # Expose the GC trigger to the swarm
        self.mesh.register_tool(name="trigger_intent_gc", schema={"description": "Cleans up completed intents instantly."})
        
        if "Cognition" in self.branches and self.branches["Cognition"]:
            self.mesh.register_tool(name="query_holographic_ast", schema={"parameters": {"intent": "string"}})
        if "Execution" in self.branches and self.branches["Execution"]:
            self.mesh.register_tool(name="compute_res_execute_bash", schema={"parameters": {"cmd": "string"}})
        if "Time" in self.branches and self.branches["Time"]:
            self.mesh.register_tool(name="jage_sync_ast", schema={"parameters": {}})
            
        # Hook native GC execution
        original_handler = self.mesh.handle_incoming_request
        async def hooked_handler(tool_name: str, args: dict):
            if tool_name == "trigger_intent_gc":
                return self.intent_gc.sweep_completed_intents()
            if tool_name == "compute_res_execute_bash" and "Execution" in self.branches:
                return await self.branches["Execution"].dispatch_intent(b"Mesh-Client", {"type": "EXEC_BASH", "args": args})
            return await original_handler(tool_name, args)
        self.mesh.handle_incoming_request = hooked_handler

    async def boot(self):
        self.register_mesh_tools()
        
        # Run GC EXACTLY ONCE at boot
        self.intent_gc.sweep_completed_intents()
        
        if "Cognition" in self.branches and self.branches["Cognition"]:
            asyncio.create_task(self.branches["Cognition"].generate_embeddings_background_task())
        if "Execution" in self.branches and self.branches["Execution"]:
            await self.branches["Execution"].boot_branch()
        if "Time" in self.branches and self.branches["Time"]:
            await self.branches["Time"].boot_branch()
            
        await self.mesh.start_mdns_broadcast()
        return self.governor
