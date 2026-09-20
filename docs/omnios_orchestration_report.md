# OmniOS Orchestration & Distributed Systems Report

This report documents the challenges, architectural behaviors, and engineering solutions discovered while building autonomous agents (`feature_agent.py` and `swarm_scraper.py`) that command the **OmniOS ZeroMQ Mesh** to modify external projects (like `PodPitch`).

---

## 1. The Daemon CWD Trap (Execution Branch)

### The Architecture
OmniOS operates via a centralized root kernel (`omniswarm_daemon.py`) that manages the ZeroMQ router. When an agent utilizes the `OmniOSAgentHarness` to send a `compute_res_execute_bash` payload, that payload is executed by the **Execution Branch** (`ComputeRes`).

### The Challenge
I created `feature_agent.py` inside `~/Projects/PodPitch` to dynamically inject an Analytics router into the FastAPI backend. However, because the root daemon was anchored at `~/Projects`, the Execution Branch evaluated the bash commands from the perspective of the daemon's CWD, not the agent's CWD. Commands like `cat > backend/app/routers/analytics.py` failed because the `backend/` directory did not exist at the umbrella root.

### The Engineering Solution
Agents must explicitly manage spatial awareness when dispatching execution payloads. I modified the payload to include explicit pathing (`cd PodPitch/backend`) before executing the file manipulations, ensuring the execution node navigated to the correct sector of the workspace before running the script.

---

## 2. Blind Payload Manipulation & AST Verification

### The Challenge
In a standard script, manipulating text strings is straightforward. In a decentralized swarm, sending a `sed` command across a network to an execution node is essentially "blind manipulation." When attempting to graft the analytics router into `main.py`, I initially assumed the import syntax was `from routers import auth`. In reality, the codebase used `from app.routers import auth`.

### The Engineering Solution
An execution node will silently fail or corrupt a file if the payload is misaligned with the physical code structure. Before dispatching blind string-manipulation payloads, an agent must either:
1. Visually read the file using standard read tools to confirm the structure.
2. Rely strictly on the **Cognition Branch** (AST Graph) to verify the exact string syntax of the node before instructing the Execution branch to modify it.

---

## 3. Eventual Consistency in SQLite Vector Embeddings (Cognition Branch)

### The Architecture
The **Cognition Branch** (`polymath-nodeos`) maps the workspace into an AST graph and uses an asynchronous background thread to calculate pseudo-vector embeddings for semantic search (processing 10 nodes every 0.5 seconds). This design intentionally throttles CPU usage to prevent triggering the Android Low Memory Killer (LMK).

### The Challenge
In the `SwarmScraper` pipeline, the agent followed this sequence:
1. Scrape a webpage & save to `.md` (Execution Branch).
2. Sync the codebase via `jage push` (Time Branch).
3. Immediately search the AST for the scraped data (Cognition Branch).

The Cognition Branch failed to return the newly scraped knowledge, instead returning vaguely related older nodes. The swarm was moving faster than the database! The agent queried the network before the background thread had finished assigning a vector embedding to the new markdown node.

### The Engineering Solution
In a distributed micro-kernel OS, state is **eventually consistent**, not instantly synchronous. To solve this, I introduced a slight asynchronous delay (`asyncio.sleep`) in the agent pipeline. For production-grade agents, the architecture should rely on a ZeroMQ broadcast event (e.g., `EMBEDDING_COMPLETE`) rather than synchronous polling, allowing the agent to suspend its intent and wake up only when the database is consistent.
