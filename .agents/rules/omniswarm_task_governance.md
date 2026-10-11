---
trigger: always_on
---
# OmniSwarm Shared Task Governance Standard

Applies to every agent on every node (PC Hub, Android/Termux edge, or any peer) that delegates or executes work across devices.

1. **Delegation goes through the harness, not raw RPC:**
   - Delegate: `await harness.delegate_task(target, cmd, timeout_s)` or `python pc_agent.py delegate <target> "<cmd>"`.
   - Each delegated task gets a unique `task_id` and is recorded in the sender's `workflow.json` as `pending` before it is sent.

2. **Lifecycle (enforced in code, `omniswarm_py/governance.py`):**
   - `pending -> running -> completed | failed`. Any other transition is rejected.
   - The executing node records `running` before it starts the command, then `completed` or `failed` with the stdout/stderr tail and return code.
   - Results are sent back to the sender as a `task_result` message. The sender applies the result only if the message came from the node the task was assigned to.

3. **Execution guards (run on the executing node):**
   - The task sender is taken from the message envelope. A task cannot claim to come from someone else.
   - A task must target the local node. Duplicate `task_id`s are rejected.
   - Commands are capped at 8192 characters. Timeouts are capped at 600 seconds (default 120).
   - Arbitrary shell commands are allowed by design. Every command is logged to `ops_stream` and recorded in `workflow.json`, so it can be audited.

4. **Do NOT:**
   - Ask the human to copy results between devices. Use the message bus.
   - Edit another node's `workflow.json` by hand to change a task's status.
   - Re-send a task with the same `task_id`. Create a new task instead.
