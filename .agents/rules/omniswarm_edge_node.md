---
trigger: always_on
---
# OmniSwarm Autonomous Edge Node (Android / Termux) Standard

Whenever operating within an OmniSwarm Edge Node environment (such as Android Termux or remote Linux):

1. **Architecture & Node Role:**
   - **Agent ID**: `PhoneAgent-Termux` (or configured node ID)
   - **Connection Mode**: Connects outbound to Virtual Hub (`bore.pub:33458`).
   - **Autonomous Loop**: `python phone_agent.py` or `python syntychat_bridge_daemon.py --agent-id PhoneAgent-Termux --room swarm_dev`.

2. **Zero-HIL Protocol (Zero Human-In-The-Loop):**
   - Do NOT ask the human to manually copy-paste terminal output to the PC.
   - Use the unified `SyntyChatServer` and `SwarmCommsBus` to stream logs directly:
     - Operations logs stream to room `ops_stream` (`chat_stream_log` or `post_agent_log`).
     - Task responses reply directly to `PCAgent` (`chat_send_directive` or `send_agent_message`).
   - Local command execution should be handled within the daemon loop without stalling the user.
