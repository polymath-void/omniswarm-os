import os
import sys
import asyncio
import json
import time

class VoidGovernor:
    def __init__(self, critical_memory_threshold_percent: float = 15.0):
        self.threshold = critical_memory_threshold_percent
        self.is_suspended = False
        
        # Determine Platform Strategy
        self.platform = sys.platform
        self.has_psutil = False
        try:
            import psutil
            self.has_psutil = True
            print(f"[VoidGovernor] Platform: {self.platform} | Engine: psutil")
        except ImportError:
            engine = "/proc/meminfo" if self.platform.startswith("linux") or self.platform == "android" else "Fallback (Unmonitored)"
            print(f"[VoidGovernor] Platform: {self.platform} | Engine: {engine}")
            
        print(f"[VoidGovernor] Initialized. Critical memory threshold set to {self.threshold}%")

    def _get_memory_stats(self) -> dict:
        """Cross-platform memory monitor."""
        stats = {"MemTotal": 100, "MemAvailable": 100} # Safe fallback
        
        # Strategy 1: psutil (Works natively on Windows, macOS, Linux)
        if self.has_psutil:
            import psutil
            mem = psutil.virtual_memory()
            return {"MemTotal": mem.total, "MemAvailable": mem.available}
            
        # Strategy 2: Native Linux/Android (/proc/meminfo)
        if self.platform.startswith("linux") or self.platform == "android":
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            stats["MemTotal"] = int(line.split()[1]) * 1024
                        elif line.startswith('MemAvailable:'):
                            stats["MemAvailable"] = int(line.split()[1]) * 1024
                        if stats["MemTotal"] != 100 and stats["MemAvailable"] != 100:
                            break
            except Exception:
                pass
                
        # Strategy 3: macOS/Windows fallback without psutil (Assume unlimited memory to prevent false crashes)
        return stats

    def get_available_memory_percent(self) -> float:
        stats = self._get_memory_stats()
        if stats["MemTotal"] == 0:
            return 100.0
        return (stats["MemAvailable"] / stats["MemTotal"]) * 100.0

    async def monitor_lmk_pressure(self, callback_on_suspend):
        print("[VoidGovernor] Daemon loop started. Watching memory pressure...")
        while not self.is_suspended:
            avail_pct = self.get_available_memory_percent()
            

            if avail_pct < self.threshold:
                print(f"\n[VoidGovernor] ⚠️ CRITICAL: Memory dropped to {avail_pct:.1f}%. System threat imminent!")
                self.is_suspended = True
                await callback_on_suspend()
                break
                
            await asyncio.sleep(1)

    def serialize_intent(self, task_id: str, current_state: dict):
        workflow_path = os.path.expanduser("~/Projects/workflow.json")
        dump = {
            "task_id": task_id,
            "status": "suspended_by_governor",
            "saved_state": current_state,
            "timestamp": time.time()
        }
        try:
            if os.path.exists(workflow_path):
                with open(workflow_path, 'r') as f:
                    workflow = json.load(f)
            else:
                workflow = {"intents": []}
                
            workflow["intents"] = [dump]
            
            with open(workflow_path, 'w') as f:
                json.dump(workflow, f, indent=2)
                
            print(f"[VoidGovernor] Intent successfully preserved. Yielding process gracefully.")
        except Exception as e:
            pass
