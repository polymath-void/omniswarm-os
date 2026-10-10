import asyncio
from omniswarm_py.agent_harness import OmniOSAgentHarness

async def query_pc_brain():
    async with OmniOSAgentHarness(agent_id="PhoneAgent", host="100.77.91.63") as harness:
        print("🧠 Asking the PC's Cognition Branch a question...")
        
        # We are asking the PC to search its local Holographic AST SQLite database
        query_payload = {
            "intent": "How does the ZeroMQ router socket work?",
            "top_k": 2
        }
        
        result = await harness.execute_in_swarm("query_holographic_ast", query_payload)
        
        print("\n📚 PC Codebase Knowledge retrieved:")
        print(result)

if __name__ == "__main__":
    asyncio.run(query_pc_brain())
