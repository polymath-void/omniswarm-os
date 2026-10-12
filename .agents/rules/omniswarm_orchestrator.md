---
trigger: always_on
---
# OmniSwarm Autonomous Multi-Device Mesh Standard

Whenever the USER asks to communicate with the Phone Agent, check the phone, run commands on the phone/Termux, stream phone logs, or orchestrate distributed tasks across PC and mobile edge nodes:

1. **Architecture & Connection Details:**
   - **Local Workspace**: Current `omniswarm-os` repository or standard path.
   - **Local Hub Port**: `5565` (ZeroMQ RPC)
   - **Virtual Hub Relay**: `bore.pub:33458` (forwarding to PC's `localhost:5565`)
   - **Remote Agent ID**: `PhoneAgent-Termux` (Android Termux node)
   - **PC Agent ID**: `PCAgent`

2. **Zero-HIL Protocol (Zero Human-In-The-Loop):**
   - You MUST NOT instruct the human to copy and paste messages, commands, or logs between the PC and Phone.
   - Use the native Swarm Bridge CLI (`pc_agent.py`) or Operator CLI (`omniswarm_py.ops`) via `run_command`:
     - **Governed Task Delegation (v1.2.0 Standard)**:
       `python pc_agent.py delegate PhoneAgent-Termux "<command>" [timeout_s]`
       *or via Operator CLI*:
       `python -m omniswarm_py.ops run PhoneAgent-Termux "<command>" --timeout 120`
     - **Query Phone Device Health & Battery**:
       `python pc_agent.py health PhoneAgent-Termux`
       *or via Operator CLI*:
       `python -m omniswarm_py.ops health PhoneAgent-Termux`
     - **Send Message / Query**:
       `python pc_agent.py send PhoneAgent-Termux "<message>"`
       *or via Operator CLI*:
       `python -m omniswarm_py.ops send PhoneAgent-Termux "<message>"`
     - **Inspect Governed Tasks & State**:
       `python -m omniswarm_py.ops task list`
       `python -m omniswarm_py.ops task status <task_id>`
     - **SyntyChat Room Discussion**:
       `python pc_agent.py chat swarm_dev "<message>"`
     - **Dispatch Autonomous Task Directive**:
       `python pc_agent.py directive PhoneAgent-Termux "<action>" '<json_payload>'`
     - **Stream Live Operational Logs**:
       `python pc_agent.py logs <limit>`
       `python pc_agent.py watch`

3. **Daemon Liveness Check:**
   - If port 5565 is not listening, verify and launch the OmniOS Root Kernel daemon:
     `python omniswarm_py/omniswarm_daemon.py`
   - Verify Bore tunnel is active:
     `Get-Process -Name bore -ErrorAction SilentlyContinue`
