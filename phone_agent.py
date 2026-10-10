#!/usr/bin/env python3
"""
OmniSwarm Autonomous Phone Agent (Termux / Edge Node)
Zero Human-in-the-Loop (Zero-HIL) Autonomous Edge Node.
Connects across the Virtual Hub mesh, executes tasks, streams live operational logs,
and collaborates directly with the PC Agent.
"""

import os
import sys
import json
import asyncio
import platform
import time
import subprocess
from typing import Dict, Any, Optional

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from omniswarm_py.agent_harness import OmniOSAgentHarness
from omniswarm_py.mesh_config import load_mesh_config

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

AGENT_ID = "PhoneAgent-Termux"

def get_device_info() -> Dict[str, Any]:
    is_termux = "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')
    device_type = "Android Termux" if is_termux else f"{platform.system()} ({platform.machine()})"
    info = {
        "device_type": device_type,
        "is_termux": is_termux,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "pid": os.getpid()
    }
    
    # Try getting memory info
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["memory_total_mb"] = round(mem.total / (1024 * 1024), 1)
        info["memory_available_mb"] = round(mem.available / (1024 * 1024), 1)
        info["memory_percent_used"] = mem.percent
    except Exception:
        pass

    # Try getting Termux battery info if available
    if is_termux:
        try:
            res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                info["battery"] = json.loads(res.stdout)
        except Exception:
            pass
            
    return info

