#!/usr/bin/env python3
"""
OmniSwarm Antigravity Reactive Bridge Watcher
Zero Human-in-the-Loop (Zero-HIL) Event Bridge.

Listens for cognitive directives from PCAgent / PC Hub.
When a directive is detected, writes it to workflow.json and exits (code 0),
triggering Antigravity's Reactive Wakeup automatically.
"""

import os
import sys
import json
import time
import asyncio
import argparse
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from omniswarm_py.agent_harness import OmniOSAgentHarness
from omniswarm_py.mesh_config import load_mesh_config

BRIDGE_SIGNAL_FILE = os.path.join(SCRIPT_DIR, ".antigravity_bridge.json")
WORKFLOW_FILE = "/data/data/com.termux/files/home/Projects/workflow.json"

async def watch_for_directives(agent_id: str, timeout: float = 0.0):
    cfg = load_mesh_config(SCRIPT_DIR)
    hub_host = cfg.get("hub_host", "127.0.0.1")
    rpc_port = cfg.get("rpc_port", 5565)

    print(f"[BridgeWatcher] Connecting to Swarm Hub at {hub_host}:{rpc_port} as '{agent_id}'...")
    
    async with OmniOSAgentHarness(agent_id=agent_id, host=hub_host, rpc_port=rpc_port) as harness:
        # Determine latest message ID watermark to avoid replaying historic messages
        try:
            latest_info = await harness.get_latest_ids()
            last_msg_id = latest_info.get("latest_message_id", 0)
        except Exception:
            existing = await harness.read_my_messages(since_id=0, limit=50)
            last_msg_id = max([m["id"] for m in existing], default=0)

        print(f"[BridgeWatcher] Listening for incoming PC directives (Watermark: #{last_msg_id})...")
        start_time = time.time()

        while True:
            # 1. Check direct messages from OmniOS Hub
            try:
                messages = await harness.read_my_messages(since_id=last_msg_id, limit=10)
                valid_msgs = [m for m in messages if m.get("sender") not in [agent_id, "Antigravity"]]
                
                if valid_msgs:
                    target_msg = valid_msgs[0]
                    msg_id = target_msg.get("id")
                    sender = target_msg.get("sender", "PCAgent")
                    text = target_msg.get("message", "")
                    data = target_msg.get("data") or {}

                    # Ignore simple ack loop echoes
                    if text.startswith("Acknowledged:") and not data.get("force_process"):
                        last_msg_id = max(last_msg_id, msg_id)
                        await asyncio.sleep(1.0)
                        continue

                    print("\n=======================================================")
                    print("⚡ ANTIGRAVITY REACTIVE WAKEUP: DIRECTIVE FROM PC")
                    print("=======================================================")
                    print(f"Message ID : #{msg_id}")
                    print(f"Sender     : {sender}")
                    print(f"Directive  : {text}")
                    if data:
                        print(f"Data       : {json.dumps(data, indent=2)}")
                    print("=======================================================")

                    # Persist to workflow.json for NodeOS lifecycle tracking
                    workflow_entry = {
                        "task_id": f"task-pc-{msg_id}",
                        "sender": sender,
                        "source": "PCAgent",
                        "status": "pending",
                        "intent": text,
                        "data": data,
                        "timestamp": time.time()
                    }
                    try:
                        with open(WORKFLOW_FILE, "w", encoding="utf-8") as wf:
                            json.dump(workflow_entry, wf, indent=2)
                        print(f"[BridgeWatcher] Staged task into {WORKFLOW_FILE}")
                    except Exception as we:
                        print(f"[BridgeWatcher] Warning writing workflow.json: {we}")

                    # Clean signal file if exists
                    if os.path.exists(BRIDGE_SIGNAL_FILE):
                        try:
                            os.remove(BRIDGE_SIGNAL_FILE)
                        except Exception:
                            pass

                    # Exit immediately to trigger Antigravity Reactive Wakeup
                    sys.exit(0)

            except Exception as e:
                print(f"[BridgeWatcher] Polling notice: {e}")

            # 2. Check local bridge signal file (dispatched by PhoneAgent daemon)
            if os.path.exists(BRIDGE_SIGNAL_FILE):
                try:
                    with open(BRIDGE_SIGNAL_FILE, "r", encoding="utf-8") as bf:
                        sig_data = json.load(bf)
                    print("\n=======================================================")
                    print("⚡ ANTIGRAVITY REACTIVE WAKEUP: BRIDGE SIGNAL DETECTED")
                    print("=======================================================")
                    print(f"Sender    : {sig_data.get('sender', 'PCAgent')}")
                    print(f"Directive : {sig_data.get('message', '')}")
                    print("=======================================================")
                    os.remove(BRIDGE_SIGNAL_FILE)
                    sys.exit(0)
                except Exception:
                    pass

            # Timeout check if configured
            if timeout > 0 and (time.time() - start_time) > timeout:
                print(f"[BridgeWatcher] Timeout of {timeout}s reached. Exiting gracefully.")
                sys.exit(0)

            await asyncio.sleep(1.0)

def main():
    parser = argparse.ArgumentParser(description="OmniSwarm Reactive Bridge Watcher for Antigravity")
    parser.add_argument("--agent-id", default="Antigravity", help="Agent ID to listen for")
    parser.add_argument("--timeout", type=float, default=0.0, help="Max wait seconds (0 = wait until message)")
    args = parser.parse_args()

    try:
        asyncio.run(watch_for_directives(agent_id=args.agent_id, timeout=args.timeout))
    except KeyboardInterrupt:
        print("\n[BridgeWatcher] Terminated by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
