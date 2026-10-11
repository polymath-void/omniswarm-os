import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "omniswarm_py"))

from governance import (
    GovernanceError, TaskLedger, build_exec_task, build_result_data,
    summarize_result, validate_incoming_task,
)


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wf = os.path.join(self.tmp.name, "workflow.json")
        self.ledger = TaskLedger(self.wf)

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_rejects_self_delegation_and_bad_timeouts(self):
        with self.assertRaises(GovernanceError):
            build_exec_task("PCAgent", "PCAgent", "echo hi")
        with self.assertRaises(GovernanceError):
            build_exec_task("PCAgent", "PhoneAgent-Termux", "echo hi", timeout_s=0)
        with self.assertRaises(GovernanceError):
            build_exec_task("PCAgent", "PhoneAgent-Termux", "echo hi", timeout_s=9999)
        with self.assertRaises(GovernanceError):
            build_exec_task("PCAgent", "PhoneAgent-Termux", "   ")

    def test_incoming_validation_binds_sender_and_target(self):
        task = build_exec_task("PCAgent", "PhoneAgent-Termux", "echo hi")
        ok = validate_incoming_task(task, "PhoneAgent-Termux", "PCAgent")
        self.assertEqual(ok["sender"], "PCAgent")
        with self.assertRaises(GovernanceError):
            validate_incoming_task(task, "PhoneAgent-Termux", "SomeoneElse")
        with self.assertRaises(GovernanceError):
            validate_incoming_task(task, "OtherNode", "PCAgent")
        with self.assertRaises(GovernanceError):
            validate_incoming_task({**task, "action": "exec_shell"}, "PhoneAgent-Termux", "PCAgent")

    def test_lifecycle_pending_running_completed(self):
        task = build_exec_task("PCAgent", "PhoneAgent-Termux", "echo hi")
        self.ledger.record("PCAgent", task)
        self.ledger.transition(task["task_id"], "running")
        self.ledger.transition(task["task_id"], "completed", {"success": True}, actor="PhoneAgent-Termux")
        with open(self.wf) as f:
            intent = json.load(f)["intents"][-1]
        self.assertEqual(intent["status"], "completed")
        self.assertEqual(intent["result"], {"success": True})

    def test_illegal_transitions_and_duplicates_rejected(self):
        task = build_exec_task("PCAgent", "PhoneAgent-Termux", "echo hi")
        self.ledger.record("PCAgent", task)
        with self.assertRaises(GovernanceError):
            self.ledger.record("PCAgent", task)
        self.ledger.transition(task["task_id"], "completed", actor="PhoneAgent-Termux")
        with self.assertRaises(GovernanceError):
            self.ledger.transition(task["task_id"], "running")

    def test_result_from_wrong_peer_is_rejected(self):
        task = build_exec_task("PCAgent", "PhoneAgent-Termux", "echo hi")
        self.ledger.record("PCAgent", task)
        with self.assertRaises(GovernanceError):
            self.ledger.transition(task["task_id"], "completed", actor="Forger")
        with open(self.wf) as f:
            self.assertEqual(json.load(f)["intents"][-1]["status"], "pending")

    def test_ledger_refuses_to_overwrite_non_object(self):
        with open(self.wf, "w") as f:
            json.dump([1, 2, 3], f)
        task = build_exec_task("PCAgent", "PhoneAgent-Termux", "echo hi")
        with self.assertRaises(RuntimeError):
            self.ledger.record("PCAgent", task)

    def test_result_summary_is_bounded(self):
        summary = summarize_result({"success": True, "returncode": 0, "stdout": "x" * 10000, "stderr": ""})
        self.assertLessEqual(len(summary["stdout"]), 2000)
        data = build_result_data("task_1", "completed", summary)
        self.assertEqual(data["action"], "task_result")


if __name__ == "__main__":
    unittest.main()
