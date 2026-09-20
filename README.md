# OmniOS (OmniSwarm Operating System)

OmniOS is a universal, decentralized Operating System designed exclusively for autonomous AI agents. Built on a ZeroMQ P2P Mesh, it provides stateful environment tracking, spatial codebase awareness, and multi-tenant execution sandboxes.

Instead of writing linear Bash scripts, agents operate as citizens within the OmniOS Matrix, routing intents through a robust Asynchronous Kernel.

## Core Architecture

OmniOS runs via a centralized root daemon (`omniswarm_daemon.py`) that manages three primary Kernel Branches:

1. **Cognition Branch (`polymath-nodeos`)**: Maintains a Holographic AST Graph of the entire codebase in an SQLite database, using eventual-consistency background threads to compute vector embeddings.
2. **Execution Branch (`ComputeRes`)**: A secure WASM / Bash execution sandbox capable of multiplexing asynchronous execution payloads (`compute_res_execute_bash`).
3. **Time Branch (`polymath-jage`)**: Native integration with the Jage AST version-control CLI, enabling agents to dynamically push spatial snapshots of the codebase.

### Event Ledger & ZeroMQ ROUTER
- **True Multi-Tenancy**: The Kernel utilizes a ZeroMQ `ROUTER` socket and Python `asyncio` subprocesses to prevent deadlocks and sustain hundreds of concurrent agent executions.
- **Durable Event Ledger**: Ephemeral `OS_EVENT` broadcasts (like `AST_SYNC_COMPLETE`) are permanently recorded in the `agy_nodeos.db` SQLite ledger. Agents can use the `query_os_events` mesh tool to catch up on missed network events after waking from hibernation.
- **Void-Governor**: A daemon loop that constantly monitors the Android Termux Low Memory Killer (LMK) pressure, orchestrating safe hibernation protocols when resources run low.

## Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/polymath-void/omniswarm-os.git
   cd omniswarm-os
   ```

2. **Boot the Root Kernel**
   ```bash
   # Run the daemon in the background to initialize the ZeroMQ Mesh
   nohup python3 omniswarm-py/omniswarm_daemon.py > omniswarm.log 2>&1 &
   ```

3. **Deploying Agents via CLI**
   Agents interact with the OS using the Native CLI wrapper:
   ```bash
   python3 omnios_cli.py <tool_name> '<json_args>'
   
   # Example: Query the AST
   python3 omnios_cli.py query_holographic_ast '{"intent": "FastAPI Router"}'
   
   # Example: Catch up on OS Events
   python3 omnios_cli.py query_os_events '{"since_timestamp": 0.0}'
   ```

## Creating Custom Agents

Use the provided `OmniOSAgentHarness` to build autonomous nodes in Python that communicate with the Kernel via ZeroMQ.

```python
import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def my_agent():
    async with OmniOSAgentHarness(agent_id="MyAgent") as harness:
        # Request the Execution Branch to run a command
        res = await harness.execute_in_swarm("compute_res_execute_bash", {"cmd": "echo Hello Matrix"})
        print(res)

asyncio.run(my_agent())
```
