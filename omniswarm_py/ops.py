"""Native operator commands for OmniSwarm agents.

Agents operate the swarm through these verbs instead of writing Python:

    omnios send <peer> <message...>        message a peer, optionally wait for a reply
    omnios run <peer> <command...>         delegate a shell command, wait for its result
    omnios task status <task_id>           show one task's state and result summary
    omnios task list                       list delegated tasks and their states
    omnios inbox                           show unread messages addressed to this node
    omnios health <peer>                   ask a peer for device telemetry

Every verb prints one compact JSON document on stdout. Long output is truncated
and the full text is stored under .omnios/out/, so the console stays readable.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from omniswarm_py.governance import GovernanceError, TaskLedger, TASK_ACTION, RESULT_ACTION
from omniswarm_py.mesh_config import load_mesh_config

DEFAULT_WAIT_S = 120.0
INLINE_CHARS = 1200
STATE_DIR = ".omnios"
OUT_DIR = os.path.join(STATE_DIR, "out")
MAX_MESSAGE_WAIT_S = 600.0


def _root() -> str:
    return os.getcwd()


def _state_path(*parts: str) -> str:
    return os.path.join(_root(), *parts)


def _agent_id() -> str:
    return os.environ.get("OMNIOS_AGENT_ID") or "PCAgent"


def _emit(payload: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _clip(text: Optional[str], task_id: str, label: str) -> Dict[str, Any]:
    """Returns text inline if small, else stores it under .omnios/out and returns a pointer."""
    text = text or ""
    if len(text) <= INLINE_CHARS:
        return {"text": text, "truncated": False}
    os.makedirs(_state_path(OUT_DIR), exist_ok=True)
    path = _state_path(OUT_DIR, f"{task_id}.{label}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return {"text": text[-INLINE_CHARS:], "truncated": True, "full_output": os.path.relpath(path, _root()), "bytes": len(text)}


def _ledger_for(agent_id: str) -> TaskLedger:
    return TaskLedger(_state_path(STATE_DIR, "workflow.json"))


def _harness(agent_id: str):
    from omniswarm_py.agent_harness import OmniOSAgentHarness
    return OmniOSAgentHarness(agent_id=agent_id)


def _summarize_task(intent: Dict[str, Any]) -> Dict[str, Any]:
    state = intent.get("saved_state") or {}
    result = intent.get("result") or {}
    out = {
        "task_id": state.get("task_id"),
        "target": state.get("target"),
        "status": intent.get("status"),
        "cmd": state.get("cmd"),
        "updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(intent.get("timestamp", 0))),
    }
    if result:
        out["returncode"] = result.get("returncode")
        out["stdout"] = (result.get("stdout") or "")[-INLINE_CHARS:]
        out["stderr"] = (result.get("stderr") or "")[-INLINE_CHARS:]
    return out


async def cmd_send(args) -> int:
    agent_id = _agent_id()
    async with _harness(agent_id) as h:
        res = await h.send_agent_message(recipient=args.peer, message=" ".join(args.message))
        if res.get("status") != "success":
            _emit({"ok": False, "error": res.get("message") or res.get("error") or res})
            return 1
        out = {"ok": True, "sent_to": args.peer, "message_id": res.get("message_id")}
        if args.wait:
            deadline = time.time() + min(args.wait, MAX_MESSAGE_WAIT_S)
            since = res.get("message_id", 0)
            while time.time() < deadline:
                msgs = await h.read_my_messages(since_id=since, limit=20)
                for m in msgs:
                    since = max(since, m["id"])
                    if m.get("sender") == args.peer:
                        out["reply"] = {"id": m["id"], "message": m["message"][:INLINE_CHARS]}
                        _emit(out)
                        return 0
                await asyncio.sleep(1.0)
            out["reply"] = None
            out["timed_out"] = True
        _emit(out)
        return 0


async def cmd_run(args) -> int:
    agent_id = _agent_id()
    command = " ".join(args.command)
    async with _harness(agent_id) as h:
        dispatch = await h.delegate_task(args.peer, command, timeout_s=args.timeout)
        task_id = dispatch["task_id"]
        if dispatch["dispatch"].get("status") != "success":
            _emit({"ok": False, "task_id": task_id, "error": dispatch["dispatch"].get("message")})
            return 1
        ledger = h.task_ledger()
        deadline = time.time() + args.wait
        since = dispatch["dispatch"].get("message_id", 0)
        while time.time() < deadline:
            msgs = await h.read_my_messages(since_id=since, limit=20)
            for m in msgs:
                since = max(since, m["id"])
                if await h.apply_task_result(m):
                    intent = ledger.get(task_id)
                    if intent and intent.get("status") in ("completed", "failed"):
                        summary = _summarize_task(intent)
                        result_out = _clip(summary.get("stdout"), task_id, "stdout")
                        _emit({
                            "ok": intent["status"] == "completed",
                            "task_id": task_id,
                            "target": args.peer,
                            "status": intent["status"],
                            "returncode": summary.get("returncode"),
                            "stdout": result_out,
                            "stderr": (summary.get("stderr") or "")[-INLINE_CHARS:],
                        })
                        return 0 if intent["status"] == "completed" else 2
            await asyncio.sleep(1.0)
        _emit({"ok": False, "task_id": task_id, "status": "pending", "timed_out": True,
               "hint": f"still running on {args.peer}; check with: omnios task status {task_id}"})
        return 3


def cmd_task_status(args) -> int:
    intent = _ledger_for(_agent_id()).get(args.task_id)
    if not intent:
        _emit({"ok": False, "error": f"unknown task {args.task_id}"})
        return 1
    _emit({"ok": True, **_summarize_task(intent)})
    return 0


def cmd_task_list(args) -> int:
    tasks = [_summarize_task(i) for i in _ledger_for(_agent_id()).list_tasks()]
    counts: Dict[str, int] = {}
    for t in tasks:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    tasks = tasks[-args.limit:]
    for t in tasks:
        t.pop("stdout", None)
        t.pop("stderr", None)
    _emit({"ok": True, "counts": counts, "tasks": tasks})
    return 0


async def cmd_inbox(args) -> int:
    async with _harness(_agent_id()) as h:
        msgs = await h.read_my_messages(since_id=args.since, limit=args.limit)
        _emit({
            "ok": True,
            "count": len(msgs),
            "messages": [
                {"id": m["id"], "from": m["sender"], "message": m["message"][:INLINE_CHARS]}
                for m in msgs
            ],
        })
        return 0


async def cmd_health(args) -> int:
    async with _harness(_agent_id()) as h:
        res = await h.send_agent_message(recipient=args.peer, message="health", data={"action": "health_check"})
        if res.get("status") != "success":
            _emit({"ok": False, "error": res.get("message")})
            return 1
        since = res.get("message_id", 0)
        deadline = time.time() + args.wait
        while time.time() < deadline:
            for m in await h.read_my_messages(since_id=since, limit=20):
                since = max(since, m["id"])
                if m.get("sender") == args.peer:
                    _emit({"ok": True, "peer": args.peer, "telemetry": m.get("data") or {}})
                    return 0
            await asyncio.sleep(1.0)
        _emit({"ok": False, "peer": args.peer, "timed_out": True})
        return 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="omnios", description="Native OmniSwarm operator commands.")
    sub = p.add_subparsers(dest="verb", required=True)

    s = sub.add_parser("send", help="message a peer")
    s.add_argument("peer")
    s.add_argument("message", nargs="+")
    s.add_argument("--wait", type=float, default=0.0, help="seconds to wait for a reply")
    s.set_defaults(func=cmd_send, is_async=True)

    r = sub.add_parser("run", help="delegate a shell command and wait for its result")
    r.add_argument("peer")
    r.add_argument("command", nargs="+")
    r.add_argument("--timeout", type=float, default=120.0, help="execution limit on the peer (s)")
    r.add_argument("--wait", type=float, default=DEFAULT_WAIT_S, help="how long to wait for the result (s)")
    r.set_defaults(func=cmd_run, is_async=True)

    t = sub.add_parser("task", help="inspect delegated tasks")
    tsub = t.add_subparsers(dest="task_verb", required=True)
    ts = tsub.add_parser("status", help="show one task")
    ts.add_argument("task_id")
    ts.set_defaults(func=cmd_task_status, is_async=False)
    tl = tsub.add_parser("list", help="list tasks")
    tl.add_argument("--limit", type=int, default=20)
    tl.set_defaults(func=cmd_task_list, is_async=False)

    i = sub.add_parser("inbox", help="unread messages for this node")
    i.add_argument("--since", type=int, default=0)
    i.add_argument("--limit", type=int, default=20)
    i.set_defaults(func=cmd_inbox, is_async=True)

    h = sub.add_parser("health", help="ask a peer for telemetry")
    h.add_argument("peer")
    h.add_argument("--wait", type=float, default=20.0)
    h.set_defaults(func=cmd_health, is_async=True)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.is_async:
            return asyncio.run(args.func(args))
        return args.func(args)
    except GovernanceError as ge:
        _emit({"ok": False, "error": str(ge)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
