# OmniOS: Complete Codebase & API Reference

This document provides an exhaustive map of the OmniOS source code, detailing every file, class, method, variable, and internal integration reference across the entire architecture.

---

## Directory Structure
```text
omniswarm-os/
├── omniswarm-py/
│   ├── omniswarm_daemon.py
│   ├── kernel.py
│   ├── mesh_broker.py
│   ├── void_governor.py
│   ├── fall_detector.py
│   ├── intent_gc.py
│   ├── holographic_ast.py
│   ├── agent_harness.py
│   └── branch_adapters/
│       ├── execution_branch.py
│       └── time_branch.py
├── examples/
│   ├── agent_llm_harness_example.py
│   └── pc_worker_simulation.py
├── README.md
├── ARCHITECTURE.md
└── CODEBASE_REFERENCE.md
```

---

## 1. Core Daemon & Kernel

### `omniswarm_daemon.py`
The entry point script that boots the Operating System.
* **Class `OmniOSDaemon`**
  * **Variables:**
    * `self.kernel`: Instance of `OmniOSRootKernel`.
    * `self.running`: Boolean controlling the infinite daemon loop.
  * **Methods:**
    * `_handle_suspend(self)`: Async callback passed to the Void-Governor. Triggers when RAM drops. Serializes state and gracefully terminates the `self.running` loop.
    * `run(self)`: Main `asyncio` entry loop. Boots the kernel, schedules the background governor task, and idles infinitely to keep the ZMQ network alive.

### `kernel.py`
The Micro-Kernel router that mounts branches and dynamically handles OS dependencies.
* **Class `OmniOSRootKernel`**
  * **Variables:**
    * `self.workspace_root`: Resolved dynamically via `os.getcwd()`.
    * `self.node_id`: Unique OS identifier tied to `os.getpid()`.
    * `self.mesh`: Instance of `MCPMeshBroker`.
    * `self.governor`: Instance of `VoidGovernor`.
    * `self.fall_detector`: Instance of `SystemFallDetector`.
    * `self.intent_gc`: Instance of `IntentGarbageCollector`.
    * `self.branches`: Dictionary mapping names (`"Cognition"`, `"Execution"`, `"Time"`) to their physical adapter instances.
  * **Methods:**
    * `_is_termux()`: Detects if running on Android (`PREFIX` contains `com.termux`).
    * `_run_cmd()`: Executes subprocess installation commands safely.
    * `_ensure_os_dependencies()`: Auto-installs `nodeos` via PyPI, `jage` via NPM, and clones `ComputeRes`.
    * `_mount_branches()`: Uses `SystemFallDetector` to safely instantiate code from `holographic_ast.py` and `branch_adapters/`.
    * `register_mesh_tools()`: Maps Branch functions (like `compute_res_execute_bash` and `trigger_intent_gc`) to the `self.mesh.local_tools` registry. Hooks the mesh network to route traffic into the branches natively.
    * `boot()`: The master bootloader. Triggers GC sweep, generates background AST vectors, boots ZeroMQ meshes, and returns the governor task.

---

## 2. Networking & Safety

### `mesh_broker.py`
The pure Python ZeroMQ implementation replacing gRPC and Rust libp2p.
* **Class `MCPMeshBroker`**
  * **Variables:**
    * `self.rpc_server`: ZMQ `REP` socket bound to a random ephemeral TCP port.
    * `self.discovery_pub`: ZMQ `PUB` socket bound to TCP `5566`.
    * `self.discovery_sub`: ZMQ `SUB` socket connecting to `5566`.
    * `self.local_tools`: Dictionary mapping tool names to JSON schemas.
    * `self.mesh_peers`: Dictionary tracking discovered network peers.
  * **Methods:**
    * `start_mdns_broadcast()`: Spawns the background tasks for discovery and RPC listening.
    * `_listen_for_rpc()`: Awaits incoming payloads, routes them to `handle_incoming_request()`, and sends back the result.
    * `_listen_for_discovery()`: Maps `OMNI_DISCOVERY` broadcasts to populate `self.mesh_peers`.
    * `handle_incoming_request()`: The execution router. Normally overridden by `kernel.py` to route directly into mounted branches.
    * `execute_remote_tool()`: Uses a ZMQ `REQ` socket to establish a TCP connection to a target peer's ephemeral port, fires JSON, and awaits a response.

