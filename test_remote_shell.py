import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def remote_shell():
    async with OmniOSAgentHarness(agent_id="PhoneAgent") as harness:
        print("🚀 Sending remote command to PC...")
        
        # We are sending a system command to be executed natively on the PC
        # (This uses the Execution Branch of the PC's OmniOS Daemon)
        command_payload = {
            "cmd": "whoami && echo '---' && python -c \"import sys; print('PC Python Version:', sys.version)\""
        }
        
        result = await harness.execute_in_swarm("compute_res_execute_bash", command_payload)
        
        print("\n💻 Output returned from PC:")
        print(result)

if __name__ == "__main__":
    asyncio.run(remote_shell())
