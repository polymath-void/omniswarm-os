import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def run_and_listen():
    async with OmniOSAgentHarness(agent_id="PhoneAgent", host="192.168.0.111") as harness:
        print("🎧 Subscribing to PC event mesh to catch the output...")
        
        # Start listening in the background
        async def listener():
            async for topic, message in harness.subscribe_to_events(""):
                if "cpu" in str(message).lower() or "sys_" in str(message).lower():
                    print(f"\n[PC SKILL RESPONSE RECEIVED] Topic: {topic}")
                    print(f"Data: {message}")
                    return True # Stop listening once we get it
        
        listener_task = asyncio.create_task(listener())
        
        # Wait a moment to ensure socket is bound
        await asyncio.sleep(1)
        
        print("🚀 Executing sys_cpu_info.py on the PC...")
        command_payload = {
            "skill_name": "sys_cpu_info.py",
            "action": "execute",
            "target_node": "omniswarm_daemon"
        }
        
        result = await harness.execute_in_swarm("publish_skill", command_payload)
        print("💻 Routing Status:", result['message'])
        
        # Wait for the response to hit the event bus (timeout 10s)
        try:
            await asyncio.wait_for(listener_task, timeout=10.0)
        except asyncio.TimeoutError:
            print("\n❌ Timed out waiting for PC to broadcast the CPU info.")

if __name__ == "__main__":
    asyncio.run(run_and_listen())
