import asyncio
import sys
import os

# Safely resolve the correct absolute path to the module
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, "omniswarm-py"))

from agent_harness import OmniOSAgentHarness

async def mock_agent_lifecycle():
    print("=== AGENT HARNESS: LLM INTEGRATION TEST ===\n")
    
    # Advanced Context Manager usage
    async with OmniOSAgentHarness(agent_id="Agent-GPT4") as harness:
        
        # 1. Agent Understanding (Dynamic Tool Extraction)
        tools = harness.get_llm_tool_schemas()
        print("[Agent Logic] I discovered the following OS schemas:")
        for t in tools:
            print(f"  -> {t['function']['name']}: {t['function']['description']}")
            
        print("\n[Agent Logic] Injecting schemas into my LLM Context...")
        
        # 2. Optimized Execution
        print("\n[Agent Logic] Executing a remote tool via ZMQ Harness...")
        result = await harness.execute_in_swarm(
            tool_name="query_holographic_ast", 
            args={"intent": "User Authentication"},
            timeout=1.0
        )
        print(f"[Harness Response] {result}")
        
        # 3. Graceful Suspension
        print("\n[Agent Logic] Memory pressure detected. Yielding execution gracefully.")
        await harness.suspend_intent_safely({"current_file": "auth.py", "lines_read": 140})

if __name__ == "__main__":
    asyncio.run(mock_agent_lifecycle())
