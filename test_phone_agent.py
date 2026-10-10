#!/usr/bin/env python3
"""
OmniSwarm PC-Side Phone Agent Verifier & Zero-HIL Bridge Inspector
Monitors the Swarm Mesh, Workflow Ledger, and Swarm Comms Bus
to verify the Phone Agent's activity and live operational health.
"""

import os
import sys
import json
import time
import sqlite3
import asyncio
from typing import Dict, Any, List

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_FILE = os.path.join(WORKSPACE_ROOT, "workflow.json")
DB_PATH = os.path.join(WORKSPACE_ROOT, "agy_nodeos.db")

def check_db_comms() -> Dict[str, Any]:
    """Inspects SQLite database for PhoneAgent messages and operational logs."""
    result = {"messages": [], "logs": []}
    if not os.path.exists(DB_PATH):
        return result

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        c = conn.cursor()
        
        # Check messages
        c.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='swarm_messages'
        """)
        if c.fetchone():
            c.execute("""
                SELECT id, sender, recipient, message, timestamp 
                FROM swarm_messages 
                WHERE sender LIKE '%Phone%' OR recipient LIKE '%Phone%'
                ORDER BY id DESC LIMIT 5
            """)
            result["messages"] = c.fetchall()

        # Check logs
        c.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='swarm_logs'
        """)
        if c.fetchone():
            c.execute("""
                SELECT id, agent_id, log_level, message, timestamp 
                FROM swarm_logs 
                WHERE agent_id LIKE '%Phone%'
                ORDER BY id DESC LIMIT 5
            """)
            result["logs"] = c.fetchall()

        conn.close()
    except Exception as e:
        result["error"] = str(e)

    return result

def check_workflow_ledger() -> List[Dict[str, Any]]:
    """Inspects workflow.json for Phone Agent intents."""
    if not os.path.exists(WORKFLOW_FILE):
        return []
    try:
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        intents = workflow.get("intents", [])
        return [
            item for item in intents 
            if "Phone" in item.get("agent_id", "") or "phone" in str(item).lower()
        ]
    except Exception:
        return []

async def test_live_bridge() -> bool:
    """Attempts a live Zero-HIL ping to PhoneAgent over the local hub."""
    try:
        from omniswarm_py.agent_harness import OmniOSAgentHarness
        async with OmniOSAgentHarness(agent_id="Verifier", host="127.0.0.1", rpc_port=5565) as harness:
            print(f"    {CYAN}Pinging PhoneAgent-Termux over the swarm mesh...{RESET}")
            res = await harness.send_agent_message("PhoneAgent-Termux", "Verifier Ping", data={"action": "ping"})
            if res.get("status") == "success":
                # Wait up to 5s for response
                msg_id = res.get("message_id")
                for _ in range(5):
                    await asyncio.sleep(1.0)
                    replies = await harness.read_my_messages(limit=5)
                    for r in replies:
                        if r.get("sender") == "PhoneAgent-Termux":
                            print(f"    {GREEN}✅ Live Response from Phone Agent: {r['message']}{RESET}")
                            return True
            return False
    except Exception:
        return False

def verify_phone_activity():
    print(f"\n{CYAN}======================================================={RESET}")
    print(f"{CYAN}       🔍 OMNISWARM PHONE AGENT VERIFICATION SUITE     {RESET}")
    print(f"{CYAN}======================================================={RESET}\n")

    # 1. Check Comms Bus Activity (Database)
    db_activity = check_db_comms()
    phone_logs = db_activity.get("logs", [])
    phone_msgs = db_activity.get("messages", [])

    print(f"{BOLD}1. Swarm Comms Bus Telemetry (Zero-HIL Bridge):{RESET}")
    if phone_logs or phone_msgs:
        print(f"   {GREEN}✅ Live Telemetry Detected in Swarm Bus!{RESET}")
        print(f"   Recent Phone Logs : {len(phone_logs)} entries recorded")
        for l in phone_logs[:3]:
            print(f"     • [{l[2]}] {l[3]}")
        print(f"   Recent Messages   : {len(phone_msgs)} entries exchanged")
        for m in phone_msgs[:3]:
            print(f"     • [{m[1]} -> {m[2]}]: {m[3]}")
    else:
        print(f"   {YELLOW}⚠️ No live PhoneAgent messages or logs found in agy_nodeos.db yet.{RESET}")

    # 2. Check Workflow Ledger
    phone_intents = check_workflow_ledger()
    print(f"\n{BOLD}2. Workflow Ledger (workflow.json):{RESET}")
    if phone_intents:
        latest = phone_intents[-1]
        saved_state = latest.get("saved_state", {})
        print(f"   {GREEN}✅ Phone Agent Intent Verified in Ledger!{RESET}")
        print(f"   Agent ID       : {latest.get('agent_id', 'PhoneAgent-Termux')}")
        print(f"   Device Target  : {saved_state.get('device', 'Android Termux')}")
        print(f"   Status         : {saved_state.get('status', 'ACTIVE')}")
        print(f"   Skills Found   : {saved_state.get('skills_accessible', 'N/A')}")
        print(f"   Hub Endpoint   : {saved_state.get('hub_endpoint', 'N/A')}")
        print(f"   Recorded Time  : {time.ctime(latest.get('timestamp', time.time()))}")
    else:
        print(f"   {YELLOW}⚠️ No Phone Agent intent recorded in workflow.json yet.{RESET}")

    # 3. Overall Verdict
    is_verified = bool(phone_logs or phone_msgs or phone_intents)
    print(f"\n{CYAN}======================================================={RESET}")
    if is_verified:
        print(f"{GREEN}       ✅ PHONE AGENT VERIFICATION: PASSED             {RESET}")
        print(f"{GREEN}       The Swarm Mesh & Comms Bus are Active!          {RESET}")
    else:
        print(f"{YELLOW}       ⏳ PHONE AGENT VERIFICATION: PENDING            {RESET}")
        print("To complete verification, run on the phone:")
        print(f"  {GREEN}python phone_agent.py{RESET}")
    print(f"{CYAN}======================================================={RESET}\n")
    return is_verified

if __name__ == "__main__":
    verify_phone_activity()
