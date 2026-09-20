import os
import json
import asyncio

class IntentGarbageCollector:
    """
    Event-driven worker that cleans up workflow.json.
    Runs once at boot, and subsequently only when explicitly triggered by an agent,
    eliminating wasteful disk polling.
    """
    def __init__(self, workspace_root):
        self.workflow_path = os.path.join(workspace_root, "workflow.json")

    def sweep_completed_intents(self):
        """Sweeps completed intents instantly with zero background polling."""
        if not os.path.exists(self.workflow_path):
            return {"status": "skipped", "message": "No workflow.json found."}

        try:
            with open(self.workflow_path, 'r') as f:
                data = json.load(f)

            if "intents" not in data or not data["intents"]:
                return {"status": "clean", "message": "No intents to clean."}

            original_count = len(data["intents"])
            active_intents = [
                intent for intent in data["intents"] 
                if intent.get("status") != "completed"
            ]

            if len(active_intents) < original_count:
                data["intents"] = active_intents
                tmp_file = self.workflow_path + ".tmp"
                with open(tmp_file, 'w') as f:
                    json.dump(data, f, indent=2)
                os.replace(tmp_file, self.workflow_path)
                
                cleared = original_count - len(active_intents)
                msg = f"🧹 Auto-deleted {cleared} completed intent(s)."
                print(f"\n[IntentGC] {msg}")
                return {"status": "success", "cleared": cleared, "message": msg}
                
            return {"status": "clean", "message": "No completed intents found."}

        except json.JSONDecodeError:
            return {"status": "error", "message": "workflow.json is currently locked or corrupted."}
