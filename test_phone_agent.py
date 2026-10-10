#!/usr/bin/env python3
"""
OmniSwarm PC-Side Phone Agent Verifier
Monitors the Swarm Mesh and Workflow Ledger to verify the Phone Agent's activity.
"""

import os
import sys
import json
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_FILE = os.path.join(WORKSPACE_ROOT, "workflow.json")

def verify_phone_activity():
    print(f"\n{CYAN}======================================================={RESET}")
    print(f"{CYAN}       🔍 OMNISWARM PHONE AGENT VERIFICATION SUITE     {RESET}")
    print(f"{CYAN}======================================================={RESET}\n")

    if not os.path.exists(WORKFLOW_FILE):
        print(f"{YELLOW}[Status] workflow.json ledger not yet present.{RESET}")
        print("Please tell the Phone Agent to execute:")
        print(f"  {GREEN}python phone_agent.py{RESET}")
        print("to establish its presence in the Swarm workflow ledger.\n")
        return False

    try:
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"[Error] Failed to read workflow.json: {e}")
        return False

    intents = workflow.get("intents", [])
    phone_intents = [
        item for item in intents 
        if "PhoneAgent" in item.get("agent_id", "") 
        or "phone" in item.get("saved_state", {}).get("device", "").lower()
        or "termux" in item.get("saved_state", {}).get("device", "").lower()
    ]

    if not phone_intents:
        print(f"{YELLOW}[Status] No Phone Agent intents recorded yet in workflow.json.{RESET}")
        print(f"Total intents in ledger: {len(intents)}")
        print("\nHave the Phone Agent run:")
        print(f"  {GREEN}python phone_agent.py{RESET}\n")
        return False

    latest = phone_intents[-1]
    saved_state = latest.get("saved_state", {})
    
    print(f"{GREEN}🎉 PHONE AGENT INTENT VERIFIED IN SWARM LEDGER!{RESET}")
    print(f"Agent ID       : {latest.get('agent_id')}")
    print(f"Device Target  : {saved_state.get('device')}")
    print(f"Status         : {saved_state.get('status')}")
    print(f"Skills Found   : {saved_state.get('skills_accessible')}")
    print(f"Hub Endpoint   : {saved_state.get('hub_endpoint')}")
    print(f"Recorded Time  : {time.ctime(latest.get('timestamp', time.time()))}")
    print(f"\n{CYAN}======================================================={RESET}")
    print(f"{GREEN}       ✅ PHONE AGENT VERIFICATION: PASSED             {RESET}")
    print(f"{CYAN}======================================================={RESET}\n")
    return True

if __name__ == "__main__":
    verify_phone_activity()
