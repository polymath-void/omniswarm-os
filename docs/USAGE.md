# OmniSwarm-OS: Practical Usage Guide

If you are wondering, *"Okay, but how do I actually use this?"*, this guide breaks down the practical workflow for both human developers and AI agents.

## 1. Booting the Hyper-Daemon
OmniSwarm-OS is meant to run entirely in the background, exactly like `polymath-nodeos`.

Whenever you start a Termux session on your Android device (or your PC), you boot the daemon:
```bash
python3 ~/Projects/omniswarm-os/omniswarm_py/omniswarm_daemon.py &
```
Once booted, the device becomes a "Node" in your local P2P Mesh. If you boot it on your phone and your tablet, they instantly discover each other via mDNS.

## 2. How the AI Agent Uses It
The real magic happens when you use OpenCode or Antigravity CLI. Because we injected `.agents/skills/omniswarm/SKILL.md`, your AI agents now possess a "Swarm Mindset".

### Scenario A: Semantic Code Search (Holographic AST)
Normally, an agent uses `grep` or `rg` to find code. With OmniSwarm-OS, it uses "Semantic Telepathy".
- **User Request:** *"Find the logic where we handle file uploads."*
- **Agent Action:** The agent doesn't scan the disk. Instead, it queries the local Mesh Broker via MCP: `mesh.execute_tool("query_holographic_ast", {"intent": "file upload handling"})`.
- **Result:** The graph returns mathematically matched AST nodes (`FileBrowserFragment.kt`, `api.ts`), even if the words "file" or "upload" aren't explicitly written in the variable names.

### Scenario B: Delegating Compute (The MCP Mesh)
- **User Request:** *"Compile this heavy Rust project."*
- **Agent Action:** The agent checks the **Void-Governor** and sees that Termux only has 15% RAM available. It knows compiling Rust will cause Android to kill the process (LMK).
- **Agent Mesh Query:** The agent asks the Mesh: *"Does anyone have heavy compute?"*
- **Delegation:** The Mesh Broker discovers that your PC (Node B) is on the network. The Termux agent forwards the compilation command to your PC via the P2P Mesh, waits for the compiled `.so` file to be returned, and continues operating safely on Android.

### Scenario C: Surviving the Android LMK (Void-Governor)
If an agent accidentally starts a massive `fd` directory scan that consumes too much memory:
1. The **Void-Governor** daemon detects RAM dropping below 10%.
2. It immediately halts the `fd` command.
3. It takes the agent's current "Thought Process" and saves it as a JSON payload in `workflow.json` with the status `suspended_by_governor`.
4. Your Android device survives without crashing. Later, when memory is freed up (or a stronger device joins the mesh), the swarm reads `workflow.json` and finishes the search automatically.

## Summary
You don't actively "type" into OmniSwarm. You run it in the background, and it acts as an invisible network protocol that makes your Antigravity AI agents infinitely smarter, distributed, and immune to Android memory crashes.

## Platform Compatibility
OmniSwarm-OS is 100% platform-independent.

*   **Linux:** Fully native. The Void-Governor reads `/proc/meminfo` seamlessly without extra dependencies.
*   **Android (Termux):** Fully native. The auto-installer knows how to bypass Android's PEP 668 restrictions safely using `--break-system-packages`.
*   **Windows / macOS:** Fully supported. The Void-Governor dynamically falls back to `psutil` or an unmonitored safe-mode to prevent crashes, while the Python mDNS mesh works flawlessly.