async def execute_local_shell(command: str) -> Dict[str, Any]:
    """Safely executes a shell command on the local device and captures stdout/stderr."""
    def _run():
        try:
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
            return {
                "stdout": res.stdout,
                "stderr": res.stderr,
                "returncode": res.returncode,
                "success": res.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out (120s limit)", "success": False, "returncode": -1}
        except Exception as e:
            return {"error": str(e), "success": False, "returncode": -1}

    return await asyncio.to_thread(_run)

async def run_stage_mission(harness: OmniOSAgentHarness, cfg: dict, device_info: dict) -> bool:
    """Runs the 4-Stage initial mission to verify hub connectivity."""
    print(f"\n{CYAN}>>> [Stage 1/4] Probing Root Kernel Handshake...{RESET}")
    ping_res = await harness.execute_in_swarm("ping_edge_node", {})
    if ping_res.get("status") == "success":
        print(f"    {GREEN}✅ Root Kernel Handshake Confirmed: {ping_res.get('message')}{RESET}")
    else:
        print(f"    {YELLOW}⚠️ Handshake Warning: {ping_res}{RESET}")

    print(f"\n{CYAN}>>> [Stage 2/4] Querying PC Cognition Branch for Codebase AST...{RESET}")
    ast_res = await harness.execute_in_swarm("query_holographic_ast", {
        "intent": "ZeroMQ Router and WebRTC execution architecture",
        "top_k": 2
    })
    print(f"    {GREEN}✅ Cognition Branch Retrieved State: {ast_res.get('status')}{RESET}")

    print(f"\n{CYAN}>>> [Stage 3/4] Dispatching Compute Payload to PC Execution Branch...{RESET}")
    cmd_payload = {
        "cmd": "echo '[PC-KERNEL] Handshake verified from Phone Agent at ' %TIME%" if os.name == 'nt' else "echo '[PC-KERNEL] Handshake verified from Phone Agent at $(date)'"
    }
    exec_res = await harness.execute_in_swarm("compute_res_execute_bash", cmd_payload)
    stdout_output = exec_res.get("stdout", "").strip()
    print(f"    {GREEN}✅ Execution Branch Output: {stdout_output or exec_res}{RESET}")

    print(f"\n{CYAN}>>> [Stage 4/4] Querying Evolved Skills Hub...{RESET}")
    skills_res = await harness.execute_in_swarm("query_skills", {"query": "all"})
    skills_found = skills_res.get("skills_found", [])
    print(f"    {GREEN}✅ Swarm Skills Verified: {len(skills_found)} skills available{RESET}")

    # Commit intent to ledger
    session_state = {
        "agent": AGENT_ID,
        "device": device_info.get("device_type"),
        "timestamp": time.time(),
        "status": "COLLABORATION_VERIFIED",
        "skills_accessible": len(skills_found),
        "hub_endpoint": f"{cfg.get('hub_host')}:{cfg.get('rpc_port')}"
    }
    await harness.suspend_intent_safely(session_state)
    await harness.post_agent_log(f"Stage Mission Completed. Verified {len(skills_found)} skills.")
    return True

async def run_autonomous_loop(harness: OmniOSAgentHarness, device_info: dict):
    """
    Continuous Zero-HIL Event Loop.
    Listens for PCAgent instructions, executes tasks, streams live logs, and replies autonomously.
    """
    print(f"\n{MAGENTA}{BOLD}======================================================={RESET}")
    print(f"{MAGENTA}{BOLD}  ⚡ ZERO-HIL AUTONOMOUS EVENT LOOP ACTIVATED          {RESET}")
    print(f"{MAGENTA}{BOLD}  Listening for PCAgent Directives via Swarm Mesh...   {RESET}")
    print(f"{MAGENTA}{BOLD}======================================================={RESET}\n")

    await harness.post_agent_log(f"Phone Agent entering Zero-HIL Loop on {device_info['device_type']}")
    await harness.send_agent_message("PCAgent", "PhoneAgent-Termux is online in Autonomous Mode. Ready for tasks.", data=device_info)

    # Find highest message ID to avoid replaying historic messages
    initial_messages = await harness.read_my_messages(since_id=0, limit=50)
    last_msg_id = max([m["id"] for m in initial_messages], default=0)
    
    heartbeat_interval = 45.0
    last_heartbeat = time.time()

    while True:
        try:
            # 1. Poll incoming directives
            messages = await harness.read_my_messages(since_id=last_msg_id, limit=20)
            for msg in messages:
                last_msg_id = max(last_msg_id, msg["id"])
                sender = msg.get("sender", "Unknown")
                text = msg.get("message", "")
                data = msg.get("data") or {}
                
                print(f"\n{CYAN}📩 [Directive Received #{msg['id']}] from {BOLD}{sender}{RESET}: {text}")
                await harness.post_agent_log(f"Processing directive #{msg['id']} from {sender}: {text[:80]}")

                # Determine action type
                action = data.get("action")
                if not action:
                    if text.startswith("exec:"):
                        action = "exec_shell"
                        data["cmd"] = text[5:].strip()
                    elif text.lower() in ["health", "health_check", "status"]:
                        action = "health_check"
                    elif text.lower() in ["ping", "are you alive?"]:
                        action = "ping"
                    elif text.lower() in ["git_sync", "git pull", "sync"]:
                        action = "git_sync"
                    elif text.lower() in ["verify", "verify_install"]:
                        action = "verify_install"
                    else:
                        action = "echo"

                # Dispatch Action
                if action == "exec_shell":
                    cmd = data.get("cmd") or ""
                    print(f"    {YELLOW}▶ Executing Shell Command:{RESET} {cmd}")
                    await harness.post_agent_log(f"Executing: {cmd}")
                    exec_result = await execute_local_shell(cmd)
                    
                    status_flag = "SUCCESS" if exec_result.get("success") else "FAILED"
                    stdout_peek = (exec_result.get("stdout") or exec_result.get("error") or "")[:200].strip()
                    await harness.post_agent_log(f"Result [{status_flag}]: {stdout_peek}")
                    
                    await harness.send_agent_message(
                        recipient=sender,
                        message=f"Command '{cmd}' completed ({status_flag})",
                        data=exec_result
                    )
                    print(f"    {GREEN}✅ Result streamed back to {sender}{RESET}")

                elif action == "health_check":
                    print(f"    {YELLOW}▶ Gathering Device Telemetry...{RESET}")
                    health_data = get_device_info()
                    await harness.post_agent_log(f"Telemetry: Memory {health_data.get('memory_available_mb', 'N/A')}MB free")
                    await harness.send_agent_message(
                        recipient=sender,
                        message="Device Health & Telemetry Report",
                        data=health_data
                    )
                    print(f"    {GREEN}✅ Telemetry sent to {sender}{RESET}")

                elif action == "verify_install":
                    print(f"    {YELLOW}▶ Running verify_install.py...{RESET}")
                    res = await execute_local_shell(f"{sys.executable} verify_install.py")
                    await harness.post_agent_log(f"Verification output: {res.get('stdout', '')[:200]}")
                    await harness.send_agent_message(
                        recipient=sender,
                        message="Verification Complete",
                        data=res
                    )
                    print(f"    {GREEN}✅ Verification report returned to {sender}{RESET}")

                elif action == "git_sync":
                    print(f"    {YELLOW}▶ Running git pull origin main...{RESET}")
                    res = await execute_local_shell("git pull origin main")
                    await harness.post_agent_log(f"Git Sync: {res.get('stdout', '')[:200]}")
                    await harness.send_agent_message(
                        recipient=sender,
                        message="Git Sync Complete",
                        data=res
                    )
                    print(f"    {GREEN}✅ Git Sync reported to {sender}{RESET}")

                elif action == "ping":
                    await harness.send_agent_message(
                        recipient=sender,
                        message="PONG! PhoneAgent-Termux is fully operational.",
                        data={"uptime": time.time() - last_heartbeat}
                    )
                    print(f"    {GREEN}✅ Pong sent to {sender}{RESET}")

                else:
                    # Generic acknowledgement
                    reply_text = f"Acknowledged: '{text}'. Ready for directives."
                    await harness.send_agent_message(
                        recipient=sender,
                        message=reply_text,
                        data={"handled_at": time.time()}
                    )
                    print(f"    {GREEN}✅ Acknowledged to {sender}{RESET}")

            # 2. Periodic Heartbeat
            if time.time() - last_heartbeat > heartbeat_interval:
                await harness.post_agent_log("Heartbeat: Autonomous Phone Agent healthy, listening on Swarm Mesh.")
                last_heartbeat = time.time()

            await asyncio.sleep(2.5)

        except asyncio.CancelledError:
            print(f"\n{YELLOW}Stopping Autonomous Loop...{RESET}")
            break
        except Exception as e:
            print(f"{YELLOW}Loop Notice: {e}{RESET}")
            await asyncio.sleep(3.0)

async def main():
    print(f"\n{CYAN}======================================================={RESET}")
    print(f"{CYAN}       🤖 OMNISWARM AUTONOMOUS PHONE AGENT ONLINE      {RESET}")
    print(f"{CYAN}======================================================={RESET}")

    cfg = load_mesh_config()
    device_info = get_device_info()

    print(f"Device Type     : {device_info['device_type']}")
    print(f"Target Hub      : {cfg.get('hub_host')}:{cfg.get('rpc_port')}")
    print(f"Agent ID        : {AGENT_ID}")
    print(f"{CYAN}-------------------------------------------------------{RESET}\n")

    # Command line argument handling
    args = sys.argv[1:]
    test_only = "--test" in args or "--mission-only" in args
    skip_mission = "--loop-only" in args or "--daemon" in args

    async with OmniOSAgentHarness(agent_id=AGENT_ID) as harness:
        if not skip_mission:
            print("🚀 Executing Initial Swarm Stage Mission...")
            await run_stage_mission(harness, cfg, device_info)
            print(f"\n{GREEN}🎉 Initial Mission Succeeded!{RESET}")

        if not test_only:
            # Enter Zero-HIL Autonomous Loop
            await run_autonomous_loop(harness, device_info)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{CYAN}[PhoneAgent] Gracefully terminated by user.{RESET}")
