import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def listen_to_swarm():
    async with OmniOSAgentHarness(agent_id="PhoneAgent", host="192.168.0.112") as harness:
        print("🎧 Phone Agent is now listening to all global PC events. (Press Ctrl+C to stop)")
        
        # Subscribe to the global PUB/SUB bus
        async for topic, message in harness.subscribe_to_events(""):
            print(f"\n[BROADCAST RECEIVED] Topic: {topic}")
            print(f"Payload: {message}")

if __name__ == "__main__":
    try:
        asyncio.run(listen_to_swarm())
    except KeyboardInterrupt:
        print("\nStopped listening.")
