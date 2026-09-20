import os
import sys
import asyncio
import subprocess
import shutil
from mesh_broker import MCPMeshBroker
from holographic_ast import HolographicASTGraph
from void_governor import VoidGovernor

class OmniHubRegistry:
    def __init__(self, workspace_root=None):
        self.workspace_root = workspace_root or os.getcwd()
        self.node_id = f"OmniSwarm-Node-{os.getpid()}"
        
        print(f"[{self.node_id}] Scanning workspace dynamically: {self.workspace_root}")
        
        self.mesh = MCPMeshBroker(self.node_id)
        self.governor = VoidGovernor(critical_memory_threshold_percent=10.0)
        self.adapters = {}
        
        self._ensure_os_dependencies()
        self._discover_workspace_capabilities()

    def _is_termux(self):
        """Detects if we are running inside Android Termux vs a standard PC."""
        return "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')

    def _run_cmd(self, cmd: str, description: str):
        print(f"[{self.node_id}] Auto-Installer | {description}...")
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[{self.node_id}] ✅ Successfully installed {description}.")
        except subprocess.CalledProcessError:
            print(f"[{self.node_id}] ❌ Failed to install {description}. Ensure package exists or network is online.")

    def _ensure_os_dependencies(self):
        print(f"[{self.node_id}] Verifying OmniSwarm-OS dependency matrix...")
        
        # 1. Polymath-NodeOS (PyPI) - OS Aware Installation!
        if not shutil.which("nodeos"):
            # On Termux, we must break system packages. On PC, we use standard pip (or pipx).
            pip_cmd = "pip install polymath-nodeos"
            if self._is_termux():
                pip_cmd += " --break-system-packages"
            else:
                print(f"[{self.node_id}] Note: PC Environment detected. Using standard standard pip installation.")
                # Future enhancement: fallback to 'pipx install' if global pip fails on PC
                
            self._run_cmd(pip_cmd, "polymath-nodeos (PyPI)")
            
        # 2. Polymath-Jage (NPM or local)
        jage_path = os.path.join(self.workspace_root, "polymath-jage")
        parent_jage = os.path.join(os.path.dirname(self.workspace_root), "polymath-jage")
        
        if not os.path.exists(jage_path):
            if os.path.exists(parent_jage):
                print(f"[{self.node_id}] Found polymath-jage in parent directory. Symlinking...")
                os.symlink(parent_jage, jage_path)
            elif not shutil.which("jage"):
                self._run_cmd("npm install -g polymath-jage", "polymath-jage (NPM)")
            
        # 3. ComputeRes (Git or local)
        compute_res_path = os.path.join(self.workspace_root, "ComputeRes")
        parent_compute_res = os.path.join(os.path.dirname(self.workspace_root), "ComputeRes")
        
        if not os.path.exists(compute_res_path):
            if os.path.exists(parent_compute_res):
                print(f"[{self.node_id}] Found ComputeRes in parent directory. Symlinking...")
                os.symlink(parent_compute_res, compute_res_path)
            else:
                self._run_cmd(f"git clone https://github.com/polymath-void/ComputeRes.git {compute_res_path}", "ComputeRes (Git)")

    def _discover_workspace_capabilities(self):
        db_path = os.path.join(self.workspace_root, "agy_nodeos.db")
        if os.path.exists(db_path) or shutil.which("nodeos"):
            print(f"[{self.node_id}] 🟢 Mapped: Polymath-NodeOS")
            self.adapters["NodeOS"] = HolographicASTGraph(db_path)
            
        compute_res_path = os.path.join(self.workspace_root, "ComputeRes")
        if os.path.isdir(compute_res_path):
            print(f"[{self.node_id}] 🟢 Mapped: ComputeRes (Stateful OS)")
            self.adapters["ComputeRes"] = compute_res_path
            
        if shutil.which("jage") or os.path.isdir(os.path.join(self.workspace_root, "polymath-jage")):
            print(f"[{self.node_id}] 🟢 Mapped: Polymath-Jage (AST VC)")
            self.adapters["PolymathJage"] = True

    def register_mesh_tools(self):
        self.mesh.register_tool(name="ping_edge_node", schema={"returns": "pong"})
        if "NodeOS" in self.adapters:
            self.mesh.register_tool(name="query_holographic_ast", schema={"parameters": {"intent": "string"}})
        if "ComputeRes" in self.adapters:
            self.mesh.register_tool(name="query_skills", schema={"parameters": {"query": "string"}})
            self.mesh.register_tool(name="compute_res_manage_processes", schema={"parameters": {"action": "string"}})
        if "PolymathJage" in self.adapters:
            self.mesh.register_tool(name="jage_sync_ast", schema={"parameters": {}})

    async def boot_hub(self):
        self.register_mesh_tools()
        if "NodeOS" in self.adapters:
            try:
                asyncio.create_task(self.adapters["NodeOS"].generate_embeddings_background_task())
            except Exception:
                pass
        await self.mesh.start_mdns_broadcast()
        return self.governor
