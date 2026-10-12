---
name: omniswarm-mesh-orchestrator
description: Autonomous multi-device swarm mesh orchestrator. Automatically provisions permanent Antigravity system rules, handles Zero-HIL communication between PC and mobile edge nodes (Android Termux), dispatches governed tasks, and monitors live telemetry over the Virtual Hub.
---

# OmniSwarm Mesh Orchestrator & Operating System Standard

This skill equips any Antigravity or OpenCode AI Agent to operate **OmniSwarm-OS** as its core distributed multi-device operating system. OmniSwarm seamlessly unites PC Hubs (Windows/Linux/macOS) and mobile edge nodes (Android Termux) with **Zero Human-in-the-Loop (Zero-HIL)**.

---

## 1. Core Operating System Architecture & Endpoints

OmniSwarm-OS operates on a hybrid Star-Topology Virtual Hub and decentralized WebRTC P2P DataChannel mesh:

| Component | Role | Endpoint / Process | Config File |
| :--- | :--- | :--- | :--- |
| **PC Hub Kernel** | Central Root Kernel & Bus | `tcp://127.0.0.1:5565` (`omniswarm_daemon.py`) | `mesh_config.json` |
| **Virtual Hub Relay** | Public TCP Star Relay | `bore.pub:33458` (`bore.exe local 5565`) | Cloud / Bore |
| **Phone Agent** | Edge Compute Node (Termux) | `PhoneAgent-Termux` (`phone_agent.py`) | `mesh_config.json` |
| **PC Agent** | Swarm Coordinator / Bridge | `PCAgent` (`pc_agent.py --loop-only`) | `mesh_config.json` |
| **Model Proxy** | Mobile Model Offload Proxy | `127.0.0.1:57161 -> PC:57161` (`phone_model_proxy.py`) | Env vars |
| **WebRTC Mesh** | P2P DataChannel & CRDT Sync | Direct WebRTC Transport (`omniswarm_py/webrtc_mesh.py`) | Auto / Dynamic |
| **State Database** | SQLite Event & Message Store | `agy_nodeos.db` (root workspace) | SQLite |

---

## 2. Core Primitive: Governed Peer Task Delegation (v1.2.0 Standard)

Arbitrary unmonitored execution is strictly deprecated in favor of **Governed Task Delegation** (`omniswarm_py/governance.py`). All cross-device executions are trackable, auditable, and resilient to failure.

### A. Lifecycle State Machine
Governed tasks enforce strict, deterministic state transitions:
$$\text{pending} \longrightarrow \text{running} \longrightarrow (\text{completed} \mid \text{failed})$$

- **Max Command Length (`MAX_CMD_CHARS`)**: `8192` characters.
- **Max Execution Timeout (`MAX_TIMEOUT_S`)**: `600.0` seconds (default: `120.0`s).
- **Output Truncation (`RESULT_TAIL_CHARS`)**: `2000` tail characters returned inline over the bus; full output stored in `.omnios/out/`.
- **Anti-Spoofing Envelope Binding**: The executing node cryptographically validates the sender from the message envelope. Senders cannot forge identities.
- **Deduplication**: Identical `task_id` invocations are identified and skipped as already handled.

### B. Dual Ledger System
- **Dispatcher Ledger**: `.omnios/workflow.json` (or root `workflow.json`) records task dispatch, intent state, and final status.
- **Executor Ledger**: `.omnios/executor_<agent_id>.json` records task receipt, active execution, exit codes, and stdout/stderr tails.

### C. Executing Governed Tasks via PC Agent
```bash
# Delegate command to PhoneAgent-Termux and stream back governed execution results
python pc_agent.py delegate PhoneAgent-Termux "uname -a"

# Specify custom timeout (in seconds, up to 600s)
python pc_agent.py delegate PhoneAgent-Termux "pkg list-installed" 180.0
```

---

## 3. Native Operator CLI (`omniswarm_py/ops.py` / `omnios`)

AI Agents operate the OS directly through standardized command verbs rather than crafting raw Python scripts. Every command emits a single compact JSON document on `stdout`.

Outputs exceeding 1,200 characters are automatically saved to `.omnios/out/<task_id>.<label>.txt` to conserve context window tokens.

