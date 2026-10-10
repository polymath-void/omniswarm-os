#!/usr/bin/env python3
"""
OmniSwarm Cross-Platform Real-Time Notification & Audio Ping Engine
=============================================================================
Eliminates battery-draining polling by providing event-driven push notifications
and audio pings across Windows, Android (Termux), Linux, and macOS.

Whenever an edge node (e.g. Phone Agent) sends a message to the PC Hub,
or when the PC Hub dispatches a task to the phone:
- Windows: Desktop Toast Notification + System Audio Chime.
- Android (Termux): Native Status Bar Notification (termux-notification) + Vibration.
- Linux: Desktop notification via notify-send.
- macOS: AppleScript notification.
=============================================================================
"""

import os
import sys
import subprocess
import threading
from typing import Optional

def _is_termux() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')

def notify(title: str, message: str, play_sound: bool = True):
    """
    Fires an asynchronous, non-blocking notification on the host OS.
    Never blocks the main thread or event loop.
    """
    threading.Thread(target=_dispatch_notification, args=(title, message, play_sound), daemon=True).start()

def _dispatch_notification(title: str, message: str, play_sound: bool):
    # 1. Android Termux
    if _is_termux():
        try:
            cmd = [
                "termux-notification",
                "--title", title,
                "--content", message,
                "--priority", "high"
            ]
            if play_sound:
                cmd.append("--sound")
            subprocess.run(cmd, capture_output=True, timeout=3)
            
            # Optional haptic vibration
            subprocess.run(["termux-vibrate", "-d", "150"], capture_output=True, timeout=2)
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
