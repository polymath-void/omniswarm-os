import sys
import os
import subprocess
import shutil

def is_termux():
    return "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')

def ensure_environment():
    """Ensures dependencies are installed and proxies the process into a VENV if on PC."""
    try:
        import zmq
        import psutil
        import tornado
        return # Everything is installed and accessible
    except ImportError:
        pass # Needs installation

    print("\n[Bootloader] Missing dependencies detected. Initiating Auto-Setup...")
    workspace_root = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(workspace_root, "requirements.txt")
    
    if is_termux():
        print("[Bootloader] Termux OS Detected. Force-installing global packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file, "--break-system-packages"], check=True)
        print("[Bootloader] Dependencies installed. Restarting daemon...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print("[Bootloader] PC Environment Detected (PEP 668 Guard active).")
        venv_path = os.path.join(workspace_root, ".omnios_venv")
        
        # Windows vs POSIX paths
        if os.name == 'nt':
            python_exe = os.path.join(venv_path, "Scripts", "python.exe")
            pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
        else:
            python_exe = os.path.join(venv_path, "bin", "python")
            pip_exe = os.path.join(venv_path, "bin", "pip")

        if sys.prefix == venv_path:
            # We are inside the venv but still missing packages? Install them.
            subprocess.run([pip_exe, "install", "-r", req_file], check=True)
            return

        if not os.path.exists(venv_path):
            print(f"[Bootloader] Creating isolated virtual environment at {venv_path}...")
            import venv
            venv.create(venv_path, with_pip=True)
            print("[Bootloader] Installing dependencies into VENV...")
            subprocess.run([pip_exe, "install", "-r", req_file], check=True)

        print("[Bootloader] Shifting process execution into isolated VENV...")
        os.execv(python_exe, [python_exe] + sys.argv)
