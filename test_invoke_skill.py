import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def run_cpu_info():
    async with OmniOSAgentHarness(agent_id="PhoneAgent") as harness:
        print("🚀 Requesting PC to execute: sys_cpu_info.py")
        
        # We send the request via the publish_skill tool which routes to skills_router.publish()
        command_payload = {
            "skill_name": "sys_cpu_info.py",
            "action": "execute"
        }
        
        result = await harness.execute_in_swarm("publish_skill", command_payload)
        
        print("\n💻 Output returned from PC:")
        print(result)

if __name__ == "__main__":
    asyncio.run(run_cpu_info())
