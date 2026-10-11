# Changelog

## 1.2.0

### Added
- **Governed task delegation** between nodes (`omniswarm_py/governance.py`).
  - `harness.delegate_task(target, cmd, timeout_s)` and `python pc_agent.py delegate <target> "<cmd>"`.
  - Lifecycle `pending -> running -> completed | failed`, enforced in code.
  - Executing node checks the task's sender against the message envelope, checks that the task targets it, rejects duplicate task IDs, and caps command length and timeout.
  - Results return as `task_result` messages. The sender applies a result only from the assigned executor.
  - Each node keeps its own ledger: the sender in `workflow.json`, the executor in `tasks_<agent_id>.json`.
- Shared governance rule: `.agents/rules/omniswarm_task_governance.md`.
- Test suite: `tests/test_governance.py` (run with `python tests/test_governance.py`).
- `MANIFEST.in`, so the sdist ships the entry scripts, config template, rules, and tests.

### Fixed
- `pc_agent.py` no longer hardcodes `127.0.0.1`; it reads the hub address from `mesh_config.json`.
- A failed dispatch marks the task `failed` instead of leaving it `pending`.
- `kernel.py` and `omni_hub.py` import from the package first, so they work installed or run from inside `omniswarm_py/`.
- `omnios_cli.py` has a `main()` entry point, so the `omnios-cli` console command works.
- `setup.py` ships `omnios_cli`, `bootloader`, `pc_agent`, and `phone_agent` as modules.

### Known limitations
- Sender identity is not authenticated. The bus trusts the `sender` name a client supplies.
- The legacy `exec:` / `exec_shell` path on the phone is not governed; it has no task ID or ledger entry.
- Live test covered a harmless command only. Failing and timing-out commands are not yet tested live.

## 1.1.0
- Phone agent build deployment (`deploy_build`, `fetch_build`), WebRTC P2P transport, SyntyChat bridge.
