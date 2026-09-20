import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def query_pc_skills():
    async with OmniOSAgentHarness(agent_id="PhoneAgent", host="192.168.0.112") as harness:
        print("🚀 Invoking the new Skills Router on the PC...")
        
        command_payload = {
            "query": "list_all"
        }
        
        # We use the newly registered 'query_skills' MCP tool
        result = await harness.execute_in_swarm("query_skills", command_payload)
        
        print("\n💻 Output returned from PC Execution Branch:")
        print(result)

if __name__ == "__main__":
    asyncio.run(query_pc_skills())
