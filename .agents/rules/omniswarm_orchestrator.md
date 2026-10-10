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
   - Use the native Swarm Bridge CLI (`pc_agent.py`) via `run_command`:
     - **Send Message / Query**:
       `python pc_agent.py send PhoneAgent-Termux "<message>"`
     - **Execute Shell Command on Phone (Termux)**:
       `python pc_agent.py exec PhoneAgent-Termux "<command>"`
     - **Query Phone Device Health & Battery**:
       `python pc_agent.py health PhoneAgent-Termux`
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
