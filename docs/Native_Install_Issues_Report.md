# OmniOS Native Install: Root Cause & Issues Report

When attempting to perform a completely fresh, native clone and installation of `omniswarm-os` on a Windows environment, several architectural and environmental hurdles were encountered. 

Here is the exact timeline of issues and their root causes:

### 1. Missing Core Dependencies
* **Symptom:** `ModuleNotFoundError: No module named 'zmq'` during the first execution of `omniswarm_daemon.py`.
* **Root Cause:** The repository lacks a top-level `requirements.txt` or `pyproject.toml`. Because the OS doesn't use standard Python packaging, essential networking libraries like `pyzmq` had to be manually identified and installed by the user before the kernel could boot.

### 2. Global Python Environment Lock (PEP 668)
* **Symptom:** `error: externally-managed-environment` when running `pip install pyzmq`.
* **Root Cause:** The host machine manages its Python environments using `uv` (or a similar modern manager). Modern Python actively prevents `pip` from modifying global system packages to avoid bricking OS tools. We had to bypass this safety constraint manually by passing the `--break-system-packages` flag.

### 3. Asynchronous Loop Incompatibility (Windows)
* **Symptom:** `RuntimeError: Proactor event loop does not implement add_reader family of methods required for zmq`.
* **Root Cause:** On Windows, Python's `asyncio` defaults to the `ProactorEventLoop`. However, `pyzmq` relies on standard POSIX I/O stream selectors. When `omnios_cli.py` tried to open a ZeroMQ connection, it crashed.
* *Note: This was elegantly fixed in your latest commit by explicitly enforcing `asyncio.WindowsSelectorEventLoopPolicy()` at the top of the scripts, which prevents the need for installing `tornado` as a middleman.*

### 4. Console Encoding Crash (cp1252)
* **Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'`
* **Root Cause:** The OmniOS console outputs UI emojis (like ✅ and 🚨) to indicate system states. Native Windows terminals default to the `cp1252` character map, which cannot decode modern Unicode emojis, causing a fatal crash immediately upon booting the kernel.
* *Note: Also fixed in your latest commit via `sys.stdout.reconfigure(encoding='utf-8')`.*

### 5. Holographic AST Database Initialization
* **Symptom:** `sqlite3.OperationalError: no such table: nodes`
* **Root Cause:** The `generate_embeddings_background_task` inside the Cognition Branch expects to query the `nodes` table inside `agy_nodeos.db`. Because this was a completely fresh clone, the `.agents` hook hadn't triggered yet and the AGY-NodeOS background watchdog hadn't performed its first sweep of the repository to build the database schema. When SQLite connects to a missing `.db` file, it creates a blank file, causing the `SELECT` statement to fail. (Fortunately, this only crashes the background embedding task, not the main OS router loop).
