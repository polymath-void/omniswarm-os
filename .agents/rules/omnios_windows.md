---
name: omnios_windows_quirks
description: Guidelines for interacting with OmniOS on Windows, resolving bootloader detachments, and ignoring expected PyZMQ warnings.
trigger: always_on
---

# OmniOS Windows & Python VENV Rules

When operating within the `omniswarm-os` repository on a Windows host, you MUST adhere to the following operational guidelines to prevent false failures and debugging loops:

1. **Bootloader Process Detachment (os.execv)**:
   - When running `python omniswarm-py/omniswarm_daemon.py` or `python omnios_cli.py` natively on Windows, the `bootloader.py` script automatically bootstraps an `.omnios_venv` to bypass `uv` and PEP-668 environment locks.
   - It then uses `os.execv()` to hand off execution to the virtual environment. **On Windows, this detaches the process** and instantly returns exit code 0 to the original terminal, swallowing all `stdout`/`stderr` from the child process.
   - **Do NOT assume the daemon crashed.** The daemon is running silently in the background as an orphaned process. 
   - **To see output natively and capture logs:** Execute scripts directly using the virtual environment binary: `.omnios_venv\Scripts\python.exe omniswarm-py\omniswarm_daemon.py` or `.omnios_venv\Scripts\python.exe omnios_cli.py <args>`.

2. **PyZMQ Tornado Warnings**:
   - When running the CLI or daemon directly from the `.omnios_venv`, you will see a `RuntimeWarning` from `zmq.asyncio` regarding the `Proactor event loop` missing the `add_reader` family of methods.
   - **Do NOT attempt to fix this.** This warning is expected and harmless. The underlying architecture dynamically registers a Tornado thread to safely bridge PyZMQ polling into the native Windows Proactor loop. `asyncio.WindowsSelectorEventLoopPolicy` must NOT be enabled, as it breaks native Wasmtime asynchronous subprocesses.

3. **SQLite Initialization (No Such Table)**:
   - If the daemon background embedding loop crashes with `sqlite3.OperationalError: no such table: nodes`, **do not panic**. 
   - This just means the AGY-NodeOS background watchdog hasn't completed its first workspace AST sweep to initialize the database schema. The main OmniOS ZeroMQ kernel remains fully functional.