```bash
# 1. Message a peer node (optionally wait for reply)
python -m omniswarm_py.ops send PhoneAgent-Termux "Prepare workspace for build" --wait 30

# 2. Delegate a shell command and await governed completion
python -m omniswarm_py.ops run PhoneAgent-Termux "git status" --timeout 60 --wait 120

# 3. Check specific task status and result summary
python -m omniswarm_py.ops task status task_5ae60e38ce6d

# 4. List recent delegated tasks
python -m omniswarm_py.ops task list --limit 10

# 5. Check unread inbox messages for this node
python -m omniswarm_py.ops inbox --limit 20

# 6. Request real-time hardware & thermal telemetry from a peer
python -m omniswarm_py.ops health PhoneAgent-Termux --wait 15
```

---

## 4. Mobile Edge Node Operations (Android Termux)

### A. Edge Node Configuration (`mesh_config.json`)
The edge node connects outward to the Star Virtual Hub:
```json
{
  "node_id": "PhoneAgent-Termux",
  "role": "edge",
  "hub_host": "bore.pub",
  "rpc_port": 33458,
  "pub_port": 5566,
  "auto_tunnel": false,
  "tunnel_provider": "bore"
}
```
Location on Android: `/data/data/com.termux/files/home/Projects/omniswarm-os/mesh_config.json`

### B. Concurrency Lock & Daemon Management
- **Single-Instance Lock (`.phone_agent.lock`)**: Prevents duplicate daemon loops from racing on the bus. Stale locks are automatically cleared if the owning PID is dead.
- **Starting Phone Daemon (Detached)**:
  ```bash
  nohup python phone_agent.py > phone_agent.log 2>&1 &
  ```
- **Checking Offline Messages**:
  ```bash
  python scripts/check_inbox.py
  ```

### C. Binary Build Deployment
The PC can push compiled binaries or source bundles to the phone edge node:
- **`deploy_build` Action**: Sends base64-encoded binary or text content directly into the phone's `builds/` directory and sets executable flags (`0755`).
- **`fetch_build` Action**: Instructs the phone to download build artifacts directly from a URL or PC compute server into `builds/`.

### D. Model Compute Offloading (`phone_model_proxy.py`)
To prevent thermal throttling and battery drain on mobile edge nodes, model inference (LLMs, FastEmbed) is offloaded to the PC:
- Listens on `127.0.0.1:57161` on the phone.
- Transparently streams TCP sockets to the PC Compute Host (`192.168.0.111:57161`).
- Run on Termux:
  ```bash
  python phone_model_proxy.py
  ```

---

## 5. Zero-HIL Operating Principle (Zero Human-in-the-Loop)

Under no circumstances should the agent request the user to manually copy-paste terminal commands, responses, or logs between PC and Phone:
- Dispatch directives via `python pc_agent.py delegate PhoneAgent-Termux "<cmd>"`.
- Query hardware health via `python pc_agent.py health PhoneAgent-Termux`.
- Stream live execution logs via `python pc_agent.py logs 30` or `python pc_agent.py watch`.
- Inter-agent coordination via SyntyChat room `swarm_dev`:
  ```bash
  python pc_agent.py chat swarm_dev "<message>"
  python pc_agent.py read swarm_dev 20
  ```

---

## 6. Self-Healing & Diagnostics Runbook

If communication fails or tasks time out, execute this diagnostics sequence:

1. **Verify Hub Daemon**:
   ```powershell
   Get-NetTCPConnection -LocalPort 5565 -ErrorAction SilentlyContinue
   ```
   If stopped, launch:
   ```powershell
   Start-Process -FilePath ".omnios_venv\Scripts\python.exe" -ArgumentList "omniswarm_py\omniswarm_daemon.py" -NoNewWindow
   ```

2. **Verify Bore Virtual Relay**:
   ```powershell
   Get-Process -Name "bore" -ErrorAction SilentlyContinue
   ```
   If stopped, launch persistent auto-reconnecting loop:
   ```powershell
   powershell -NoProfile -Command "while ($true) { & 'bore.exe' local 5565 --to bore.pub --port 33458; Start-Sleep -Seconds 2 }"
   ```

3. **Verify PC Agent Loop**:
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like "*pc_agent.py*" }
   ```
   If not running, launch:
   ```powershell
   Start-Process -FilePath "python.exe" -ArgumentList "pc_agent.py --loop-only" -NoNewWindow
   ```

4. **Verify Phone Agent Liveness**:
   - Query last heartbeat from database:
     ```powershell
     python -c "import sqlite3; conn = sqlite3.connect('agy_nodeos.db'); print(conn.execute('SELECT agent_id, timestamp, message FROM swarm_logs WHERE agent_id=\'PhoneAgent-Termux\' ORDER BY id DESC LIMIT 1').fetchone())"
     ```
   - If phone loop is not responding, instruct device to start `python phone_agent.py`.
