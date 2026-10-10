# OmniOS (OmniSwarm Operating System)

OmniOS is a universal, decentralized Operating System designed exclusively for autonomous AI agents. Built on a ZeroMQ P2P Mesh and Virtual Cloud Hub topology, it provides stateful environment tracking, spatial codebase awareness, cross-platform execution sandboxes, and distributed multi-device swarm collaboration.

Instead of writing linear Bash scripts, agents operate as citizens within the OmniOS Matrix, routing intents through a robust Asynchronous Kernel across Windows, Linux, macOS, and Android (Termux).

---

## Universal Turnkey Installation (Any Device)

### 1. Android Termux, Linux & macOS
Run the universal POSIX installer:
```bash
# Clone the repository
git clone https://github.com/polymath-void/omniswarm-os.git
cd omniswarm-os

# Run the installer (auto-provisions venv / Termux libraries)
bash install.sh

# Or join an existing Swarm via Virtual Hub:
bash install.sh --role edge --hub-host bore.pub --hub-port 33458
```

### 2. Windows 10/11
Run the turnkey PowerShell installer or double-click `install.bat`:
```powershell
# In PowerShell:
.\install.ps1 -Role Hub

# Or join as an Edge agent:
.\install.ps1 -Role Edge -HubHost "bore.pub" -HubPort 33458
```

### 3. Run Self-Diagnostics
Verify all dependencies, sockets, and branch registries across any platform:
```bash
python verify_install.py
```

---

## Dynamic Mesh Configuration (`mesh_config.json`)

Devices discover the Swarm topology through `mesh_config.json` or environment variables (`OMNIOS_HUB_HOST`, `OMNIOS_HUB_PORT`, `OMNIOS_ROLE`):
```json
{
  "node_id": "PhoneAgent-01",
  "role": "edge",
  "hub_host": "bore.pub",
  "rpc_port": 33458,
  "pub_port": 5566,
  "auto_tunnel": false,
  "tunnel_provider": "bore"
}
```

Agents using `OmniOSAgentHarness` automatically connect without needing hardcoded IP addresses!

---

## Core Architecture

OmniOS runs via a centralized root daemon (`omniswarm_daemon.py`) that manages three primary Kernel Branches:

1. **Cognition Branch (`polymath-nodeos`)**: Maintains a Holographic AST Graph of the entire codebase in an SQLite database, using eventual-consistency background threads to compute vector embeddings.
2. **Execution Branch (`ComputeRes`)**: A secure execution sandbox capable of multiplexing asynchronous execution payloads (`compute_res_execute_bash`) and executing 140+ registered swarm skills.
3. **Time Branch (`polymath-jage`)**: Native integration with the Jage AST version-control CLI, enabling agents to dynamically push spatial snapshots of the codebase.

### Event Ledger & ZeroMQ ROUTER
- **True Multi-Tenancy**: The Kernel utilizes a ZeroMQ `ROUTER` socket and Python `asyncio` subprocesses to prevent deadlocks and sustain hundreds of concurrent agent executions.
- **Durable Event Ledger**: Ephemeral `OS_EVENT` broadcasts (like `AST_SYNC_COMPLETE`) are permanently recorded in the `agy_nodeos.db` SQLite ledger.
- **Virtual Cloud Hub Topology**: Built-in support for `bore.pub` or Tailscale overlay networking to bridge across firewalls and router AP isolation.
- **Void-Governor**: A daemon loop that constantly monitors memory pressure, orchestrating safe hibernation protocols when resources run low on mobile devices.

---

## Quickstart: Creating Custom Swarm Agents

```python
import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def my_agent():
    # Automatically reads mesh_config.json from any device
    async with OmniOSAgentHarness(agent_id="MyAgent") as harness:
        # 1. Query the 140+ swarm skills available across devices
        skills = await harness.execute_in_swarm("query_skills", {"query": "all"})
        print("Available Skills:", len(skills.get("skills_found", [])))

        # 2. Execute a command on the remote Hub execution branch
        res = await harness.execute_in_swarm("compute_res_execute_bash", {"cmd": "echo Hello Swarm"})
        print("Execution Result:", res)

asyncio.run(my_agent())
```
