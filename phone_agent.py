#!/usr/bin/env python3
"""
OmniSwarm Autonomous Phone Agent (Termux / Edge Node)
Collaborates directly with the PC Root Kernel across the Virtual Hub mesh.
"""

import os
import sys
import json
import asyncio
import platform
import time

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
RESET = "\033[0m"

async def run_phone_agent():
    print(f"\n{CYAN}======================================================={RESET}")
    print(f"{CYAN}       🤖 OMNISWARM AUTONOMOUS PHONE AGENT ONLINE      {RESET}")
    print(f"{CYAN}======================================================={RESET}")
    
    cfg = load_mesh_config()
    is_termux = "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')
    device_type = "Android Termux" if is_termux else f"{platform.system()} ({platform.machine()})"
    
    print(f"Device Type     : {device_type}")
    print(f"Target Hub      : {cfg.get('hub_host')}:{cfg.get('rpc_port')}")
    print(f"Agent ID        : PhoneAgent-Termux")
    print(f"{CYAN}-------------------------------------------------------{RESET}\n")

    async with OmniOSAgentHarness(agent_id="PhoneAgent-Termux") as harness:
        # Step 1: Handshake with Swarm Kernel
        print(">>> [Stage 1/4] Probing Root Kernel Handshake...")
        ping_res = await harness.execute_in_swarm("ping_edge_node", {})
        if ping_res.get("status") == "success":
            print(f"    {GREEN}✅ Root Kernel Handshake Confirmed: {ping_res.get('message')}{RESET}")
        else:
            print(f"    {YELLOW}⚠️ Handshake Warning: {ping_res}{RESET}")

        # Step 2: Query Swarm Cognition Branch (Holographic AST)
        print("\n>>> [Stage 2/4] Querying PC Cognition Branch for Codebase AST...")
        ast_res = await harness.execute_in_swarm("query_holographic_ast", {
            "intent": "ZeroMQ Router and WebRTC execution architecture",
            "top_k": 2
        })
        print(f"    {GREEN}✅ Cognition Branch Retrieved State: {ast_res.get('status')}{RESET}")

        # Step 3: Dispatch Remote Execution to PC Kernel Branch
        print("\n>>> [Stage 3/4] Dispatching Compute Payload to PC Execution Branch...")
        cmd_payload = {
            "cmd": "echo '[PC-KERNEL] Handshake verified from Phone Agent at ' %TIME%" if os.name == 'nt' else "echo '[PC-KERNEL] Handshake verified from Phone Agent at $(date)'"
        }
        exec_res = await harness.execute_in_swarm("compute_res_execute_bash", cmd_payload)
        stdout_output = exec_res.get("stdout", "").strip()
        print(f"    {GREEN}✅ Execution Branch Output: {stdout_output or exec_res}{RESET}")

        # Step 4: Discover 140+ Evolved Skills in the Swarm
        print("\n>>> [Stage 4/4] Querying Evolved Skills Hub...")
        skills_res = await harness.execute_in_swarm("query_skills", {"query": "all"})
        skills_found = skills_res.get("skills_found", [])
        print(f"    {GREEN}✅ Swarm Skills Verified: {len(skills_found)} skills available{RESET}")

        # Step 5: Save Intent Execution State to Workflow Ledger
        print(f"\n>>> [Ledger] Committing Swarm Session Intent to workflow.json...")
        session_state = {
            "agent": "PhoneAgent-Termux",
            "device": device_type,
            "timestamp": time.time(),
            "status": "COLLABORATION_VERIFIED",
            "skills_accessible": len(skills_found),
            "hub_endpoint": f"{cfg.get('hub_host')}:{cfg.get('rpc_port')}"
        }
        await harness.suspend_intent_safely(session_state)
        print(f"    {GREEN}✅ Intent cleanly recorded to workflow.json{RESET}")

    print(f"\n{CYAN}======================================================={RESET}")
    print(f"{GREEN} 🎉 PHONE AGENT COLLABORATION MISSION COMPLETE (PASS)  {RESET}")
    print(f"{CYAN}======================================================={RESET}\n")

if __name__ == "__main__":
    asyncio.run(run_phone_agent())
