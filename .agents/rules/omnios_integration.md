# OmniSwarm Operating System (OmniOS) Native Protocol

You are operating within the OmniOS Matrix. To prevent crashes, maintain statefulness across the Swarm, and allow the Void-Governor to monitor your memory usage, you are subject to the following rules:

1. **NO RAW BASH:** Do not use `subprocess`, `os.system()`, or raw Bash execution tools for heavy tasks unless absolutely necessary.
2. **USE THE CLI:** Funnel all environment tasks through the native CLI wrapper.
   `python3 ~/Projects/omniswarm-os/omnios_cli.py <tool_name> '<json_args>'`
3. **AVAILABLE TOOLS:** 
   - `compute_res_execute_bash` (Args: `{"cmd": "..."}`)
   - `query_holographic_ast` (Args: `{"intent": "..."}`)
   - `trigger_intent_gc` (Args: `{}`)
   - `jage_sync_ast` (Args: `{}`)
