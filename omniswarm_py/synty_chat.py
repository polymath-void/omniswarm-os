#!/usr/bin/env python3
"""
SyntyChatServer Module for OmniSwarm-OS
=============================================================================
Evolution of SyntyChatServer (originally synthesized via syntycode.sdk)
adapted into an enterprise, asynchronous, multi-room, zero-HIL communication
and operations-log streaming engine for AI agent swarms.

Features:
- Room & Client Management (inspired by SyntyChatServer's Client/Room/Server architecture)
- Asynchronous Broadcast & Message Routing
- Operations Log Streaming between PC and Edge/Phone Nodes
- ZeroMQ PUB/SUB Real-Time Integration
- Persistent Chat & Telemetry Ledger (JSONL)
- Zero Human-In-The-Loop Autonomous Protocol
=============================================================================
"""

import os
import sys
import json
import time
import uuid
import asyncio
from typing import Dict, List, Any, Optional

class SyntyClient:
    """
    Representation of a participating Swarm Agent or Human in SyntyChat.
    """
    def __init__(self, client_id: str, role: str = "agent", metadata: Optional[Dict[str, Any]] = None):
        self.client_id = client_id
        self.role = role
        self.metadata = metadata or {}
        self.queue = asyncio.Queue()
        self.last_active = time.time()

    def send(self, message: Dict[str, Any]):
        """Synchronously enqueue message for client."""
        self.last_active = time.time()
        try:
            self.queue.put_nowait(message)
        except Exception:
            pass

    async def recv(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Asynchronously wait for the next message."""
        try:
            if timeout:
                return await asyncio.wait_for(self.queue.get(), timeout=timeout)
            return await self.queue.get()
        except asyncio.TimeoutError:
            return None


class SyntyRoom:
    """
    Chat room for Swarm coordination, log streaming, and autonomous task dispatch.
    """
    def __init__(self, name: str, persistence_file: Optional[str] = None):
        self.name = name
        self.clients: Dict[str, SyntyClient] = {}
        self.history: List[Dict[str, Any]] = []
        self.max_history = 500
        self.persistence_file = persistence_file

    def add_client(self, client: SyntyClient):
        self.clients[client.client_id] = client

    def remove_client(self, client_id: str):
        if client_id in self.clients:
            del self.clients[client_id]

    def broadcast(self, message: Dict[str, Any], sender_id: Optional[str] = None):
        """Broadcasts a message to all clients in the room."""
        # Ensure timestamp and message ID
        if "timestamp" not in message:
            message["timestamp"] = time.time()
        if "id" not in message:
            message["id"] = str(uuid.uuid4())[:8]
        if "room" not in message:
            message["room"] = self.name

        self.history.append(message)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Write to persistence ledger if configured
        if self.persistence_file:
            try:
                with open(self.persistence_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(message) + "\n")
            except Exception:
                pass

        for cid, c in list(self.clients.items()):
            # Send to all clients
            c.send(message)

    def get_history(self, limit: int = 50, since_timestamp: float = 0.0) -> List[Dict[str, Any]]:
        """Retrieves recent history filtered by timestamp."""
        filtered = [m for m in self.history if m.get("timestamp", 0) > since_timestamp]
        return filtered[-limit:]


class SyntyChatServer:
    """
    Core SyntyChatServer Hub managing rooms, routing, and persistence.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        self.rooms: Dict[str, SyntyRoom] = {}
        self.storage_dir = storage_dir or os.getcwd()
        self.ledger_file = os.path.join(self.storage_dir, "synty_chat_ledger.jsonl")
        
        # Pre-seed default core rooms
        self.create_room("swarm_dev")      # General agent coordination
        self.create_room("ops_stream")     # Raw operation and execution logs
        self.create_room("autonomous_hil") # Zero-HIL directive/response channel

    def create_room(self, name: str) -> SyntyRoom:
        if name not in self.rooms:
            self.rooms[name] = SyntyRoom(name, persistence_file=self.ledger_file)
        return self.rooms[name]

    def get_room(self, name: str) -> Optional[SyntyRoom]:
        return self.rooms.get(name)

    def join_room(self, room_name: str, client: SyntyClient) -> SyntyRoom:
        room = self.get_room(room_name)
        if not room:
            room = self.create_room(room_name)
        room.add_client(client)
        return room

    def leave_room(self, room_name: str, client_id: str):
        room = self.get_room(room_name)
        if room:
            room.remove_client(client_id)

    def post_message(
        self,
        room_name: str,
        sender: str,
        content: Any,
        msg_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Posts a message to a room and broadcasts to participants."""
        room = self.get_room(room_name)
        if not room:
            room = self.create_room(room_name)

        msg_obj = {
            "id": str(uuid.uuid4())[:8],
            "room": room_name,
            "sender": sender,
            "type": msg_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        room.broadcast(msg_obj)
        return msg_obj

    def poll_messages(self, room_name: str, limit: int = 50, since_timestamp: float = 0.0) -> List[Dict[str, Any]]:
        room = self.get_room(room_name)
        if not room:
            return []
        return room.get_history(limit=limit, since_timestamp=since_timestamp)

    def list_rooms(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": r.name,
                "clients_count": len(r.clients),
                "messages_cached": len(r.history)
            }
            for r in self.rooms.values()
        ]

# Global singleton server instance for easy in-process access
chat_server = SyntyChatServer()
