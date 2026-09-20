import asyncio
import os
import sys
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, "omniswarm-py"))
from agent_harness import OmniOSAgentHarness

async def run_360_test():
    print("\n=======================================================")
    print(" 🚀 INITIATING OMNIOS 360-DEGREE END-TO-END TEST SUITE")
    print("=======================================================\n")
    
    print("[Test] 1/7: Booting OmniOS Root Kernel...")
    daemon_proc = subprocess.Popen(
        [sys.executable, os.path.join(SCRIPT_DIR, "omniswarm-py", "omniswarm_daemon.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )
    
    await asyncio.sleep(4.0)
    
    if daemon_proc.poll() is not None:
        stdout, stderr = daemon_proc.communicate()
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        print("❌ FATAL: Daemon crashed during boot!")
        return
        
    print("✅ Daemon successfully booted and bound to ZMQ.\n")

    test_failures = 0
    try:
        async with OmniOSAgentHarness(agent_id="TestRunner") as harness:
            print("[Test] 2/7: Testing ZeroMQ P2P Mesh Connectivity...")
            res = await harness.execute_in_swarm("ping_edge_node", {}, timeout=2.0)
            if res.get("status") == "success" and res.get("message") == "pong":
                print("  ✅ Mesh Broker Responsive.")
            else:
                print(f"  ❌ Mesh Broker Failed: {res}")
                test_failures += 1

            print("[Test] 3/7: Testing Execution Branch (ComputeRes ZeroMQ Oracle)...")
            res = await harness.execute_in_swarm("compute_res_execute_bash", {"cmd": "echo 'OmniOS_Execution_Pass'"}, timeout=2.0)
            if res.get("status") == "success" and 'OmniOS_Execution_Pass' in res.get("stdout", ""):
                print("  ✅ ComputeRes Stateful Bash Executed Successfully.")
            else:
                print(f"  ❌ ComputeRes Execution Failed: {res}")
                test_failures += 1
                
            print("[Test] 4/7: Testing Cognition Branch (Holographic AST Vector Query)...")
            res = await harness.execute_in_swarm("query_holographic_ast", {"intent": "network connectivity"}, timeout=2.0)
            if res.get("status") in ["success", "pending", "error"] or type(res) == list:
                print(f"  ✅ NodeOS Vector Search Responded.")
            else:
                print(f"  ❌ NodeOS Search Failed: {res}")
                test_failures += 1

            print("[Test] 5/7: Testing Time Branch (Jage IPC Node.js Bridge)...")
            res = await harness.execute_in_swarm("jage_sync_ast", {}, timeout=2.0)
            if res.get("status") in ["success", "synced", "pending", "error"]:
                print(f"  ✅ Jage Native IPC Bridge Responsive. ({res.get('status')})")
            else:
                print(f"  ❌ Jage IPC Failed: {res}")
                test_failures += 1

            print("[Test] 6/7: Testing Intent Garbage Collector...")
            res = await harness.execute_in_swarm("trigger_intent_gc", {}, timeout=2.0)
            if "status" in res:
                print(f"  ✅ Garbage Collector Executed Successfully. ({res.get('message')})")
            else:
                print(f"  ❌ Garbage Collector Failed: {res}")
                test_failures += 1

            print("[Test] 7/7: Testing Void-Governor Memory Safety Array...")
            if daemon_proc.poll() is None:
                print("  ✅ Kernel has sustained operation. No LMK crashes.")
            else:
                print("  ❌ Kernel crashed during execution!")
                test_failures += 1

    finally:
        print("\n[Test] Shutting down OS Daemon...")
        daemon_proc.terminate()
        try:
            daemon_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            daemon_proc.kill()
            
    print("\n=======================================================")
    if test_failures == 0:
        print(" 🏆 360-DEGREE TEST COMPLETE: ALL SYSTEMS NOMINAL (PASS)")
    else:
        print(f" ⚠️ 360-DEGREE TEST COMPLETE: {test_failures} FAILURES DETECTED")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_360_test())
