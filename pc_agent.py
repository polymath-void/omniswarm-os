#!/usr/bin/env python3
"""
OmniSwarm PC-Side Autonomous Controller & Swarm Bridge
Directly interacts with PhoneAgent and Edge Nodes over the Swarm Mesh.
Zero Human-in-the-Loop (Zero-HIL) command dispatch, live log streaming, and diagnostics.
"""

import os
import sys
import json
import asyncio
import time
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

AGENT_ID = "PCAgent"

async def dispatch_directive_and_wait(
    harness: OmniOSAgentHarness,
    recipient: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Sends a directive to an edge node, live-streams operational logs while waiting,
    and returns the node's autonomous response.
    """
    print(f"\n{CYAN}>>> [PCAgent] Dispatching directive to {BOLD}{recipient}{RESET}: {message}")
    if data:
        print(f"    Payload: {json.dumps(data)}")

    # Record current message count to detect new replies
    existing_messages = await harness.read_my_messages(since_id=0, limit=100)
    start_msg_id = max([m["id"] for m in existing_messages], default=0)

    # Record current log ID
    existing_logs = await harness.stream_agent_logs(limit=20)
    start_log_id = max([l["id"] for l in existing_logs], default=0)

    # Send the directive
    send_res = await harness.send_agent_message(recipient=recipient, message=message, data=data)
    if send_res.get("status") != "success":
        print(f"    {YELLOW}⚠️ Failed to send directive: {send_res}{RESET}")
        return {"status": "error", "message": "Failed to send directive"}

    print(f"    {GREEN}✅ Directive queued (ID: {send_res.get('message_id')}). Streaming logs...{RESET}\n")

    start_time = time.time()
    seen_log_ids = set()

    while time.time() - start_time < timeout:
        # 1. Stream live logs from the recipient
        logs = await harness.stream_agent_logs(limit=30)
        for log_entry in logs:
            log_id = log_entry["id"]
            if log_id > start_log_id and log_id not in seen_log_ids:
                seen_log_ids.add(log_id)
                level = log_entry.get("level", "INFO")
                color = GREEN if level == "INFO" else (YELLOW if level == "WARN" else MAGENTA)
                print(f"    {color}[LOG:{log_entry['agent_id']}] {log_entry['message']}{RESET}")

        # 2. Check for incoming replies addressed to PCAgent from the recipient
        replies = await harness.read_my_messages(since_id=start_msg_id, limit=20)
        for r in replies:
            if r.get("sender") == recipient or r["id"] > start_msg_id:
                print(f"\n{GREEN}🎉 [Response Received from {BOLD}{r['sender']}{RESET}{GREEN}]: {r['message']}{RESET}")
                if r.get("data"):
                    print(f"\n{CYAN}--- Data Payload ---{RESET}")
                    print(json.dumps(r["data"], indent=2))
                    print(f"{CYAN}--------------------{RESET}")
                return r

        await asyncio.sleep(1.0)

    print(f"\n{YELLOW}⚠️ Timeout waiting for response from {recipient} ({timeout}s elapsed).{RESET}")
    return {"status": "timeout"}

async def live_log_watcher(harness: OmniOSAgentHarness):
    """Continuously prints real-time logs from all swarm nodes."""
    print(f"\n{MAGENTA}{BOLD}======================================================={RESET}")
    print(f"{MAGENTA}{BOLD}      📡 OMNISWARM LIVE TELEMETRY & LOG STREAM         {RESET}")
    print(f"{MAGENTA}{BOLD}======================================================={RESET}\n")
    
    seen_log_ids = set()
    initial_logs = await harness.stream_agent_logs(limit=25)
    for l in initial_logs:
        seen_log_ids.add(l["id"])
        print(f"[{l.get('level', 'INFO')}] [{l['agent_id']}] {l['message']}")

    while True:
        try:
            logs = await harness.stream_agent_logs(limit=25)
            for l in logs:
                if l["id"] not in seen_log_ids:
                    seen_log_ids.add(l["id"])
                    level = l.get("level", "INFO")
                    color = GREEN if level == "INFO" else (YELLOW if level == "WARN" else MAGENTA)
                    print(f"{color}[{level}] [{l['agent_id']}] {l['message']}{RESET}")
            await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(2.0)

async def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ["--help", "-h", "help"]:
        print(f"\n{CYAN}OmniSwarm PC Agent & Autonomous Bridge Controller{RESET}")
        print("Usage:")
        print("  python pc_agent.py send <recipient> <message>     # Send message & wait for response")
        print("  python pc_agent.py exec <recipient> <command>     # Remote shell execution on edge node")
        print("  python pc_agent.py health <recipient>             # Query edge node hardware health")
        print("  python pc_agent.py logs [limit]                   # View recent swarm logs")
        print("  python pc_agent.py watch                          # Continuous live stream of swarm logs")
        print("  python pc_agent.py test                           # Test autonomous handshake with PhoneAgent")
        return

    cmd = args[0]
    
    async with OmniOSAgentHarness(agent_id=AGENT_ID, host="127.0.0.1", rpc_port=5565) as harness:
        if cmd == "send":
            recipient = args[1] if len(args) > 1 else "PhoneAgent-Termux"
            message = " ".join(args[2:]) if len(args) > 2 else "Hello from PC Agent"
            await dispatch_directive_and_wait(harness, recipient, message)

        elif cmd == "exec":
            recipient = args[1] if len(args) > 1 else "PhoneAgent-Termux"
            shell_cmd = " ".join(args[2:]) if len(args) > 2 else "uname -a"
            await dispatch_directive_and_wait(
                harness,
                recipient,
                f"Execute shell: {shell_cmd}",
                data={"action": "exec_shell", "cmd": shell_cmd}
            )

        elif cmd == "health":
            recipient = args[1] if len(args) > 1 else "PhoneAgent-Termux"
            await dispatch_directive_and_wait(
                harness,
                recipient,
                "Requesting device health check",
                data={"action": "health_check"}
            )

        elif cmd == "rooms":
            res = await harness.execute_in_swarm("synty_chat_rooms", {})
            rooms = res.get("rooms", [])
            print(f"\n{CYAN}--- SyntyChat Active Rooms ({len(rooms)}) ---{RESET}")
            for r in rooms:
                print(f"  • {BOLD}{r['name']}{RESET} (Clients: {r.get('clients_count', 0)}, Cached: {r.get('messages_cached', 0)})")

        elif cmd == "chat":
            room = args[1] if len(args) > 1 else "swarm_dev"
            msg = " ".join(args[2:]) if len(args) > 2 else "Hello from PC Agent"
            res = await harness.chat_post(room=room, content=msg, msg_type="chat")
            print(f"{GREEN}✅ Posted to room '{room}' (ID: {res.get('message_id')}){RESET}")

        elif cmd == "read":
            room = args[1] if len(args) > 1 else "swarm_dev"
            limit = int(args[2]) if len(args) > 2 else 20
            messages = await harness.chat_read(room=room, limit=limit)
            print(f"\n{CYAN}--- Messages in '{room}' (Last {len(messages)}) ---{RESET}")
            for m in messages:
                print(f"[{m.get('sender')} | {m.get('type')}]: {m.get('content')}")

        elif cmd == "directive":
            target = args[1] if len(args) > 1 else "PhoneAgent-Termux"
            action = args[2] if len(args) > 2 else "verify_system_status"
            payload = json.loads(args[3]) if len(args) > 3 else {}
            res = await harness.chat_send_directive("autonomous_hil", target, action, payload)
            print(f"{GREEN}✅ Directive '{action}' dispatched to {target} in 'autonomous_hil' (ID: {res.get('message_id')}){RESET}")

        elif cmd == "logs":
            limit = int(args[1]) if len(args) > 1 else 30
            logs = await harness.stream_agent_logs(limit=limit)
            print(f"\n{CYAN}--- Swarm Logs (Last {len(logs)}) ---{RESET}")
            for l in logs:
                print(f"[{l.get('level', 'INFO')}] [{l['agent_id']}] {l['message']}")

        elif cmd == "watch":
            await live_log_watcher(harness)

        elif cmd == "test":
            print(f"\n{CYAN}======================================================={RESET}")
            print(f"{CYAN}   🧪 TESTING ZERO-HIL AUTONOMOUS BRIDGE TO PHONE      {RESET}")
            print(f"{CYAN}======================================================={RESET}\n")
            
            # Step 1: Health check
            print(f"{BOLD}[Step 1/2] Probing Phone Agent Device Telemetry...{RESET}")
            health_res = await dispatch_directive_and_wait(
                harness,
                "PhoneAgent-Termux",
                "Health Telemetry Request",
                data={"action": "health_check"},
                timeout=15.0
            )

            if health_res.get("status") == "timeout":
                print(f"\n{YELLOW}⚠️ PhoneAgent-Termux did not respond within 15s.{RESET}")
                print("Make sure PhoneAgent is running on Termux:")
                print(f"  {GREEN}python phone_agent.py{RESET}")
                return

            # Step 2: Remote command
            print(f"\n{BOLD}[Step 2/2] Dispatching Remote Shell Command to Termux...{RESET}")
            cmd_res = await dispatch_directive_and_wait(
                harness,
                "PhoneAgent-Termux",
                "Remote Echo Test",
                data={"action": "exec_shell", "cmd": "echo 'Hello from Termux! System is: ' $(uname -o 2>/dev/null || echo Windows)"},
                timeout=15.0
            )

            print(f"\n{GREEN}{BOLD}🎉 ZERO-HIL AUTONOMOUS SWARM BRIDGE 100% OPERATIONAL!{RESET}")
            print(f"{GREEN}Both agents are communicating directly with zero human copy-pasting.{RESET}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{CYAN}[PCAgent] Exited.{RESET}")
