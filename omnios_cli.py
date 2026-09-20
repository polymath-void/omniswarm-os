#!/usr/bin/env python3
import asyncio
import sys
import json
import os

# Safely resolve the correct absolute path to the module
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, "omniswarm-py"))

from agent_harness import OmniOSAgentHarness

async def execute_cli(tool_name, args_json):
    args = json.loads(args_json)
    async with OmniOSAgentHarness(agent_id="OmniOS-CLI") as harness:
        result = await harness.execute_in_swarm(tool_name, args, timeout=30.0)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ./omnios_cli.py <tool_name> '<json_args>'")
        sys.exit(1)
    
    tool = sys.argv[1]
    args_json = sys.argv[2]
    asyncio.run(execute_cli(tool, args_json))
