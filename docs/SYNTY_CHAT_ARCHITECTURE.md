# SyntyChat Zero-HIL Swarm Architecture

## 1. Overview & Motivation
In standard agent development across distributed devices (e.g. PC and Mobile Termux), developers often find themselves trapped in a **Human-In-The-Loop (HIL) bottleneck**: copying terminal output from one agent and pasting it as a prompt into another agent.

**SyntyChatServer** (originally designed via `syntycode.sdk` as a zero-syntax AST room-and-client model) has been integrated directly into the core `OmniSwarm-OS` codebase to eliminate this bottleneck completely. It establishes an autonomous, bi-directional, event-driven message bus and log stream between all participating Swarm Agents.

```
+-----------------------------------------------------------------------------------+
|                            Virtual Hub (bore.pub / Local Mesh)                    |
+-----------------------------------------------------------------------------------+
                                    ^               ^
                                    | ZMQ RPC/PUB   | ZMQ RPC/PUB
                                    v               v
+-----------------------------------------+   +-------------------------------------+
|        PC Agent (Kernel / Hub)          |   |     Phone Agent (Edge / Termux)     |
| - SyntyChatServer Core                  |   | - SyntySwarmBridge Client           |
| - Room: 'swarm_dev' (Directives)        |<->| - Room: 'swarm_dev' (Directives)    |
| - Room: 'ops_stream' (Live Logs)        |   | - Room: 'ops_stream' (Live Logs)    |
| - Autonomous Directive Handlers         |   | - Autonomous Directive Handlers     |
+-----------------------------------------+   +-------------------------------------+
```

---

## 2. Core Architecture Components

### A. The Core Engine (`omniswarm_py/synty_chat.py`)
Directly adapted from the `SyntyChatServer` pattern:
- **`SyntyClient`**: Represents an connected agent or monitor with an asynchronous message queue.
- **`SyntyRoom`**: Manages isolated multi-agent communication channels with in-memory ring buffering and persistent disk logging (`synty_chat_ledger.jsonl`).
- **`SyntyChatServer`**: The room registry and dispatcher. Default core channels include:
  - `swarm_dev`: Inter-agent operational discussion and state coordination.
  - `ops_stream`: Real-time streaming of stdout/stderr, compilation logs, and diagnostics.
  - `autonomous_hil`: Structured task directives (`TASK_DIRECTIVE`) and automated task results (`TASK_RESULT`).

### B. The Swarm Network Bridge (`omniswarm_py/synty_bridge.py`)
- Hooks into `MCPMeshBroker` and `OmniOSAgentHarness`.
- Exposes three network RPC tools:
  - `synty_chat_post`: Broadcasts a message or log to a room.
  - `synty_chat_read`: Polls or retrieves recent messages since a given timestamp.
  - `synty_chat_rooms`: Lists all active rooms and participant counts.
- Broadcasts every message across the ZeroMQ PUB/SUB event mesh under topic `SYNTY_CHAT:<room_name>`.

### C. Autonomous Zero-HIL Bridge Daemon (`syntychat_bridge_daemon.py`)
Runs continuously as a background process on each device:
```bash
python syntychat_bridge_daemon.py --agent-id PCAgent --room swarm_dev
```
- Listens for incoming task directives.
- When a task (e.g. `verify_system_status`, `run_command`, `ast_query`) is received from another agent, it executes it natively without human intervention.
- Formats the execution output as a `TASK_RESULT` and posts it back into the room.

---

## 3. Quick Start Guide for Agents

### Step 1: Update & Restart Kernel
On the PC (Hub node):
```powershell
git pull
# Restart the OmniOS Daemon so kernel.py registers the new synty_chat tools
```

### Step 2: Running the Diagnostic Test
```bash
python test_synty_chat.py
```

### Step 3: Launching the Autonomous Zero-HIL Loop
On the PC:
```powershell
.omnios_venv\Scripts\python.exe syntychat_bridge_daemon.py --agent-id PCAgent --room swarm_dev
```

On Android (Termux):
```bash
python syntychat_bridge_daemon.py --agent-id PhoneAgent --room swarm_dev
```

Once running, both agents will stream their logs directly to each other and execute distributed workflows with zero manual copy-pasting!
