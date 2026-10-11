import json
import os
import threading
import time
import uuid
from typing import Any, Dict, Optional

TASK_ACTION = "delegated_exec"
RESULT_ACTION = "task_result"
TASK_STATES = ("pending", "running", "completed", "failed")
TASK_TRANSITIONS = {
    "pending": {"running", "completed", "failed"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}
DEFAULT_TIMEOUT_S = 120.0
MAX_TIMEOUT_S = 600.0
MAX_CMD_CHARS = 8192
RESULT_TAIL_CHARS = 2000

_LEDGER_LOCK = threading.Lock()


class GovernanceError(ValueError):
    pass


def _check_cmd_and_timeout(cmd: Any, timeout_s: Any) -> float:
    if not isinstance(cmd, str) or not cmd.strip():
        raise GovernanceError("cmd must be a non-empty string")
    if len(cmd) > MAX_CMD_CHARS:
        raise GovernanceError(f"cmd exceeds {MAX_CMD_CHARS} characters")
    try:
        timeout = float(timeout_s)
    except (TypeError, ValueError):
        raise GovernanceError("timeout_s must be a number")
    if not 0 < timeout <= MAX_TIMEOUT_S:
        raise GovernanceError(f"timeout_s must be in (0, {MAX_TIMEOUT_S:g}]")
    return timeout


def build_exec_task(sender: str, target: str, cmd: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> Dict[str, Any]:
    """Creates a task record on the delegating node before it leaves the device."""
    if not sender or not target:
        raise GovernanceError("sender and target are required")
    if sender == target:
        raise GovernanceError("an agent cannot delegate a task to itself")
    timeout = _check_cmd_and_timeout(cmd, timeout_s)
    return {
        "task_id": f"task_{uuid.uuid4().hex[:12]}",
        "action": TASK_ACTION,
        "sender": sender,
        "target": target,
        "cmd": cmd,
        "timeout_s": timeout,
        "created_at": time.time(),
    }


def validate_incoming_task(data: Dict[str, Any], local_agent: str, message_sender: str) -> Dict[str, Any]:
    """Checks a delegated task on the executing node before it runs.

    The sender is taken from the message envelope, so a task cannot claim to come from someone else.
    """
    task_id = data.get("task_id")
    if not task_id or not isinstance(task_id, str):
        raise GovernanceError("task_id is required")
    if data.get("action") != TASK_ACTION:
        raise GovernanceError(f"action must be '{TASK_ACTION}'")
    target = data.get("target")
    if target not in (None, local_agent):
        raise GovernanceError(f"task targets '{target}', not '{local_agent}'")
    claimed_sender = data.get("sender") or message_sender
    if claimed_sender != message_sender:
        raise GovernanceError("task sender does not match message sender")
    timeout = _check_cmd_and_timeout(data.get("cmd"), data.get("timeout_s", DEFAULT_TIMEOUT_S))
    return {
        "task_id": task_id,
        "action": TASK_ACTION,
        "sender": message_sender,
        "target": local_agent,
        "cmd": data["cmd"],
        "timeout_s": timeout,
    }


def summarize_result(exec_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "success": bool(exec_result.get("success")),
        "returncode": exec_result.get("returncode"),
        "stdout": (exec_result.get("stdout") or "")[-RESULT_TAIL_CHARS:],
        "stderr": (exec_result.get("stderr") or exec_result.get("error") or "")[-RESULT_TAIL_CHARS:],
    }


def build_result_data(task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if status not in TASK_STATES:
        raise GovernanceError(f"unknown task state '{status}'")
    data: Dict[str, Any] = {"action": RESULT_ACTION, "task_id": task_id, "status": status}
    if result is not None:
        data["result"] = result
    return data


class TaskLedger:
    """Tracks delegated tasks as intents in workflow.json (pending -> running -> completed/failed)."""

    def __init__(self, workflow_file: str):
        self.workflow_file = workflow_file

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.workflow_file):
            return {"intents": []}
        with open(self.workflow_file, "r", encoding="utf-8") as f:
            wf = json.load(f)
        if not isinstance(wf, dict):
            raise RuntimeError(f"{self.workflow_file} is not a JSON object; refusing to overwrite it")
        wf.setdefault("intents", [])
        return wf

    def _save(self, wf: Dict[str, Any]) -> None:
        tmp_file = self.workflow_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(wf, f, indent=2)
        os.replace(tmp_file, self.workflow_file)

    def record(self, agent_id: str, task: Dict[str, Any]) -> None:
        with _LEDGER_LOCK:
            wf = self._load()
            if any((i.get("saved_state") or {}).get("task_id") == task["task_id"] for i in wf["intents"] if i.get("kind") == "delegated_task"):
                raise GovernanceError(f"task {task['task_id']} already recorded")
            wf["intents"].append({
                "agent_id": agent_id,
                "status": "pending",
                "kind": "delegated_task",
                "saved_state": {k: task.get(k) for k in ("task_id", "action", "sender", "target", "cmd", "timeout_s")},
                "timestamp": time.time(),
            })
            self._save(wf)

    def transition(self, task_id: str, new_status: str, result: Optional[Dict[str, Any]] = None, actor: Optional[str] = None) -> Dict[str, Any]:
        if new_status not in TASK_STATES:
            raise GovernanceError(f"unknown task state '{new_status}'")
        with _LEDGER_LOCK:
            wf = self._load()
            for intent in reversed(wf["intents"]):
                state = intent.get("saved_state") or {}
                if intent.get("kind") != "delegated_task" or state.get("task_id") != task_id:
                    continue
                if actor is not None and actor != state.get("target"):
                    raise GovernanceError(f"{actor} is not the assigned executor for {task_id}")
                current = intent.get("status")
                if new_status not in TASK_TRANSITIONS.get(current, set()):
                    raise GovernanceError(f"illegal transition {current} -> {new_status} for {task_id}")
                intent["status"] = new_status
                intent["timestamp"] = time.time()
                if result is not None:
                    intent["result"] = result
                self._save(wf)
                return intent
        raise GovernanceError(f"unknown task {task_id}")
