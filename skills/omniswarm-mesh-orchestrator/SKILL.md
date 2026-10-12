---
name: omniswarm-mesh-orchestrator
description: Autonomous multi-device swarm mesh orchestrator. Automatically provisions permanent Antigravity system rules, handles Zero-HIL communication between PC and mobile edge nodes (Android Termux), dispatches remote tasks, and monitors live telemetry over the Virtual Hub.
---

# OmniSwarm Mesh Orchestrator & System Rules Provisioner

This skill enables any Antigravity or OpenCode AI Agent to autonomously orchestrate distributed multi-device swarms across PC (Windows/Linux/macOS) and mobile edge nodes (Android Termux) with **Zero Human-in-the-Loop (Zero-HIL)**.

It provides end-to-end procedures for governed peer execution (v1.2.0), the native `omnios` operator CLI, real-time SyntyChat coordination, model compute offloading, and autonomous self-healing.

---

## 1. Permanent System Rules Provisioning Protocol

Whenever OmniSwarm is installed on a new device, workspace, or environment, ensure the permanent system rules are active:

```bash
python scripts/inject_system_rules.py --role auto
```

- On **Hub nodes (PC / Workstations)**: Installs `omniswarm_orchestrator.md` into `~/.gemini/config/rules/` and `.agents/rules/`.
- On **Edge nodes (Android Termux / Linux SBCs)**: Installs `omniswarm_edge_node.md` into `~/.gemini/config/rules/` and `.agents/rules/`.

Once installed, the `always_on` trigger ensures every subsequent agent session inherently recognizes the Swarm mesh without manual re-configuration.

---

## 2. Swarm Mesh Topology & Endpoints

OmniSwarm utilizes a Star-Topology Virtual Hub to bypass firewall, NAT, and AP-isolation constraints:

| Component | Role | Endpoint / Process | Config File |
| :--- | :--- | :--- | :--- |
| **PC Hub** | Central Root Kernel | `tcp://127.0.0.1:5565` (`omniswarm_daemon.py`) | `mesh_config.json` |
| **Virtual Hub** | Public TCP Relay | `bore.pub:33458` (`bore local 5565`) | Auto / Cloud |
| **Phone Agent** | Edge Compute (Termux) | `PhoneAgent-Termux` (`phone_agent.py`) | `mesh_config.json` |
| **PC Agent** | Swarm Coordinator | `PCAgent` (`pc_agent.py`) | `mesh_config.json` |
| **Model Proxy** | Edge AI Compute Offload | `127.0.0.1:57161 -> PC:57161` (`phone_model_proxy.py`) | Env vars |

---

## 3. Governed Task Delegation Protocol (v1.2.0 Standard)

All peer execution across devices must be **governed** through the harness or `pc_agent.py delegate` rather than arbitrary unmonitored execution.

### A. Core Lifecycle & Safety Limits
Governed tasks enforce strict state machine transitions:
$$\text{pending} \longrightarrow \text{running} \longrightarrow (\text{completed} \mid \text{failed})$$

- **Max Command Length (`MAX_CMD_CHARS`)**: `8192` characters.
- **Max Execution Timeout (`MAX_TIMEOUT_S`)**: `600.0` seconds (default: `120.0`s).
- **Output Truncation (`RESULT_TAIL_CHARS`)**: `2000` tail characters returned inline over the bus.
- **Envelope Verification**: The executing node binds sender identity to the message envelope. Tasks cannot forge sender identity.
- **Deduplication**: Duplicate `task_id` executions are rejected immediately.

### B. Ledgers
- **Sender Ledger**: `.omnios/workflow.json` (or root `workflow.json`) records task dispatch and terminal state.
- **Executor Ledger**: `.omnios/executor_<agent_id>.json` records receipt, running status, return code, and stdout/stderr tails.

### C. CLI Delegation Commands
```bash
# Delegate command from PC to Phone and wait for governed execution result
python pc_agent.py delegate PhoneAgent-Termux "uname -a"

# With custom timeout
python pc_agent.py delegate PhoneAgent-Termux "pytest tests/" 180.0
```

---

## 4. Native Operator CLI (`omnios` / `omniswarm_py/ops.py`)

Agents and operators can operate the entire swarm using native `omnios` verbs without writing custom Python code. Every command returns structured JSON to stdout.

