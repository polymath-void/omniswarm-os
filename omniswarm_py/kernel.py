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

    def _ensure_venv(self):
        if self._is_termux():
            return
            
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if in_venv:
            return
            
        import sysconfig
        stdlib_path = sysconfig.get_path("stdlib")
        if stdlib_path and os.path.exists(os.path.join(stdlib_path, "EXTERNALLY-MANAGED")):
            venv_dir = os.path.join(self.workspace_root, ".omnios_venv")
            if not os.path.exists(venv_dir):
                print(f"[{self.node_id}] System is externally managed. Creating isolated .omnios_venv...")
                subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
            
            if sys.platform == 'win32':
                python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
                venv_bin = os.path.join(venv_dir, "Scripts")
            else:
                python_exe = os.path.join(venv_dir, "bin", "python")
                venv_bin = os.path.join(venv_dir, "bin")
                
            if os.path.abspath(sys.executable) != os.path.abspath(python_exe):
                print(f"[{self.node_id}] Proxying daemon process into isolated venv...")
                os.environ["PATH"] = venv_bin + os.pathsep + os.environ.get("PATH", "")
                os.execv(python_exe, [python_exe] + sys.argv)

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
        self._ensure_venv()
        
        # 1. Check/Symlink NodeOS database
        self._symlink_from_umbrella("agy_nodeos.db")
        if not shutil.which("nodeos"):
            try:
                import zmq
            except ImportError:
                print(f"[{self.node_id}] Installing Core Python Dependencies (pyzmq, psutil, tornado)...")
                req_file = os.path.join(self.parent_root, "omniswarm-os", "requirements.txt")
                if os.path.exists(req_file):
                    pip_cmd = f"{sys.executable} -m pip install -r {req_file}" + (" --break-system-packages" if self._is_termux() else "")
                    self._run_cmd(pip_cmd, "OmniOS Core Requirements")
            pip_cmd = f"{sys.executable} -m pip install polymath-nodeos" + (" --break-system-packages" if self._is_termux() else "")
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
        
        try:
            from comms import SwarmCommsBus
        except ImportError:
            from omniswarm_py.comms import SwarmCommsBus
        self.comms_bus = SwarmCommsBus(db_path, self.workspace_root)
        
        self.mesh.register_tool(name="ping_edge_node", schema={"returns": "pong"})
        self.mesh.register_tool(name="compute_res_execute_bash", schema={"parameters": {"cmd": "string"}})
        self.mesh.register_tool(name="trigger_intent_gc", schema={"description": "Cleans up completed intents instantly."})
        self.mesh.register_tool(name="query_os_events", schema={"parameters": {"since_timestamp": "float"}})
        self.mesh.register_tool(name="synty_chat_post", schema={"parameters": {"room": "string", "content": "any"}})
        self.mesh.register_tool(name="synty_chat_read", schema={"parameters": {"room": "string", "since_timestamp": "float"}})
        self.mesh.register_tool(name="synty_chat_rooms", schema={"parameters": {}})
        
        # Autonomous Agent-to-Agent Mesh Tools (Zero-HIL Architecture)
        self.mesh.register_tool(name="swarm_send_message", schema={"parameters": {"recipient": "string", "message": "string"}})
        self.mesh.register_tool(name="swarm_read_messages", schema={"parameters": {"since_id": "integer"}})
        self.mesh.register_tool(name="swarm_post_log", schema={"parameters": {"log_level": "string", "message": "string"}})
        self.mesh.register_tool(name="swarm_stream_logs", schema={"parameters": {"limit": "integer"}})
        self.mesh.register_tool(name="swarm_sync_intent", schema={"parameters": {"intent": "object"}})
        self.mesh.register_tool(name="swarm_get_latest_ids", schema={"parameters": {}})
        self.mesh.register_tool(name="swarm_get_latest_message_id", schema={"parameters": {}})
        
        if "Cognition" in self.branches and self.branches["Cognition"]:
            self.mesh.register_tool(name="query_holographic_ast", schema={"parameters": {"intent": "string"}})
        if "Execution" in self.branches and self.branches["Execution"]:
            self.mesh.register_tool(name="query_skills", schema={"parameters": {"query": "string"}})
        if "Time" in self.branches and self.branches["Time"]:
            self.mesh.register_tool(name="jage_sync_ast", schema={"parameters": {}})
            
        original_handler = self.mesh.handle_incoming_request
        async def hooked_handler(tool_name: str, args: dict):
            if tool_name in ["synty_chat_post", "synty_chat_read", "synty_chat_rooms"]:
                try:
                    from synty_bridge import SyntySwarmBridge
                except ImportError:
                    from omniswarm_py.synty_bridge import SyntySwarmBridge
                bridge = SyntySwarmBridge(broker=self.mesh, comms_bus=self.comms_bus)
                return await bridge.handle_chat_rpc(tool_name, args)
            if tool_name == "query_os_events":
                return {"status": "success", "events": self.event_ledger.query_events_since(args.get("since_timestamp", 0.0))}
            if tool_name == "trigger_intent_gc":
                return self.intent_gc.sweep_completed_intents()
            if tool_name == "swarm_send_message":
                sender = args.get("sender") or args.get("agent_id") or "AnonymousAgent"
                msg_text = args.get("message", "")
                res = self.comms_bus.send_message(sender, args.get("recipient", "*"), msg_text, args.get("data"))
                if sender not in ["PCAgent", "Verifier"]:
                    try:
                        try:
                            from notifier import notify
                        except ImportError:
                            from omniswarm_py.notifier import notify
                        notify(f"📱 OmniSwarm: {sender}", msg_text[:100])
                    except Exception:
                        pass
                return res
            if tool_name == "swarm_read_messages":
                agent = args.get("agent_id") or args.get("recipient")
                return {"status": "success", "messages": self.comms_bus.get_messages(agent, args.get("since_id", 0), args.get("limit", 20))}
            if tool_name == "swarm_post_log":
                agent = args.get("agent_id") or "AnonymousAgent"
                return self.comms_bus.post_log(agent, args.get("log_level", "INFO"), args.get("message", ""))
            if tool_name == "swarm_stream_logs":
                return {"status": "success", "logs": self.comms_bus.get_logs(args.get("agent_id"), args.get("limit", 50))}
            if tool_name == "swarm_sync_intent":
                intent = args.get("intent", {})
                success = self.comms_bus.sync_workflow_intent(intent)
                return {"status": "success" if success else "error"}
            if tool_name in ["swarm_get_latest_ids", "swarm_get_latest_message_id"]:
                return {
                    "status": "success",
                    "latest_message_id": self.comms_bus.get_latest_message_id(),
                    "latest_id": self.comms_bus.get_latest_message_id(),
                    "latest_log_id": self.comms_bus.get_latest_log_id()
                }
            if tool_name in ["query_skills", "publish_skill", "adapt_and_publish_skill"] and "Execution" in self.branches:
                return await self.branches["Execution"].dispatch_intent(b"Mesh-Client", {"type": "SKILL_ROUTER_INVOKE", "args": args})
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
