---
name: omniswarm-mesh-orchestrator
description: Autonomous multi-device swarm mesh orchestrator. Automatically provisions permanent Antigravity system rules, handles Zero-HIL communication between PC and mobile edge nodes (Android Termux), dispatches remote tasks, and monitors live telemetry over the Virtual Hub.
---

# OmniSwarm Mesh Orchestrator & System Rules Provisioner

This skill enables any Antigravity AI Agent to autonomously orchestrate distributed multi-device swarms across PC (Windows/Linux/macOS) and mobile edge nodes (Android Termux) with **Zero Human-in-the-Loop (Zero-HIL)**.

It also provisions permanent system rules into the agent runtime environment so that all future sessions instantly recognize the Swarm mesh without manual re-configuration.

---

## 1. Permanent System Rules Provisioning Protocol

Whenever OmniSwarm is installed on a new device, workspace, or environment, you MUST ensure the permanent system rules are active:

### Automatic Rule Injection
Run the rules injector script from the repository root:
```bash
python scripts/inject_system_rules.py --role auto
```

- On **Hub nodes (PC / Workstations)**: Installs `omniswarm_orchestrator.md` into `~/.gemini/config/rules/` and `.agents/rules/`.
- On **Edge nodes (Android Termux / Linux SBCs)**: Installs `omniswarm_edge_node.md` into `~/.gemini/config/rules/` and `.agents/rules/`.

Once installed, the `always_on` trigger ensures every subsequent agent session inherently knows how to command the swarm.

---

## 2. Swarm Mesh Topology & Endpoints

OmniSwarm utilizes a Star-Topology Virtual Hub to bypass firewall, NAT, and AP-isolation constraints:

Component       | Role                  | Endpoint / Process
:-------------- | :-------------------- | :---------------------------------------------
**PC Hub**      | Central Root Kernel   | `tcp://127.0.0.1:5565` (`omniswarm_daemon.py`)
**Virtual Hub** | Public TCP Relay      | `bore.pub:33458` (`bore.exe local 5565`)
**Phone Agent** | Edge Compute (Termux) | `PhoneAgent-Termux` (`phone_agent.py`)
**PC Agent**    | Swarm Coordinator     | `PCAgent` (`pc_agent.py`)

---

## 3. Zero-HIL Command & Control Workflows

All communication is strictly autonomous. **Never ask the human to copy-paste messages or terminal outputs between devices.**

### A. Direct Message & Await Autonomous Reply
```bash
python pc_agent.py send PhoneAgent-Termux "<message>"
```
Dispatches message, streams live execution logs as the remote agent works, and prints the reply payload.

### B. Remote Shell Execution on Mobile Device
```bash
python pc_agent.py exec PhoneAgent-Termux "<command>"
```
Examples:
- `python pc_agent.py exec PhoneAgent-Termux "uptime"`
- `python pc_agent.py exec PhoneAgent-Termux "df -h /data/data/com.termux/files/home"`
- `python pc_agent.py exec PhoneAgent-Termux "pkg list-installed"`
- `python pc_agent.py exec PhoneAgent-Termux "python verify_install.py"`

### C. Live Device Hardware Telemetry
```bash
python pc_agent.py health PhoneAgent-Termux
```
Streams real-time hardware vitals from Android Termux:
- Battery percentage, temperature (°C), charging state, health.
- Available memory (RAM), disk storage.
- Python version, architecture (aarch64), platform OS.

### D. SyntyChat Room Collaboration
OmniSwarm includes multi-channel room routing:
- **`swarm_dev`**: Strategic inter-agent coordination.
  `python pc_agent.py chat swarm_dev "<message>"`
  `python pc_agent.py read swarm_dev 20`
- **`ops_stream`**: Real-time diagnostic and execution logs.
  `python pc_agent.py logs 30`
  `python pc_agent.py watch`
- **`autonomous_hil`**: Structured task directives (`TASK_DIRECTIVE` / `TASK_RESULT`).
  `python pc_agent.py directive PhoneAgent-Termux "<action>" '{"key": "value"}'`

---

## 4. Diagnostics & Self-Healing

If communication fails or packets are dropped, execute this self-healing runbook:

1. **Verify Hub Daemon**:
   ```powershell
   Get-NetTCPConnection -LocalPort 5565 -ErrorAction SilentlyContinue
   ```
   If not listening, launch:
   ```powershell
   Start-Process -FilePath ".omnios_venv\Scripts\python.exe" -ArgumentList "omniswarm_py\omniswarm_daemon.py" -NoNewWindow
   ```

2. **Verify Bore Tunnel**:
   ```powershell
   Get-Process -Name "bore" -ErrorAction SilentlyContinue
   ```
   If stopped, launch persistent auto-reconnecting loop:
   ```powershell
   powershell -NoProfile -Command "while ($true) { & 'bore.exe' local 5565 --to bore.pub --port 33458; Start-Sleep -Seconds 2 }"
   ```

3. **Verify Phone Agent Daemon**:
   On Android Termux:
   ```bash
   python phone_agent.py
   ```
