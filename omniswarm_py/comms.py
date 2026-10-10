import os
import time
import json
import sqlite3
from typing import Dict, List, Any, Optional

class SwarmCommsBus:
    """
    Decentralized Autonomous Communications & Log Synchronization Bus.
    Allows PC Agents and Phone Agents to communicate directly in a continuous loop
    without human copy-pasting, and live-stream execution logs to each other.
    """
    def __init__(self, db_path: str, workspace_root: Optional[str] = None):
        self.db_path = db_path
        self.workspace_root = workspace_root or os.path.dirname(os.path.abspath(db_path))
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        
        # 1. Swarm Messages Table (Agent-to-Agent Direct Messaging)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS swarm_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                timestamp REAL NOT NULL
            )
        """)
        
        # 2. Swarm Operational Logs Table (Live cross-device diagnostics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS swarm_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                log_level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()

    def send_message(self, sender: str, recipient: str, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Posts a message to another agent."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        ts = time.time()
        data_str = json.dumps(data) if data is not None else "{}"
        cursor.execute(
            "INSERT INTO swarm_messages (sender, recipient, message, data, timestamp) VALUES (?, ?, ?, ?, ?)",
            (sender, recipient, message, data_str, ts)
        )
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Mirror into SyntyChat in-memory room for real-time pub/sub subscribers
        try:
            try:
                from synty_chat import chat_server
            except ImportError:
                from omniswarm_py.synty_chat import chat_server
            chat_server.post_message(
                room_name="swarm_dev",
                sender=sender,
                content=message,
                msg_type="chat",
                metadata={"recipient": recipient, "data": data or {}}
            )
        except Exception:
            pass

        return {
            "status": "success",
            "message_id": msg_id,
            "sender": sender,
            "recipient": recipient,
            "timestamp": ts
        }

    def get_messages(self, recipient: Optional[str] = None, since_id: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves messages for an agent since a given message ID."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        if recipient and recipient != "*":
            cursor.execute(
                "SELECT id, sender, recipient, message, data, timestamp FROM swarm_messages WHERE (recipient = ? OR recipient = '*') AND id > ? ORDER BY id ASC LIMIT ?",
                (recipient, since_id, limit)
            )
        else:
            cursor.execute(
                "SELECT id, sender, recipient, message, data, timestamp FROM swarm_messages WHERE id > ? ORDER BY id ASC LIMIT ?",
                (since_id, limit)
            )
            
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for r in rows:
            try:
                data_obj = json.loads(r[4])
            except Exception:
                data_obj = {}
            messages.append({
                "id": r[0],
                "sender": r[1],
                "recipient": r[2],
                "message": r[3],
                "data": data_obj,
                "timestamp": r[5]
            })
        return messages

    def post_log(self, agent_id: str, log_level: str, message: str) -> Dict[str, Any]:
        """Streams an operational log into the shared swarm ledger."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        ts = time.time()
        cursor.execute(
            "INSERT INTO swarm_logs (agent_id, log_level, message, timestamp) VALUES (?, ?, ?, ?)",
            (agent_id, log_level.upper(), message, ts)
        )
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Mirror into SyntyChat in-memory ops_stream room
        try:
            try:
                from synty_chat import chat_server
            except ImportError:
                from omniswarm_py.synty_chat import chat_server
            chat_server.post_message(
                room_name="ops_stream",
                sender=agent_id,
                content=message,
                msg_type="OPERATION_LOG",
                metadata={"level": log_level.upper()}
            )
        except Exception:
            pass

        return {"status": "success", "log_id": log_id, "timestamp": ts}

    def get_logs(self, agent_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent logs across the swarm."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        if agent_id:
            cursor.execute(
                "SELECT id, agent_id, log_level, message, timestamp FROM swarm_logs WHERE agent_id = ? ORDER BY id DESC LIMIT ?",
                (agent_id, limit)
            )
        else:
            cursor.execute(
                "SELECT id, agent_id, log_level, message, timestamp FROM swarm_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for r in reversed(rows):
            logs.append({
                "id": r[0],
                "agent_id": r[1],
                "level": r[2],
                "message": r[3],
                "timestamp": r[4]
            })
        return logs

    def sync_workflow_intent(self, intent_payload: Dict[str, Any]) -> bool:
        """Atomically saves an intent to the Hub's workflow.json."""
        workflow_file = os.path.join(self.workspace_root, "workflow.json")
        try:
            if os.path.exists(workflow_file):
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
            else:
                workflow = {"intents": []}
            
            workflow["intents"].append(intent_payload)
            tmp_file = workflow_file + ".tmp"
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2)
            os.replace(tmp_file, workflow_file)
            return True
        except Exception as e:
            print(f"[SwarmComms] Failed to sync workflow intent: {e}")
            return False
