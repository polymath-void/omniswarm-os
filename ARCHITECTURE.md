# OmniOS: Technical Architecture Overview

This document provides a deep-dive technical overview of the internal mechanics, network topologies, and data flows of OmniOS.

## 1. The Micro-Kernel Paradigm
Unlike traditional monolithic AI frameworks, OmniOS is structured as an **Erlang/OTP-inspired Micro-Kernel**. The main Python process (`omniswarm_daemon.py`) acts solely as a supervisor. It does not execute tools itself; it manages the lifecycles, memory boundaries, and network sockets of its "Branches".

### System Fall Detector (Hot-Swapping)
OmniOS supports zero-downtime hot-swapping.
* **Mechanism:** When a branch (e.g., `NodeOS`) is mounted, the Kernel wraps the instantiation in the `SystemFallDetector`. 
* **State Checkpoints:** It caches the active memory state. If an update to `ComputeRes` or `polymath-nodeos` introduces an API break, the python `importlib.reload()` throws an exception.
* **Rollback:** The detector traps the `Exception` before it reaches the `asyncio` event loop, wipes the corrupted module from `sys.modules`, restores the cached checkpoint, and logs a `FATAL CRASH INTERCEPTED` alert, keeping the P2P mesh alive.

---

## 2. ZeroMQ Network Topology (The P2P Mesh)
OmniOS Abandons gRPC, HTTP, and REST in favor of raw **ZeroMQ (ZMQ)** TCP sockets. This provides C++ level speed with zero compilation overhead on Android.

### A. The Discovery Matrix (`PUB/SUB`)
* **Port:** `TCP 5566`
* **Flow:** Every OmniOS node broadcasts an `OMNI_DISCOVERY` JSON payload containing its `node_id`, randomly assigned RPC port, and available capabilities. 
* **State:** Nodes passively listen to this topic, silently building an internal decentralized map (`self.mesh_peers`) of all active devices on the local Wi-Fi.

### B. The RPC Execution Engine (`REQ/REP`)
* **Port:** Ephemeral (Randomly assigned on boot).
* **Flow:** When an Agent on Device A wants to execute a bash command on Device B, Device A opens a `REQ` socket, connects directly to Device B's ephemeral port, and fires the payload. Device B executes the intent in its local `ComputeRes` sandbox and returns the `stdout` via the `REP` socket.

---

## 3. Branch Integration Mechanics

### Branch 1: Cognition (`polymath-nodeos`)
* **Interface:** Direct SQLite bindings.
* **Data Flow:** OmniOS natively connects to `agy_nodeos.db`. It runs a throttled `asyncio` background task that fetches rows where `vector_embedding IS NULL`, generates deterministic semantic hashes (or quantized vector embeddings), and writes them back. It exposes `query_holographic_ast` to the ZeroMQ mesh.

### Branch 2: Execution (`ComputeRes`)
* **Interface:** Shared Python memory space + ZMQ Routing.
* **Data Flow:** OmniOS dynamically adds the `ComputeRes` directory to `sys.path`. It directly instantiates the `HyperSwarmBroker` and `OracleMaster`. 
* **Wasmtime Sandboxing:** P2P commands received by OmniOS are routed natively into the `ComputeRes` ZeroMQ `ROUTER`, dropping them into the local Agent task queue where they are executed inside secure WebAssembly sandboxes with strict CPU Fuel limits.

### Branch 3: Time (`polymath-jage`)
* **Interface:** Node.js IPC (Inter-Process Communication) Bridge.
* **Data Flow:** Because `jage` is written in Javascript, OmniOS uses `asyncio.create_subprocess_shell` to spawn a persistent V8/Node.js thread. It communicates with this thread purely through `stdin` and `stdout` streams, commanding it to execute semantic AST versioning natively.

---

## 4. Hardware Safety (The Void-Governor)
To survive on edge devices like Android phones, OmniOS employs a hardware-level safety watcher.

* **Polling:** The Governor operates a background async loop.
* **Linux/Android:** It opens and reads `/proc/meminfo` (specifically `MemAvailable`), entirely bypassing Python overhead to read directly from the kernel ring.
* **Intervention:** If RAM drops below 10%, it issues a `SIGSTOP` equivalent to the current agent. It takes the agent's exact variables, JSON serializes them, and dumps them into `workflow.json` with the status `suspended_by_governor`, preventing an Android LMK crash.

---

## 5. The Agent Harness (External Interfacing)
The `OmniOSAgentHarness` is the SDK that connects external LLMs to the OS.

* **Context Window Optimization:** It includes an **Intent Garbage Collector**. The Kernel intercepts `trigger_intent_gc` commands from the harness and performs an atomic `.tmp` file swap on `workflow.json`, deleting completed tasks to prevent JSON bloat.
* **LLM Schema Injection:** The harness dynamically reads the OS capabilities and formats them strictly to OpenAI/Anthropic `tools[]` JSON specifications, allowing any LLM to natively understand and utilize the OS mesh.
