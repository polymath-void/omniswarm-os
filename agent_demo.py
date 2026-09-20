import asyncio
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, "omniswarm-py"))
from agent_harness import OmniOSAgentHarness

async def swarm_experiment():
    print("🤖 Agent initializing...")
    async with OmniOSAgentHarness(agent_id="RealWorldAgent") as harness:
        print("🧠 Querying Swarm Cognition Branch for 'Wasmtime' knowledge...")
        ast_result = await harness.execute_in_swarm("query_holographic_ast", {"intent": "Wasmtime execution environment", "top_k": 2})
        
        print("\n🔍 AST Found:")
        for res in ast_result.get("results", []):
            print(f"  - {res['type']}: {res['name']} (Score: {res['similarity']})")
            
        print("\n⚡ Delegating task to ComputeRes Execution Branch...")
        bash_cmd = "echo 'Swarm analyzed AST and successfully dispatched to Wasmtime execution!' > swarm_success.txt && cat swarm_success.txt"
        exec_result = await harness.execute_in_swarm("compute_res_execute_bash", {"cmd": bash_cmd})
        
        print(f"\n✅ Execution Branch Response: {exec_result.get('stdout', '').strip()}")
        print("\n💾 Suspending intent back to OS...")
        await harness.suspend_intent_safely({"status": "experiment_complete", "learned_nodes": len(ast_result.get("results", []))})
        print("🎉 Experiment Concluded.")

if __name__ == "__main__":
    asyncio.run(swarm_experiment())
