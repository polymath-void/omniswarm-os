#!/usr/bin/env python3
"""
SyntyChat Swarm Bridge & Zero-HIL Autonomous Relay
=============================================================================
Bridges SyntyChatServer with ZeroMQ, MCPMeshBroker, and OmniOSAgentHarness.
Allows Phone and PC agents to seamlessly stream operations logs, exchange
task directives, and collaborate autonomously with ZERO Human-In-The-Loop.
=============================================================================
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
try:
    from synty_chat import chat_server, SyntyClient, SyntyRoom
except ImportError:
    from omniswarm_py.synty_chat import chat_server, SyntyClient, SyntyRoom

class SyntySwarmBridge:
    """
    Connects the in-process SyntyChatServer with the external ZeroMQ Swarm bus.
    """
    def __init__(self, broker=None, comms_bus=None):
        self.server = chat_server
        self.broker = broker
        self.comms_bus = comms_bus

    async def handle_chat_rpc(self, tool_name: str, args: dict) -> dict:
        """Handles incoming RPC calls from across the network."""
        if tool_name == "synty_chat_post":
            room = args.get("room", "swarm_dev")
            sender = args.get("sender", "anonymous")
            content = args.get("content", "")
            msg_type = args.get("type", "chat")
            meta = args.get("metadata", {})
            
            msg = self.server.post_message(room, sender, content, msg_type, meta)
            
            # Broadcast over ZMQ PUB bus if broker is available
            if self.broker and hasattr(self.broker, "send_queue"):
                topic = f"SYNTY_CHAT:{room}".encode("utf-8")
                payload = json.dumps(msg).encode("utf-8")
                self.broker.send_queue.put(('pub_bcast', [topic, payload]))
                
            # Mirror to SwarmComms SQLite ledger for persistent unified cross-querying
            if self.comms_bus:
                try:
                    if msg_type == "OPERATION_LOG":
                        self.comms_bus.post_log(sender, meta.get("level", "INFO"), f"[{room}] {content}")
                    else:
                        target = meta.get("target_agent", "*")
                        self.comms_bus.send_message(sender, target, f"[{room}] {content}", {"synty_id": msg["id"], "type": msg_type, "meta": meta})
                except Exception:
                    pass

            return {"status": "success", "message_id": msg["id"], "timestamp": msg["timestamp"]}

        elif tool_name == "synty_chat_read":
            room = args.get("room", "swarm_dev")
            since = float(args.get("since_timestamp", 0.0))
            limit = int(args.get("limit", 50))
            msgs = self.server.poll_messages(room, limit=limit, since_timestamp=since)
            return {"status": "success", "room": room, "messages": msgs, "count": len(msgs)}

        elif tool_name == "synty_chat_rooms":
            rooms = self.server.list_rooms()
            return {"status": "success", "rooms": rooms}

        return {"status": "error", "message": f"Unknown SyntyChat tool: {tool_name}"}


class AutonomousAgentBridge:
    """
    Autonomous loop worker designed to run on either Phone or PC.
    Listens for tasks in the shared room, executes them, and streams back logs.
    Completely eliminates the Human-In-The-Loop copy-paste cycle.
    """
    def __init__(self, harness, agent_id: str, room: str = "swarm_dev"):
        self.harness = harness
        self.agent_id = agent_id
        self.room = room
        self.running = False
        self.last_seen_time = time.time()
        self.custom_handlers: Dict[str, Callable] = {}

    def register_handler(self, directive_name: str, handler_func: Callable):
        """Register a handler for a specific directive."""
        self.custom_handlers[directive_name] = handler_func

    async def post_log(self, log_line: str, log_level: str = "INFO"):
        """Streams an operation log to the shared room."""
        await self.harness.execute_in_swarm("synty_chat_post", {
            "room": self.room,
            "sender": self.agent_id,
            "content": log_line,
            "type": "OPERATION_LOG",
            "metadata": {"level": log_level, "source_device": sys.platform}
        })

    async def post_message(self, text: str, msg_type: str = "chat", metadata: Optional[dict] = None):
        """Sends a standard message to the room."""
        return await self.harness.execute_in_swarm("synty_chat_post", {
            "room": self.room,
            "sender": self.agent_id,
            "content": text,
            "type": msg_type,
            "metadata": metadata or {}
        })

    async def run_loop(self, poll_interval: float = 1.0):
        """Runs the continuous autonomous communication loop."""
        self.running = True
        print(f"[{self.agent_id}] 🔄 SyntyChat Autonomous Zero-HIL Loop Online in room '{self.room}'...")
        await self.post_log(f"Agent '{self.agent_id}' online and synchronized with Zero-HIL mesh.")

        while self.running:
            try:
                res = await self.harness.execute_in_swarm("synty_chat_read", {
                    "room": self.room,
                    "since_timestamp": self.last_seen_time,
                    "limit": 20
                })
                
                if res.get("status") == "success":
                    messages = res.get("messages", [])
                    for msg in messages:
                        self.last_seen_time = max(self.last_seen_time, msg.get("timestamp", 0.0))
                        sender = msg.get("sender")
                        if sender == self.agent_id:
                            continue  # Ignore self messages
                            
                        await self._process_incoming_message(msg)
            except Exception as e:
                # Sleep and continue on network glitches
                pass

            await asyncio.sleep(poll_interval)

    async def _process_incoming_message(self, msg: dict):
        sender = msg.get("sender")
        mtype = msg.get("type")
        content = msg.get("content")
        
        print(f"\n📩 [{self.room}] Incoming from {sender} ({mtype}): {content}")
        
        # Check if message is a task directive targeted at this agent
        if mtype == "TASK_DIRECTIVE":
            if isinstance(content, dict):
                action = content.get("action")
                payload = content.get("payload", {})
                if action in self.custom_handlers:
                    print(f"⚡ [Autonomous] Executing handler for directive: {action}")
                    try:
                        result = await self.custom_handlers[action](payload)
                        await self.post_message(
                            text=f"Completed task '{action}': {result}",
                            msg_type="TASK_RESULT",
                            metadata={"reply_to": msg.get("id"), "action": action, "result": result}
                        )
                    except Exception as err:
                        await self.post_message(
                            text=f"Failed task '{action}': {err}",
                            msg_type="TASK_ERROR",
                            metadata={"reply_to": msg.get("id"), "error": str(err)}
                        )
                else:
                    await self.post_log(f"No local handler registered for directive '{action}'", "WARN")

    def stop(self):
        self.running = False
