#!/usr/bin/env bash
# ==============================================================================
# OmniSwarm-OS Universal Installer for Linux, macOS, and Android (Termux)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ROLE="edge"
HUB_HOST="bore.pub"
HUB_PORT=33458
NODE_ID="OmniNode-$(uname -s)-$$"

while [[ $# -gt 0 ]]; do
  case $1 in
    --role)
      ROLE="$2"
      shift 2
      ;;
    --hub-host)
      HUB_HOST="$2"
      shift 2
      ;;
    --hub-port)
      HUB_PORT="$2"
      shift 2
      ;;
    --node-id)
      NODE_ID="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: bash install.sh [--role hub|edge] [--hub-host <host>] [--hub-port <port>] [--node-id <id>]"
      exit 1
      ;;
  esac
done

echo "======================================================================"
echo "          OmniSwarm-OS Universal Cross-Platform Installer             "
echo "======================================================================"
echo "Target Platform : $(uname -s) ($(uname -m))"
echo "Assigned Role   : $ROLE"
echo "Target Hub      : $HUB_HOST:$HUB_PORT"
echo "Node ID         : $NODE_ID"
echo "======================================================================"

IS_TERMUX=false
if [ -n "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
  IS_TERMUX=true
  echo ">>> [Environment] Android Termux detected."
fi

# 1. Dependency package installation
if [ "$IS_TERMUX" = true ]; then
  echo ">>> [Dependencies] Checking Termux system packages..."
  if ! command -v python >/dev/null 2>&1; then
    echo ">>> Installing python via pkg..."
    pkg update -y && pkg install -y python
  fi
  if ! command -v clang >/dev/null 2>&1; then
    echo ">>> Installing clang & build tools for C-extensions (pyzmq)..."
    pkg install -y clang libzmq
  fi
  
  PYTHON_BIN="python"
  PIP_BIN="pip"
  PIP_EXTRA_FLAGS="--break-system-packages"
else
  # Standard Linux / macOS: Setup isolated venv to satisfy PEP-668
  echo ">>> [Environment] Standard POSIX detected. Provisioning isolated virtual environment..."
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required but not installed. Please install Python 3.10+."
    exit 1
  fi
  
  VENV_DIR="$SCRIPT_DIR/.omnios_venv"
  if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating .omnios_venv..."
    python3 -m venv "$VENV_DIR"
  fi
  
  PYTHON_BIN="$VENV_DIR/bin/python"
  PIP_BIN="$VENV_DIR/bin/pip"
  PIP_EXTRA_FLAGS=""
fi

# 2. Python Requirements
echo ">>> [Pip] Installing OmniSwarm dependencies..."
$PIP_BIN install -U pip $PIP_EXTRA_FLAGS || true
$PIP_BIN install -r requirements.txt $PIP_EXTRA_FLAGS
$PIP_BIN install -e . $PIP_EXTRA_FLAGS

# 3. Submodule / Branch Check
if [ ! -d "$SCRIPT_DIR/ComputeRes" ]; then
  echo ">>> [Submodule] Cloning ComputeRes (Execution Branch)..."
  git clone https://github.com/polymath-void/ComputeRes.git "$SCRIPT_DIR/ComputeRes" || echo "Note: ComputeRes clone skipped or already exists."
fi

# 4. Generate/Update Mesh Configuration
echo ">>> [MeshConfig] Writing local mesh configuration (mesh_config.json)..."
$PYTHON_BIN -c "
import json
config = {
    'node_id': '$NODE_ID',
    'role': '$ROLE',
    'hub_host': '$HUB_HOST',
    'rpc_port': int($HUB_PORT),
    'pub_port': 5566,
    'auto_tunnel': False,
    'tunnel_provider': 'bore'
}
with open('mesh_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('>>> mesh_config.json created successfully.')
"

# 4.5 Provision Permanent Antigravity System Rules
echo ">>> [System Rules] Provisioning permanent Antigravity system rules..."
$PYTHON_BIN scripts/inject_system_rules.py --role "$ROLE" --workspace "$SCRIPT_DIR" || true

# 5. Run Self-Verification Diagnostics
echo ">>> [Diagnostics] Running verification test suite..."
$PYTHON_BIN verify_install.py

echo ""
echo "======================================================================"
echo "          OmniSwarm-OS Installation & Configuration Complete!         "
echo "======================================================================"
if [ "$ROLE" == "hub" ]; then
  echo "To boot the Root Kernel Daemon on this machine:"
  if [ "$IS_TERMUX" = true ]; then
    echo "  python omniswarm_py/omniswarm_daemon.py"
  else
    echo "  $PYTHON_BIN omniswarm_py/omniswarm_daemon.py"
  fi
else
  echo "To execute a test skill against the Swarm:"
  if [ "$IS_TERMUX" = true ]; then
    echo "  python test_sys_cpu_info.py"
    echo "  python test_query_skills.py"
  else
    echo "  $PYTHON_BIN test_sys_cpu_info.py"
    echo "  $PYTHON_BIN test_query_skills.py"
  fi
fi
echo "======================================================================"
