#!/usr/bin/env python3
"""
OmniSwarm Inbox & Notice Checker
Reads the latest incoming messages and notices from swarm peers (e.g. PCAgent).
"""

import os
import sys
import json
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, REPO_DIR)

from omniswarm_py.notifier import get_latest_notice, mark_notice_read

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

def main():
    parser = argparse.ArgumentParser(description="Check OmniSwarm Inbox & Notices")
    parser.add_argument("--mark-read", action="store_true", help="Mark notice as read")
    parser.add_argument("--all", action="store_true", help="Show all recent inbox messages")
    args = parser.parse_args()

    latest = get_latest_notice()
    if not latest:
        print(f"{YELLOW}No OmniSwarm notices found.{RESET}")
    else:
        status_badge = f"{YELLOW}[UNREAD]{RESET}" if latest.get("unread") else f"{GREEN}[READ]{RESET}"
        print(f"\n{CYAN}{BOLD}=== OmniSwarm Latest Notice ==={RESET}")
        print(f"Status : {status_badge}")
        print(f"Time   : {latest.get('time_str')}")
        print(f"Sender : {BOLD}{latest.get('sender')}{RESET}")
        print(f"Message: {latest.get('message')}")
        if latest.get("data"):
            print(f"Data   : {json.dumps(latest.get('data'))}")
        print(f"{CYAN}==============================={RESET}\n")

        if args.mark_read:
            mark_notice_read()
            print(f"{GREEN}Marked notice as read.{RESET}")

    if args.all:
        inbox_path = os.path.join(REPO_DIR, ".inbox.jsonl")
        if os.path.exists(inbox_path):
            print(f"\n{CYAN}{BOLD}--- Recent Inbox History ---{RESET}")
            with open(inbox_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-10:]
            for line in lines:
                try:
                    entry = json.loads(line.strip())
                    print(f"[{entry.get('time_str')}] {entry.get('sender')}: {entry.get('message')[:80]}")
                except Exception:
                    pass

if __name__ == "__main__":
    main()
