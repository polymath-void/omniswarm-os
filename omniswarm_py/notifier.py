#!/usr/bin/env python3
"""
OmniSwarm Cross-Platform Real-Time Notification & Audio Ping Engine
=============================================================================
Eliminates battery-draining polling by providing event-driven push notifications,
visual toasts, audio pings, and shared notice state across Android (Termux),
Windows, Linux, and macOS.
=============================================================================
"""

import os
import sys
import json
import time
import subprocess
import threading
from typing import Optional, Dict, Any

NOTICE_PATHS = [
    os.path.join(os.getcwd(), ".latest_notice.json"),
    os.path.expanduser("~/.omniswarm_latest_notice.json")
]

INBOX_PATHS = [
    os.path.join(os.getcwd(), ".inbox.jsonl"),
    os.path.expanduser("~/.omniswarm_inbox.jsonl")
]

def _is_termux() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')

def record_notice(sender: str, message: str, title: Optional[str] = None, msg_id: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
    """
    Persists incoming notice to shared state files for conversational awareness.
    """
    notice_record = {
        "timestamp": time.time(),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "sender": sender,
        "title": title or f"OmniSwarm: {sender}",
        "message": message,
        "id": msg_id,
        "data": data or {},
        "unread": True
    }
    
    # Write latest notice atomically
    for p in NOTICE_PATHS:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
            tmp_p = f"{p}.tmp"
            with open(tmp_p, "w", encoding="utf-8") as f:
                json.dump(notice_record, f, indent=2)
            os.replace(tmp_p, p)
        except Exception:
            pass

    # Append to inbox ledger
    line = json.dumps(notice_record) + "\n"
    for p in INBOX_PATHS:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

def get_latest_notice() -> Optional[Dict[str, Any]]:
    """Returns the most recent notice recorded on this node."""
    for p in NOTICE_PATHS:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return None

def mark_notice_read():
    """Marks the latest notice as read."""
    for p in NOTICE_PATHS:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["unread"] = False
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass

def notify(
    title: str,
    message: str,
    play_sound: bool = True,
    sender: Optional[str] = None,
    msg_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None
):
    """
    Fires an asynchronous, non-blocking notification on the host OS
    and records the notice to the node ledger.
    """
    # Record state immediately
    record_notice(sender=sender or "SwarmPeer", message=message, title=title, msg_id=msg_id, data=data)

    # Dispatch OS notification asynchronously
    threading.Thread(
        target=_dispatch_notification,
        args=(title, message, play_sound, sender),
        daemon=True
    ).start()

def _dispatch_notification(title: str, message: str, play_sound: bool, sender: Optional[str] = None):
    # 1. Android Termux
    if _is_termux():
        # A. Status bar notification
        try:
            cmd = [
                "termux-notification",
                "--id", "omniswarm_alert",
                "--title", title,
                "--content", message,
                "--priority", "max"
            ]
            if play_sound:
                cmd.append("--sound")
                cmd.extend(["--vibrate", "200,100,200"])
            subprocess.run(cmd, capture_output=True, timeout=3)
        except Exception:
            pass

        # B. Immediate transient on-screen overlay Toast
        try:
            display_sender = sender or "PCAgent"
            clean_msg = message.replace("\n", " ").strip()
            if len(clean_msg) > 100:
                clean_msg = clean_msg[:97] + "..."
            toast_text = f"🔔 {title}\n[{display_sender}]: {clean_msg}"
            subprocess.run(
                ["termux-toast", "-b", "#181825", "-c", "#a6e3a1", "-g", "top", toast_text],
                capture_output=True,
                timeout=3
            )
        except Exception:
            pass
        return

    # 2. Windows
    if sys.platform == "win32":
        # Audio chime via winsound
        if play_sound:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

        # Toast notification via PowerShell WinRT script
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "show_toast.ps1")
            if os.path.exists(script_path):
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, "-Title", title, "-Message", message],
                    capture_output=True,
                    timeout=5
                )
        except Exception:
            pass
        return

    # 3. macOS
    if sys.platform == "darwin":
        try:
            apple_script = f'display notification "{message}" with title "{title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", apple_script], capture_output=True, timeout=3)
        except Exception:
            pass
        return

    # 4. Standard Linux
    if sys.platform.startswith("linux"):
        try:
            subprocess.run(["notify-send", title, message], capture_output=True, timeout=3)
        except Exception:
            pass

