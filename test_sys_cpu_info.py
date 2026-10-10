import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def run_and_listen():
    async with OmniOSAgentHarness(agent_id="PhoneAgent") as harness:
        print("🎧 Subscribing to PC event mesh to catch the output...")
        
        print("🚀 Executing sys_cpu_info.py on the PC...")
        command_payload = {
            "skill_name": "sys_cpu_info.py",
            "action": "execute",
            "target_node": "omniswarm_daemon"
        }
        
        result = await harness.execute_in_swarm("publish_skill", command_payload)
        print("\n[PC SKILL RESPONSE RECEIVED]")
        print("💻 Routing Status:", result['message'])
        if 'stdout' in result:
            print("Output:", result['stdout'])

if __name__ == "__main__":
    asyncio.run(run_and_listen())
