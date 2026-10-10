#!/usr/bin/env python3
"""
OmniSwarm System Rules Injector
=============================================================================
Automatically provisions permanent Antigravity (AGY) system rules for whoever
installs and uses OmniSwarm-OS across Windows, Linux, macOS, and Android (Termux).

This ensures any AI agent in future sessions instantly recognizes the Swarm
mesh, knows how to dispatch tasks to remote edge nodes (e.g. Phone Agent),
and operates with Zero Human-in-the-Loop (Zero-HIL).
=============================================================================
"""

import os
import sys
import argparse
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

HUB_RULE_CONTENT = """---
trigger: always_on
---
# OmniSwarm Autonomous Multi-Device Mesh Standard

Whenever the USER asks to communicate with the Phone Agent, check the phone, run commands on the phone/Termux, stream phone logs, or orchestrate distributed tasks across PC and mobile edge nodes:

1. **Architecture & Connection Details:**
   - **Local Workspace**: Current `omniswarm-os` repository or standard path.
   - **Local Hub Port**: `5565` (ZeroMQ RPC)
   - **Virtual Hub Relay**: `bore.pub:33458` (forwarding to PC's `localhost:5565`)
   - **Remote Agent ID**: `PhoneAgent-Termux` (Android Termux node)
   - **PC Agent ID**: `PCAgent`

2. **Zero-HIL Protocol (Zero Human-In-The-Loop):**
   - You MUST NOT instruct the human to copy and paste messages, commands, or logs between the PC and Phone.
   - Use the native Swarm Bridge CLI (`pc_agent.py`) via `run_command`:
     - **Send Message / Query**:
       `python pc_agent.py send PhoneAgent-Termux "<message>"`
     - **Execute Shell Command on Phone (Termux)**:
       `python pc_agent.py exec PhoneAgent-Termux "<command>"`
     - **Query Phone Device Health & Battery**:
       `python pc_agent.py health PhoneAgent-Termux`
     - **SyntyChat Room Discussion**:
       `python pc_agent.py chat swarm_dev "<message>"`
     - **Dispatch Autonomous Task Directive**:
       `python pc_agent.py directive PhoneAgent-Termux "<action>" '<json_payload>'`
     - **Stream Live Operational Logs**:
       `python pc_agent.py logs <limit>`
       `python pc_agent.py watch`

3. **Daemon Liveness Check:**
   - If port 5565 is not listening, verify and launch the OmniOS Root Kernel daemon:
     `python omniswarm_py/omniswarm_daemon.py`
   - Verify Bore tunnel is active:
     `Get-Process -Name bore -ErrorAction SilentlyContinue`
"""

EDGE_RULE_CONTENT = """---
trigger: always_on
---
# OmniSwarm Autonomous Edge Node (Android / Termux) Standard

Whenever operating within an OmniSwarm Edge Node environment (such as Android Termux or remote Linux):

1. **Architecture & Node Role:**
   - **Agent ID**: `PhoneAgent-Termux` (or configured node ID)
   - **Connection Mode**: Connects outbound to Virtual Hub (`bore.pub:33458`).
   - **Autonomous Loop**: `python phone_agent.py` or `python syntychat_bridge_daemon.py --agent-id PhoneAgent-Termux --room swarm_dev`.

2. **Zero-HIL Protocol (Zero Human-In-The-Loop):**
   - Do NOT ask the human to manually copy-paste terminal output to the PC.
   - Use the unified `SyntyChatServer` and `SwarmCommsBus` to stream logs directly:
     - Operations logs stream to room `ops_stream` (`chat_stream_log` or `post_agent_log`).
     - Task responses reply directly to `PCAgent` (`chat_send_directive` or `send_agent_message`).
   - Local command execution should be handled within the daemon loop without stalling the user.
"""

def inject_rules(role: str = "auto", workspace_root: str = None) -> bool:
    workspace_root = workspace_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Detect platform
    is_termux = "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')
    if role == "auto":
        role = "edge" if is_termux else "hub"

    home_dir = os.path.expanduser("~")
    global_rules_dir = os.path.join(home_dir, ".gemini", "config", "rules")
    workspace_rules_dir = os.path.join(workspace_root, ".agents", "rules")

    rule_filename = "omniswarm_orchestrator.md" if role == "hub" else "omniswarm_edge_node.md"
    rule_content = HUB_RULE_CONTENT if role == "hub" else EDGE_RULE_CONTENT

    success = False
    
    # 1. Inject into Global Config (~/.gemini/config/rules)
    try:
        os.makedirs(global_rules_dir, exist_ok=True)
        global_rule_path = os.path.join(global_rules_dir, rule_filename)
        with open(global_rule_path, "w", encoding="utf-8") as f:
            f.write(rule_content)
        print(f"[Rules Injector] ✅ Global rule installed at: {global_rule_path}")
        success = True
    except Exception as e:
        print(f"[Rules Injector] ⚠️ Could not write global rule: {e}")

    # 2. Inject into Workspace Project (.agents/rules)
    try:
        os.makedirs(workspace_rules_dir, exist_ok=True)
        workspace_rule_path = os.path.join(workspace_rules_dir, rule_filename)
        with open(workspace_rule_path, "w", encoding="utf-8") as f:
            f.write(rule_content)
        print(f"[Rules Injector] ✅ Workspace rule installed at: {workspace_rule_path}")
        success = True
    except Exception as e:
        print(f"[Rules Injector] ⚠️ Could not write workspace rule: {e}")

    return success

def main():
    parser = argparse.ArgumentParser(description="OmniSwarm Permanent Rules Injector")
    parser.add_argument("--role", choices=["hub", "edge", "auto"], default="auto", help="Node role (hub or edge)")
    parser.add_argument("--workspace", default=None, help="Root directory of workspace")
    args = parser.parse_args()

    print("======================================================================")
    print("        OmniSwarm Permanent System Rules Provisioner                  ")
    print("======================================================================")
    
    ok = inject_rules(role=args.role, workspace_root=args.workspace)
    if ok:
        print("\n🎉 OmniSwarm system rules are permanently active across all sessions!")
    else:
        print("\n❌ Failed to write system rules.")
        sys.exit(1)

if __name__ == "__main__":
    main()