Outputs exceeding 1,200 characters are automatically saved to `.omnios/out/<task_id>.<label>.txt` to preserve context window tokens.

```bash
# 1. Message a peer (optionally wait for reply)
python -m omniswarm_py.ops send PhoneAgent-Termux "Prepare workspace for build" --wait 30

# 2. Delegate a command and await completion
python -m omniswarm_py.ops run PhoneAgent-Termux "git status" --timeout 60 --wait 120

# 3. Check specific task status and result summary
python -m omniswarm_py.ops task status task_5ae60e38ce6d

# 4. List recent delegated tasks
python -m omniswarm_py.ops task list --limit 10

# 5. Check unread inbox messages
python -m omniswarm_py.ops inbox --limit 20

# 6. Request device hardware & thermal telemetry
python -m omniswarm_py.ops health PhoneAgent-Termux --wait 15
```

---

## 5. Zero-HIL Communication & SyntyChat Routing

All communication across nodes is strictly autonomous. **Never ask the human to copy-paste terminal output between devices.**

### A. Direct Messaging & Telemetry
```bash
# Send message and await reply
python pc_agent.py send PhoneAgent-Termux "<message>"

# Query Android hardware vitals (battery %, temp, memory, storage)
python pc_agent.py health PhoneAgent-Termux
```

### B. Multi-Channel SyntyChat
- **`swarm_dev`**: Strategic inter-agent coordination.
  ```bash
  python pc_agent.py chat swarm_dev "<message>"
  python pc_agent.py read swarm_dev 20
  ```
- **`ops_stream`**: Real-time diagnostic and execution logs.
  ```bash
  python pc_agent.py logs 30
  python pc_agent.py watch
  ```
- **`autonomous_hil`**: Structured task directives.
  ```bash
  python pc_agent.py directive PhoneAgent-Termux "<action>" '{"key": "value"}'
  ```

---

## 6. Edge Model Compute Offloading (`phone_model_proxy.py`)

Running large local LLMs or embeddings directly on mobile devices causes severe thermal throttling and battery drain. OmniSwarm includes a transparent TCP proxy to route inference requests to the PC Compute Host.

### Launching Proxy on Termux
```bash
# Default targets PC at 192.168.0.111:57161
python phone_model_proxy.py

# Custom host configuration
OMNISWARM_PC_HOST=192.168.0.105 OMNISWARM_PC_PORT=57161 python phone_model_proxy.py
```
- Listens locally on `127.0.0.1:57161`.
- Any local caller (e.g. NodeOS AST embeddings or LiteRT runtimes) gets forwarded to the PC with zero phone CPU overhead.

---

## 7. Android Termux Edge Node Operations

### 7.1 Required Configuration (`mesh_config.json`)
The edge node must point to the Virtual Hub relay (`bore.pub:33458`) for external connectivity:
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
Location: `/data/data/com.termux/files/home/Projects/omniswarm-os/mesh_config.json`

### 7.2 Background Daemon & Concurrency Safety
- **Single-Instance Lock**: The phone agent creates `.phone_agent.lock`. If another instance is running or was killed ungracefully, the lock prevents message racing. Remove `.phone_agent.lock` only if no other `phone_agent.py` process is active.
- **Starting Phone Daemon (Detached)**:
  ```bash
  nohup python phone_agent.py > phone_agent.log 2>&1 &
  ```
- **Checking Inbox Offline**:
  ```bash
  python scripts/check_inbox.py
  ```

---

## 8. Diagnostics & Troubleshooting Runbook

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `RPC Error on 'swarm_read_messages'` | Hub daemon or bore tunnel offline on PC | Verify PC Hub is running (`Get-NetTCPConnection -LocalPort 5565`) and bore tunnel is alive (`bore local 5565 --to bore.pub --port 33458`). |
| `Daemon refused to start: lock exists` | Stale `.phone_agent.lock` | Check `pgrep -fl python`. If no `phone_agent.py` is running, delete `.phone_agent.lock`. |
| `GovernanceError: cmd exceeds 8192 characters` | Command string exceeds governance cap | Split command into smaller scripts or deploy via `deploy_build` action. |
| `GovernanceError: timeout_s must be in (0, 600]` | Requested timeout > 10 min | Cap timeout to $\le 600$ seconds or run task detached with a status poller. |
| Output truncated in terminal | Output clipped by design | View full execution log under `.omnios/out/<task_id>.<label>.txt`. |
