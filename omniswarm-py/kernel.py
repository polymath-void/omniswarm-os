import os
import json
import sys
import asyncio
import subprocess
import shutil

from mesh_broker import MCPMeshBroker
from holographic_ast import HolographicASTGraph
from void_governor import VoidGovernor
from fall_detector import SystemFallDetector
from intent_gc import IntentGarbageCollector
from event_ledger import EventLedger

class OmniOSRootKernel:
    def __init__(self, workspace_root=None):
        self.workspace_root = workspace_root or os.getcwd()
        self.parent_root = os.path.dirname(self.workspace_root)
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

    def _symlink_from_umbrella(self, target_name: str):
        """Intelligently links from the parent umbrella workspace instead of re-downloading."""
        local_path = os.path.join(self.workspace_root, target_name)
        umbrella_path = os.path.join(self.parent_root, target_name)
        
        if not os.path.exists(local_path) and os.path.exists(umbrella_path):
            os.symlink(umbrella_path, local_path)
            print(f"[{self.node_id}] 🔗 Dynamically symlinked umbrella project: {target_name}")
            return True
        return os.path.exists(local_path)

    def _ensure_os_dependencies(self):
        # 1. Check/Symlink NodeOS database
        self._symlink_from_umbrella("agy_nodeos.db")
        if not shutil.which("nodeos"):
            pip_cmd = "pip install polymath-nodeos" + (" --break-system-packages" if self._is_termux() else "")
            self._run_cmd(pip_cmd, "polymath-nodeos (Cognition Branch)")
            
        # 2. Check/Symlink Jage
        has_jage = self._symlink_from_umbrella("polymath-jage")
        if not shutil.which("jage") and not has_jage:
            self._run_cmd("npm install -g polymath-jage", "polymath-jage (Time Branch)")
            
        # 3. Check/Symlink ComputeRes
        has_compute = self._symlink_from_umbrella("ComputeRes")
        if not has_compute:
            compute_res_path = os.path.join(self.workspace_root, "ComputeRes")
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
        db_path = os.path.join(self.workspace_root, "agy_nodeos.db")
        self.event_ledger = EventLedger(db_path)
        
        self.mesh.register_tool(name="ping_edge_node", schema={"returns": "pong"})
        self.mesh.register_tool(name="trigger_intent_gc", schema={"description": "Cleans up completed intents instantly."})
        self.mesh.register_tool(name="query_os_events", schema={"parameters": {"since_timestamp": "float"}})
        
        if "Cognition" in self.branches and self.branches["Cognition"]:
            self.mesh.register_tool(name="query_holographic_ast", schema={"parameters": {"intent": "string"}})
        if "Execution" in self.branches and self.branches["Execution"]:
            self.mesh.register_tool(name="compute_res_execute_bash", schema={"parameters": {"cmd": "string"}})
        if "Time" in self.branches and self.branches["Time"]:
            self.mesh.register_tool(name="jage_sync_ast", schema={"parameters": {}})
            
        original_handler = self.mesh.handle_incoming_request
        async def hooked_handler(tool_name: str, args: dict):
            if tool_name == "query_os_events":
                return {"status": "success", "events": self.event_ledger.query_events_since(args.get("since_timestamp", 0.0))}
            if tool_name == "trigger_intent_gc":
                return self.intent_gc.sweep_completed_intents()
            if tool_name == "compute_res_execute_bash" and "Execution" in self.branches:
                return await self.branches["Execution"].dispatch_intent(b"Mesh-Client", {"type": "EXEC_BASH", "args": args})
            if tool_name == "query_holographic_ast" and "Cognition" in self.branches:
                # Wrap sync call in asyncio to thread or execute directly
                return {"status": "success", "results": self.branches["Cognition"].semantic_search(args.get("intent", ""), args.get("top_k", 3))}
            if tool_name == "jage_sync_ast" and "Time" in self.branches:
                return await self.branches["Time"].version_ast_state(args.get("file_path", ""))
            return await original_handler(tool_name, args)
        self.mesh.handle_incoming_request = hooked_handler

    async def boot(self):
        self.register_mesh_tools()
        self.intent_gc.sweep_completed_intents()
        
        if "Cognition" in self.branches and self.branches["Cognition"]:
            async def notify_mesh(count):
                payload_dict = {"event": "AST_SYNC_COMPLETE", "nodes_mapped": count}
                self.event_ledger.log_event("AST_SYNC_COMPLETE", payload_dict)
                
                payload = json.dumps(payload_dict).encode()
                await self.mesh.discovery_pub.send_multipart([b"OS_EVENT", payload])
            asyncio.create_task(self.branches["Cognition"].generate_embeddings_background_task(on_batch_complete=notify_mesh))
        if "Execution" in self.branches and self.branches["Execution"]:
            await self.branches["Execution"].boot_branch()
        if "Time" in self.branches and self.branches["Time"]:
            await self.branches["Time"].boot_branch()
            
        await self.mesh.start_mdns_broadcast()
        return self.governor
