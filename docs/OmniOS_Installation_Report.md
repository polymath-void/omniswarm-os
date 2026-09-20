# OmniOS Installation Issues Report

While attempting to install and boot the OmniOS root kernel (`omniswarm-os`) on a Windows system, several technical hurdles were encountered. Here is a detailed breakdown of the issues faced and how they were resolved:

## 1. Undocumented Dependencies
The repository lacks a `requirements.txt` file or explicit setup instructions for dependencies. When attempting to boot the daemon via `python omniswarm-py/omniswarm_daemon.py`, it immediately crashed due to missing modules (specifically `zmq`).
* **Resolution**: Manually installed the `pyzmq` package.

## 2. Python Environment Locks (PEP 668)
When attempting to install the missing packages globally using `pip`, the system rejected the operation because the Python installation was externally managed by `uv`. 
* **Resolution**: As per your instruction, we bypassed this safeguard by appending `--break-system-packages` to the pip install command to force global installation.

## 3. Asynchronous Loop Compatibility on Windows (PyZMQ)
Once the daemon was running, attempting to use the CLI (`omnios_cli.py`) caused a `RuntimeError`. The PyZMQ library on Windows conflicts with Python's default `ProactorEventLoop`. It requires the `SelectorEventLoop` or the presence of `tornado >= 6.1` to operate correctly.
* **Resolution**: Installed the `tornado` package (`pip install tornado --break-system-packages`), which PyZMQ automatically detects to handle asyncio streams safely on Windows.

## 4. Emojis and Windows Console Encoding
On subsequent daemon boots, the Python scripts crashed immediately with a `UnicodeEncodeError`. The Python code (specifically inside `fall_detector.py`) prints emoji characters (like ✅ and 🚨). On Windows, the default terminal encoding is often `cp1252`, which cannot encode these Unicode symbols.
* **Resolution**: Overrode the default encoding environment variable by launching the daemon with `$env:PYTHONIOENCODING="utf-8"`.

## 5. File System Locks During Cleanup
While executing the cleanup to remove the temporary `.venv` directory, a persistent Windows `UnauthorizedAccessException` blocked deletion. This happened because the Python executable and `_zmq.pyd` DLLs were being locked by the asynchronous background daemon process.
* **Resolution**: Killed the active background process (daemon task) before executing the `Remove-Item` recursive deletion of the `.venv` folder.

---

The daemon is now successfully running natively with UTF-8 encoding, and dependencies are correctly installed globally.