### `void_governor.py`
Cross-platform RAM monitor enforcing hardware bounds.
* **Class `VoidGovernor`**
  * **Variables:**
    * `self.threshold`: Critical float boundary (e.g., `10.0%`).
    * `self.platform`: Results of `sys.platform`.
    * `self.has_psutil`: Boolean tracking if the C-extension is available.
  * **Methods:**
    * `_get_memory_stats()`: Dynamically reads either `psutil.virtual_memory()` or parses `/proc/meminfo` natively for Android/Linux compatibility.
    * `monitor_lmk_pressure()`: Infinite background loop yielding via `asyncio.sleep(1)`. Triggers the suspend callback if RAM falls below `self.threshold`.
    * `serialize_intent()`: Safely JSON dumps the active agent's state into `workflow.json`.

### `fall_detector.py`
Erlang-inspired crash supervisor.
* **Class `SystemFallDetector`**
  * **Variables:** `self.checkpoints` (Dict storing memory references to stable modules).
  * **Methods:**
    * `safe_mount(branch_name, mount_func)`: Wraps instantiation in a `try/except`. If `mount_func()` throws a fatal error, it catches it, prevents a Kernel crash, and rolls back to the cached instance in `self.checkpoints`.

### `intent_gc.py`
Event-driven cleanup utility to prevent LLM context bloating.
* **Class `IntentGarbageCollector`**
  * **Variables:** `self.workflow_path`
  * **Methods:**
    * `sweep_completed_intents()`: Reads `workflow.json`. Iterates the list. Discards any intent where `"status" == "completed"`. Writes back atomically using `.tmp` file swapping. Returns metrics on cleared counts.

---

## 3. Branches (The System Adapters)

### `holographic_ast.py` (Branch 1: Cognition)
* **Class `HolographicASTGraph`**
  * **Methods:**
    * `_generate_pseudo_embedding()`: Uses `hashlib.sha256` to create deterministic edge-optimized floats.
    * `_cosine_similarity()`: Mathematical vector distance calculator.
    * `generate_embeddings_background_task()`: Alters the SQLite `nodes` schema to add `vector_embedding`. Runs an infinite loop processing 10 nodes at a time with `asyncio.sleep(0.5)` yields to guarantee 0% CPU spiking.
    * `semantic_search()`: Performs in-memory dot-product clustering to return contextually linked AST nodes.

### `branch_adapters/execution_branch.py` (Branch 2: Execution)
* **Class `ComputeResExecutionBranch`**
  * **Variables:**
    * `self.ctx`: ZMQ Asyncio Context.
    * `self.broker`: Direct import of ComputeRes `HyperSwarmBroker`.
    * `self.oracle`: Direct import of ComputeRes `OracleMaster`.
  * **Methods:**
    * `__init__()`: Dynamically appends `ComputeRes` to `sys.path` to dodge absolute pathing issues.
    * `boot_branch()`: Spawns the native ComputeRes ZeroMQ loops on kernel threads.
    * `dispatch_intent()`: Creates a local ZMQ `DEALER` socket, connects to `tcp://127.0.0.1:5555`, and pushes P2P Mesh bash commands directly into the Wasmtime Oracle queue.

### `branch_adapters/time_branch.py` (Branch 3: Time)
* **Class `JageTimeBranch`**
  * **Variables:** `self.bin_path` (Path to `jage.js`).
  * **Methods:**
    * `version_ast_state()`: Uses `asyncio.create_subprocess_shell` to physically spawn the Node.js V8 engine and execute `node jage.js push` to freeze AST states to git natively.

---

## 4. The Agent Ecosystem

### `agent_harness.py`
The SDK allowing LLM models to interface with OmniOS without knowing python logic.
* **Class `OmniOSAgentHarness`**
  * **Features:** Implements `__aenter__` and `__aexit__` for clean Context Management (`async with`).
  * **Variables:** `self.req_socket`, `self.sub_socket`.
  * **Methods:**
    * `connect()` / `disconnect()`: Safely pools ZMQ sockets.
    * `get_llm_tool_schemas()`: Returns the OS capabilities rigidly formatted as OpenAI/Anthropic JSON Function schemas.
    * `execute_in_swarm()`: Executes a tool via the ZMQ Mesh. Features an `asyncio.wait_for` timeout wrap to handle dead edge nodes securely.
    * `suspend_intent_safely()`: Uses `asyncio.to_thread` and atomic `.tmp` renames to suspend the agent's memory to disk without blocking the main event loop.
    * `subscribe_to_events()`: Async Generator (`yield`) bound to the ZMQ `SUB` socket.
