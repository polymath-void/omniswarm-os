#!/usr/bin/env python3
"""
OmniSwarm-OS Diagnostic & Installation Verification Suite
Runs on any platform (Linux, macOS, Termux, Windows) to verify system integrity.
"""

import sys
import os
import platform

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log_pass(msg):
    print(f"[{GREEN}PASS{RESET}] {msg}")

def log_fail(msg):
    print(f"[{RED}FAIL{RESET}] {msg}")

def log_warn(msg):
    print(f"[{YELLOW}WARN{RESET}] {msg}")

def main():
    print(f"{CYAN}--- OmniSwarm-OS Diagnostic Self-Check ---{RESET}")
    print(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python  : {sys.version.split()[0]} ({sys.executable})\n")

    failures = 0
    warnings = 0

    # 1. Check Python Version
    if sys.version_info >= (3, 10):
        log_pass(f"Python version >= 3.10 ({sys.version_info.major}.{sys.version_info.minor})")
    else:
        log_fail(f"Python version must be >= 3.10 (Found: {sys.version_info.major}.{sys.version_info.minor})")
        failures += 1

    # 2. Check Core Dependencies
    is_termux = "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')
    deps = ["zmq", "tornado", "websockets"]
    if not is_termux:
        deps.append("psutil")

    for dep in deps:
        try:
            __import__(dep)
            log_pass(f"Core dependency: '{dep}' loaded successfully")
        except ImportError as e:
            log_fail(f"Missing dependency: '{dep}' ({e})")
            failures += 1

    # 3. Check OmniOS Package Import
    try:
        import omniswarm_py
        from omniswarm_py.mesh_config import load_mesh_config
        log_pass("Package: 'omniswarm_py' imported cleanly")
    except Exception as e:
        log_fail(f"Failed to import 'omniswarm_py': {e}")
        failures += 1
        return failures

    # 4. Check Mesh Configuration
    cfg = load_mesh_config()
    log_pass(f"Configuration: Role='{cfg.get('role')}', Hub='{cfg.get('hub_host')}:{cfg.get('rpc_port')}'")

    # 5. Check ComputeRes Execution Branch
    workspace_root = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(workspace_root, "ComputeRes", "compute_res", "tools", "evolved_skills")
    if os.path.exists(skills_dir):
        skills = [f for f in os.listdir(skills_dir) if f.endswith(".py") and not f.startswith("__")]
        log_pass(f"Execution Branch: ComputeRes present with {len(skills)} registered skills")
    else:
        log_warn("Execution Branch: ComputeRes skills directory not yet linked or cloned")
        warnings += 1

    # 6. Hub Probe (Non-blocking)
    hub_host = cfg.get("hub_host", "127.0.0.1")
    rpc_port = cfg.get("rpc_port", 5565)
    print(f"\nProbing configured Hub ({hub_host}:{rpc_port})...")
    try:
        import zmq
        ctx = zmq.Context.instance()
        sock = ctx.socket(zmq.REQ)
        sock.setsockopt(zmq.RCVTIMEO, 5000)
        sock.setsockopt(zmq.LINGER, 0)
        
        # SOCKS5 proxy check if on Android Termux and targeting Tailscale
        if is_termux and hub_host.startswith("100."):
            sock.setsockopt_string(zmq.SOCKS_PROXY, "127.0.0.1:1055")
            
        sock.connect(f"tcp://{hub_host}:{rpc_port}")
        sock.send_json({"agent_id": "Diagnostics", "tool": "ping_edge_node", "args": {}})
        reply = sock.recv_json()
        sock.close()
        if reply.get("status") == "success":
            log_pass(f"Hub Connectivity: Responsive! Handshake returned: {reply}")
        else:
            log_warn(f"Hub Connectivity: Responded with status {reply.get('status')}")
    except Exception as e:
        log_warn(f"Hub Connectivity: Could not reach hub ({e}). (Normal if daemon is not yet started)")
        warnings += 1

    # Summary
    print(f"\n{CYAN}--- Verification Summary ---{RESET}")
    if failures == 0:
        print(f"{GREEN}All critical system checks passed successfully! System is Swarm-Ready.{RESET}")
    else:
        print(f"{RED}Verification encountered {failures} error(s). Please review the logs above.{RESET}")

    return failures

if __name__ == "__main__":
    sys.exit(main())
