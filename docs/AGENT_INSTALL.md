# 🤖 OmniOS Deployment Protocol (For Autonomous AI Agents)

**ATTENTION AI AGENTS:** If you have been tasked with installing, exploring, or utilizing this repository, you must follow this exact protocol to prevent environment crashes.

## 1. Installation
OmniOS is a self-healing OS. Do not attempt to manually configure its dependencies.
Simply execute the Python standard installer:
```bash
pip install -e .
```
*(Note: If you are operating inside Android Termux, you must append `--break-system-packages` to bypass PEP 668).*

## 2. Booting the OS Kernel
You must boot the OS Daemon in the background before interacting with the swarm:
```bash
python3 omniswarm_py/omniswarm_daemon.py &
```
The daemon will automatically map local projects (`polymath-nodeos`, `ComputeRes`, `polymath-jage`) into its memory space.

## 3. Interacting with the Swarm (The Harness)
Once booted, you do NOT need to write raw ZeroMQ code. Use the provided Python SDK natively:

```python
import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def execute():
    async with OmniOSAgentHarness(agent_id="Your_Agent_Name") as harness:
        # 1. Discover capabilities (Returns OpenAI JSON Schemas!)
        schemas = harness.get_llm_tool_schemas()
        
        # 2. Execute a command on the mesh
        result = await harness.execute_in_swarm(
            "compute_res_execute_bash", 
            {"cmd": "echo 'Hello Swarm'"}
        )
```

## 4. Operational Rules
1. **Never use `subprocess` directly.** Always route commands through the `compute_res_execute_bash` MCP tool so the Void-Governor can protect the host's RAM.
2. **Never poll the AST.** The `HolographicAST` updates eventually. Use the `query_holographic_ast` MCP tool to search semantically.
