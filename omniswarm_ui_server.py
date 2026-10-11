#!/usr/bin/env python3
"""
OmniSwarm Cockpit UI Native Daemon & Zero-Token Server
Serves the Cockpit UI dashboard, streams real-time SSE events,
and handles generative UI actions over the OmniSwarm ZMQ mesh.
"""

import os
import sys
import json
import time
import socket
import asyncio
import platform
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from omniswarm_py.agent_harness import OmniOSAgentHarness
from omniswarm_py.mesh_config import load_mesh_config, save_mesh_config

WORKFLOW_FILE = "/data/data/com.termux/files/home/Projects/workflow.json"
HTML_FILE = os.path.join(SCRIPT_DIR, "cockpit_ui", "index.html")
HOST = "0.0.0.0"
PORT = 8765

# Thread-safe cached state
state_cache = {
    "messages": [],
    "logs": [],
    "workflow": None,
    "telemetry": {},
    "node_status": {},
    "last_update": 0
}
state_lock = threading.Lock()

def get_device_telemetry() -> Dict[str, Any]:
    is_termux = "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')
    vitals = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "is_termux": is_termux,
        "device_model": "Nothing Phone (2a)" if is_termux else platform.node(),
        "soc": "MediaTek Dimensity 7200 Pro (MT6886)" if is_termux else platform.processor(),
        "timestamp": time.time()
    }
    try:
        import psutil
        mem = psutil.virtual_memory()
        vitals["ram_total_mb"] = round(mem.total / (1024 * 1024), 1)
        vitals["ram_available_mb"] = round(mem.available / (1024 * 1024), 1)
        vitals["ram_used_percent"] = mem.percent
    except Exception:
        pass

    if is_termux:
        try:
            res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0:
                vitals["battery"] = json.loads(res.stdout)
        except Exception:
            pass

    return vitals

