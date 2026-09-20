import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def my_agent():
    # Pass the PC's IP address directly!
    async with OmniOSAgentHarness(agent_id="PhoneAgent", host="192.168.0.112") as harness:
        res = await harness.execute_in_swarm("ping_edge_node", {})
        print(res)

if __name__ == "__main__":
    asyncio.run(my_agent())
