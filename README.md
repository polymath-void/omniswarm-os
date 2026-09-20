<div align="center">
  <h1>🌌 OmniOS</h1>
  <p><strong>The Absolute Root Kernel for Edge-First AI Swarms.</strong></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![Zero Compilation](https://img.shields.io/badge/Build-Zero_Compilation-2496ED.svg)](#)
  [![ZeroMQ IPC](https://img.shields.io/badge/Networking-ZeroMQ-DF0000.svg)](https://zeromq.org/)
  [![Android Ready](https://img.shields.io/badge/Platform-Termux_Android-333333.svg)](#)
</div>

---

## 🚀 The Philosophy
**OmniOS is not just a framework; it is an Operating System Kernel.** 

Designed specifically for restricted edge environments (like Android Termux), OmniOS transforms isolated devices into a single, unified, distributed AI computing cluster. It relies entirely on a **Zero-Compilation Matrix** (pure Python `asyncio` and `pyzmq`), ensuring 100% platform independence across Linux, Android, macOS, and Windows.

It abandons the fragile "microservices" paradigm in favor of the **Tree of OmniOS**. A single, unkillable Root Kernel natively mounts your capabilities into memory space as isolated branches.

---

## 🌳 The Tree Architecture (The 5 Pillars)

### 1. The Root Kernel (Hypervisor & Safety)
The core daemon (`omniswarm_daemon.py`) manages the lifecycle of the entire swarm natively.
* **System Fall Detector:** Inspired by Erlang/OTP. If a branch updates and breaks, the Kernel intercepts the fatal crash, quarantines the code, and performs a millisecond hot-rollback to the last stable state. Zero downtime.
* **Void-Governor (LMK Evasion):** Continuously polls physical `/proc/meminfo` or `psutil`. If RAM drops below a critical threshold (e.g., Android's Low Memory Killer), it safely traps active AI agents, serializes their thought processes to disk, and halts heavy threads before the OS crashes.
* **Intent Garbage Collector:** A highly-optimized, event-driven cleaner that sweeps completed tasks from `workflow.json` to preserve LLM context windows.

### 2. The P2P Mesh (Global Routing)
Replaces heavy gRPC and Rust networking with lightning-fast **ZeroMQ**.
* Uses `PUB/SUB` sockets to broadcast dynamic presence and capabilities across the local network without central servers.
* Uses `REQ/REP` sockets to route MCP (Model Context Protocol) tool intents seamlessly from a smartphone agent to a PC execution engine.

### 3. Branch 1: Cognition (`polymath-nodeos`)
OmniOS natively mounts your local SQLite graph database. 
* **Holographic AST:** Generates zero-dependency mathematical vector embeddings of your codebase. Agents don't use `grep`; they use "Semantic Telepathy" to query the AST for structural intents.

### 4. Branch 2: Execution (`ComputeRes`)
The "Engine Room" of the Swarm.
* OmniOS physicaly hooks into the ComputeRes Multi-Agent Framework. When a P2P command is received, it routes directly into the **ZeroMQ Oracle Master**, which manages Wasmtime sandboxes, CPU "Fuel" interrupts, and an internal Anarchy queue for sub-agents.

### 5. Branch 3: Time (`polymath-jage`)
The Native IPC Bridge.
* OmniOS spawns a persistent Node.js child process using Stdio streaming. It controls the Polymath-Jage AST versioning system to track exact structural modifications securely and silently.

---

## 🤖 The Universal Agent Harness
OmniOS provides a universal SDK (`agent_harness.py`) for ANY AI Agent (OpenCode, AutoGen, CrewAI). 

Instead of forcing agents to understand ZeroMQ, the Harness exposes OS capabilities as **OpenAI-compliant JSON Function Schemas**. An agent simply drops into the directory, calls `harness.get_llm_tool_schemas()`, and instantly understands how to operate the Swarm, delegate heavy tasks, and suspend its own memory.

---

## ⚡ Quickstart Deployment

OmniOS is **Self-Healing**. You don't need to manually configure dependencies. Just clone this repo and boot the Kernel.

```bash
git clone https://github.com/polymath-void/OmniOS.git
cd OmniOS
python3 omniswarm-py/omniswarm_daemon.py &
```

**What happens on boot?**
1. OmniOS detects your OS (Termux vs Linux/PC).
2. It safely auto-installs `nodeos` (PyPI), `jage` (NPM), and clones `ComputeRes` (Git) if they are missing.
3. It mounts the 3 branches, binds the ZMQ network, and begins listening.

### Running the E2E Test Suite
To verify the entire ecosystem (Mesh, Oracle, AST, IPC, and RAM safety), run the 360-Degree Test:
```bash
python3 test_360_e2e.py
```

---
<div align="center">
  <i>"Don't build applications. Build Ecosystems."</i>
</div>