def probe_node_status() -> Dict[str, Any]:
    cfg = load_mesh_config(SCRIPT_DIR)
    hub_host = cfg.get("hub_host", "127.0.0.1")
    rpc_port = cfg.get("rpc_port", 5565)

    # Check phone daemon process
    phone_pid = None
    try:
        res = subprocess.run(["pgrep", "-f", "phone_agent.py --loop-only"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            phone_pid = res.stdout.strip().split()[-1]
    except Exception:
        pass

    # Quick probe PC hub socket
    hub_alive = False
    rtt_ms = None
    try:
        t0 = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        if s.connect_ex((hub_host, rpc_port)) == 0:
            hub_alive = True
            rtt_ms = round((time.time() - t0) * 1000, 2)
        s.close()
    except Exception:
        pass

    return {
        "phone_daemon_running": phone_pid is not None,
        "phone_daemon_pid": phone_pid,
        "pc_hub_reachable": hub_alive,
        "rtt_ms": rtt_ms,
        "config": cfg
    }

async def async_poller():
    harness = None
    while True:
        try:
            telemetry = get_device_telemetry()
            node_status = probe_node_status()

            workflow = None
            if os.path.exists(WORKFLOW_FILE):
                try:
                    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                        workflow = json.load(f)
                except Exception:
                    pass

            chat_msgs, direct_msgs, logs = [], [], []
            if node_status.get("pc_hub_reachable"):
                try:
                    if harness is None:
                        harness = OmniOSAgentHarness(agent_id="CockpitMonitor")
                        await harness.connect()
                    chat_msgs = await harness.chat_read("swarm_dev", limit=40)
                    direct_msgs = await harness.read_my_messages(since_id=0, limit=40)
                    logs = await harness.stream_agent_logs(limit=40)
                except Exception:
                    if harness:
                        try:
                            harness.disconnect()
                        except Exception:
                            pass
                    harness = None

            combined_messages = []
            seen_ids = set()
            for m in (chat_msgs + direct_msgs):
                m_id = m.get("id") or m.get("timestamp")
                if m_id not in seen_ids:
                    seen_ids.add(m_id)
                    combined_messages.append(m)

            combined_messages.sort(key=lambda x: x.get("timestamp", 0))

            with state_lock:
                state_cache["messages"] = combined_messages
                state_cache["logs"] = logs
                state_cache["workflow"] = workflow
                state_cache["telemetry"] = telemetry
                state_cache["node_status"] = node_status
                state_cache["last_update"] = time.time()

        except Exception:
            pass

        await asyncio.sleep(1.0)

def background_poller():
    """Background worker that continuously refreshes state with a persistent ZMQ connection."""
    asyncio.run(async_poller())

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class CockpitHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence standard HTTP access logging to keep terminal clean
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index.html"):
            if not os.path.exists(HTML_FILE):
                self.send_error(404, "cockpit_ui/index.html not found.")
                return
            with open(HTML_FILE, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        elif self.path == "/api/state":
            with state_lock:
                snapshot = dict(state_cache)
            self.send_json(snapshot)
            return

        elif self.path == "/api/stream":
            # Server-Sent Events (SSE) Stream
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                while True:
                    with state_lock:
                        snapshot = dict(state_cache)
                    payload = f"data: {json.dumps(snapshot)}\n\n"
                    self.wfile.write(payload.encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(1.0)
            except (BrokenPipeError, ConnectionResetError):
                return
            return

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            req_data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req_data = {}

        if self.path == "/api/action":
            # Dispatches a message or directive to an agent
            target = req_data.get("target", "PCAgent")
            message = req_data.get("message", "")
            data_payload = req_data.get("data", {})
            room = req_data.get("room")

            async def _send():
                async with OmniOSAgentHarness(agent_id="CockpitUI") as harness:
                    if room:
                        return await harness.chat_post(room, message, metadata=data_payload)
                    else:
                        return await harness.send_agent_message(target, message, data=data_payload)

            try:
                res = asyncio.run(_send())
                self.send_json({"status": "success", "result": res})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
            return

        elif self.path == "/api/node/toggle":
            action = req_data.get("action", "status")
            script = os.path.join(SCRIPT_DIR, "daemonize_phone.sh")
            try:
                res = subprocess.run(["bash", script, action], capture_output=True, text=True, timeout=10)
                self.send_json({
                    "status": "success",
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "returncode": res.returncode
                })
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
            return

        elif self.path == "/api/node/endpoint":
            hub_host = req_data.get("hub_host")
            rpc_port = req_data.get("rpc_port")
            if hub_host and rpc_port:
                cfg = load_mesh_config(SCRIPT_DIR)
                cfg["hub_host"] = str(hub_host)
                cfg["rpc_port"] = int(rpc_port)
                save_mesh_config(cfg, SCRIPT_DIR)
                # Restart daemon with new endpoint
                script = os.path.join(SCRIPT_DIR, "daemonize_phone.sh")
                subprocess.run(["bash", script, "restart"], capture_output=True, text=True)
                self.send_json({"status": "success", "updated_config": cfg})
            else:
                self.send_json({"status": "error", "message": "Missing hub_host or rpc_port"}, status=400)
            return

        elif self.path == "/api/remediate":
            action_type = req_data.get("type", "")
            cmd = ""
            if action_type == "git_pull":
                cmd = "git pull origin main"
            elif action_type == "git_rebase":
                cmd = "git pull origin main --rebase"
            elif action_type == "clean_cache":
                cmd = "rm -rf ~/.cache/*"
            elif action_type == "verify":
                cmd = f"{sys.executable} verify_install.py"

            if cmd:
                try:
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=SCRIPT_DIR, timeout=30)
                    self.send_json({
                        "status": "success",
                        "cmd": cmd,
                        "stdout": res.stdout,
                        "stderr": res.stderr,
                        "returncode": res.returncode
                    })
                except Exception as e:
                    self.send_json({"status": "error", "message": str(e)}, status=500)
            else:
                self.send_json({"status": "error", "message": "Unknown action type"}, status=400)
            return

        else:
            self.send_error(404, "Not Found")

def main():
    # Start poller thread
    t = threading.Thread(target=background_poller, daemon=True)
    t.start()

    server = ThreadedHTTPServer((HOST, PORT), CockpitHandler)
    print(f"\n=======================================================")
    print(f"  ⚡ OMNISWARM COCKPIT UI SERVER RUNNING               ")
    print(f"=======================================================")
    print(f"  Local Access   : http://localhost:{PORT}")
    print(f"  LAN Access     : http://192.168.0.103:{PORT}")
    print(f"  Real-time SSE  : http://localhost:{PORT}/api/stream")
    print(f"=======================================================\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CockpitServer] Stopping gracefully...")
        server.server_close()

if __name__ == "__main__":
    main()
