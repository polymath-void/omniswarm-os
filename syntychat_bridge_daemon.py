#!/usr/bin/env python3
"""
SyntyChat Autonomous Zero-HIL Bridge Daemon
=============================================================================
Runs continuously on either Phone or PC to eliminate Human-In-The-Loop (HIL)
copy-pasting.

Modes:
- Autonomous Loop: Listens for incoming directives, executes local capabilities,
  and streams back stdout/stderr and status logs in real time.
- Log Watcher: Continuously streams local daemon/execution logs into 'ops_stream'.
- Interactive Chat: Terminal console for human/agent live swarm participation.

Usage:
  python syntychat_bridge_daemon.py --agent-id PhoneAgent --room swarm_dev
  python syntychat_bridge_daemon.py --agent-id PCAgent --room swarm_dev --role hub
=============================================================================
"""

import os
import sys
import json
import time
import asyncio
import argparse

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from omniswarm_py.agent_harness import OmniOSAgentHarness
from omniswarm_py.synty_bridge import AutonomousAgentBridge
from omniswarm_py.mesh_config import load_mesh_config

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

async def system_status_handler(payload):
    """Example autonomous handler for system status requests."""
    import platform
    return {
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "timestamp": time.time(),
        "status": "HEALTHY"
    }

async def execute_command_handler(payload):
    """Executes a non-blocking shell command locally and returns output."""
    cmd = payload.get("cmd", "echo 'no command'")
    print(f"⚡ [Autonomous Executor] Running: {cmd}")
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return {
        "stdout": stdout.decode().strip(),
        "stderr": stderr.decode().strip(),
        "exit_code": process.returncode
    }

async def main():
    parser = argparse.ArgumentParser(description="OmniSwarm SyntyChat Autonomous Bridge Daemon")
    parser.add_argument("--agent-id", default=f"Agent-{sys.platform}-{os.getpid()}", help="Identifier for this agent")
    parser.add_argument("--room", default="swarm_dev", help="Room to subscribe to")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Polling interval in seconds")
    args = parser.parse_args()

    cfg = load_mesh_config()
    print(f"\n{CYAN}======================================================={RESET}")
    print(f"{CYAN}   🚀 OMNISWARM AUTONOMOUS ZERO-HIL BRIDGE DAEMON     {RESET}")
    print(f"{CYAN}======================================================={RESET}")
    print(f"Agent ID        : {args.agent_id}")
    print(f"Subscribed Room : {args.room}")
    print(f"Mesh Hub Target : {cfg.get('hub_host')}:{cfg.get('rpc_port')}")
    print(f"Poll Interval   : {args.poll_interval}s")
    print(f"{CYAN}-------------------------------------------------------{RESET}\n")

    async with OmniOSAgentHarness(agent_id=args.agent_id) as harness:
        bridge = AutonomousAgentBridge(harness=harness, agent_id=args.agent_id, room=args.room)
        
        # Register standard autonomous handlers
        bridge.register_handler("verify_system_status", system_status_handler)
        bridge.register_handler("run_command", execute_command_handler)

        try:
            await bridge.run_loop(poll_interval=args.poll_interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print(f"\n[{args.agent_id}] Shutting down bridge gracefully...")
            bridge.stop()

if __name__ == "__main__":
    asyncio.run(main())
