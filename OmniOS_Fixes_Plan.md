# OmniOS Windows Architecture Refactor Plan

## Goal Description
The current "fix" for Windows compatibility (`WindowsSelectorEventLoopPolicy`) relies on a critical compromise: it breaks Python's native ability to launch asynchronous subprocesses (`asyncio.create_subprocess_exec`), which the Execution Branch heavily depends on. Furthermore, fresh installs currently crash due to uninitialized SQLite tables, and `uv` environment locks block the auto-installer. 

This plan fundamentally resolves these architectural flaws without relying on dirty workarounds.

## User Review Required
> [!IMPORTANT] 
> By removing the `WindowsSelectorEventLoopPolicy` hack, we must choose how to reconcile `pyzmq` with the Windows `ProactorEventLoop`. The proposed solution implements **Strict Thread Isolation** (running PyZMQ in a dedicated sync thread, communicating with the async loop via ThreadSafe Queues) to achieve zero extra dependencies. 
> Alternatively, we can officially add `tornado>=6.1` to the dependencies, which natively bridges `pyzmq` to the Proactor loop for us.

## Open Questions
> [!WARNING]
> Do you approve the zero-dependency **Strict Thread Isolation** approach for `mesh_broker.py`, or would you rather we just formally inject `tornado` into the `kernel.py` auto-installer to let PyZMQ patch itself?

---

## Proposed Changes

### 1. Revert Event Loop Hacks
We will restore the Windows default `ProactorEventLoop` to ensure the Execution Branch can spawn native subprocesses.

#### [MODIFY] `omnios_cli.py` & `omniswarm_py/omniswarm_daemon.py`
Remove the brute-force policy override:
```python
# DELETE THESE LINES
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### 2. PyZMQ Proactor Fix (Thread Isolation Strategy)
#### [MODIFY] `omniswarm_py/mesh_broker.py`
We will rewrite `MCPMeshBroker` to spawn a dedicated polling thread.
```python
import threading
import zmq

class MCPMeshBroker:
    def __init__(self, node_id):
        self.node_id = node_id
        # Main asyncio loop (Proactor)
        self.main_loop = asyncio.get_running_loop() 
        self.msg_queue = asyncio.Queue()
        
        # Start ZMQ in an isolated synchronous thread
        self.zmq_thread = threading.Thread(target=self._zmq_polling_loop, daemon=True)
        self.zmq_thread.start()

    def _zmq_polling_loop(self):
        # Operates purely synchronously, unaffected by asyncio Proactor policies
        context = zmq.Context()
        socket = context.socket(zmq.ROUTER)
        socket.bind("tcp://*:5565")
        
        while True:
            msg = socket.recv_multipart()
            # Push to the main Proactor asyncio loop safely
            self.main_loop.call_soon_threadsafe(self.msg_queue.put_nowait, msg)
```

### 3. SQLite Auto-Initialization
#### [MODIFY] `omniswarm_py/holographic_ast.py`
Prevent the `sqlite3.OperationalError` from crashing the daemon on fresh clones by aggressively generating the expected schema before querying.

```python
    def generate_embeddings_background_task(self, on_batch_complete=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # NEW: Ensure schema exists on fresh boot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                name TEXT,
                node_type TEXT,
                vector_embedding BLOB
            )
        """)
        conn.commit()
```

### 4. PEP-668 / UV Environment Fallback
#### [MODIFY] `omniswarm_py/kernel.py`
Instead of blindly forcing `--break-system-packages` on PC, we will auto-generate an isolated `.omnios_venv` if the system is detected as externally managed, and proxy the daemon process into that virtual environment dynamically.

## Verification Plan
### Automated Tests
* Manually run `python omniswarm_py/omniswarm_daemon.py` to ensure it boots without a Unicode error or a SQLite `no such table` crash on a completely blank repo.
* Trigger a background command via `omnios_cli.py compute_res_execute_bash '{"cmd": "echo test"}'` to guarantee that asynchronous subprocess I/O functions flawlessly alongside ZeroMQ without throwing a `NotImplementedError`.

### Manual Verification
* Ensure no `uv` lock or `pip` errors fire during the auto-installation phase when the repository is first cloned.
