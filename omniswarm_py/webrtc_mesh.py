#!/usr/bin/env python3
"""
OmniSwarm Phase 2: WebRTC P2P DataChannel Mesh Transport
Integrates ComputeRes decentralized networking into OmniOS.

Provides direct NAT hole-punching (STUN/ICE), SCTP over DTLS encrypted data channels,
and CRDT state synchronization, eliminating reliance on bore.pub cloud relay.
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List

logger = logging.getLogger("OmniWebRTC")

try:
    from aiortc import (
        RTCPeerConnection,
        RTCSessionDescription,
        RTCIceCandidate,
        RTCConfiguration,
        RTCIceServer
    )
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False

# Default public STUN servers for NAT hole-punching
DEFAULT_ICE_SERVERS = [
    RTCIceServer("stun:stun.l.google.com:19302"),
    RTCIceServer("stun:stun1.l.google.com:19302"),
    RTCIceServer("stun:stun2.l.google.com:19302")
]

class CRDTStateEngine:
    """
    ComputeRes Last-Writer-Wins (LWW) CRDT State Engine.
    Provides deterministic conflict-free replication across P2P edge nodes.
    """
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.add_set: Dict[str, float] = {}
        self.remove_set: Dict[str, float] = {}

    def set(self, key: str, value: Any) -> float:
        ts = time.time()
        self.state[key] = value
        self.add_set[key] = ts
        return ts

    def delete(self, key: str) -> float:
        ts = time.time()
        self.state.pop(key, None)
        self.remove_set[key] = ts
        return ts

    def get_export_payload(self) -> Dict[str, Any]:
        return {
            "state": dict(self.state),
            "add_set": dict(self.add_set),
            "remove_set": dict(self.remove_set)
        }

    def merge_remote(self, remote: Dict[str, Any]):
        r_adds = remote.get("add_set", {})
        r_rems = remote.get("remove_set", {})
        r_state = remote.get("state", {})

        for k, ts in r_adds.items():
            if k not in self.add_set or ts > self.add_set[k]:
                self.add_set[k] = ts

        for k, ts in r_rems.items():
            if k not in self.remove_set or ts > self.remove_set[k]:
                self.remove_set[k] = ts

        new_state = {}
        for k, add_ts in self.add_set.items():
            if k not in self.remove_set or add_ts > self.remove_set[k]:
                new_state[k] = r_state.get(k, self.state.get(k))

        self.state = new_state

class OmniWebRTCMesh:
    """
    Decentralized WebRTC P2P DataChannel Node for OmniOS.
    Direct peer-to-peer transport eliminating cloud relays.
    """
    def __init__(self, node_id: str, ice_servers: Optional[List[RTCIceServer]] = None):
        self.node_id = node_id
        self.ice_servers = ice_servers or DEFAULT_ICE_SERVERS
        self.config = RTCConfiguration(self.ice_servers) if AIORTC_AVAILABLE else None
        
        self.peer_connections: Dict[str, Any] = {} # peer_id -> RTCPeerConnection
        self.data_channels: Dict[str, Any] = {}    # peer_id -> RTCDataChannel
        self.message_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.crdt = CRDTStateEngine()
        self.is_ready = AIORTC_AVAILABLE

    def register_message_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        self.message_callbacks.append(handler)

    def _on_channel_message(self, origin_peer: str, raw_msg: str):
        try:
            payload = json.loads(raw_msg)
            msg_type = payload.get("type")

            if msg_type == "CRDT_SYNC":
                self.crdt.merge_remote(payload.get("crdt", {}))
                return

            for cb in self.message_callbacks:
                try:
                    cb(origin_peer, payload)
                except Exception as e:
                    logger.error(f"Error in WebRTC message callback: {e}")
        except Exception:
            pass

    async def create_offer_for_peer(self, peer_id: str) -> Dict[str, Any]:
        """Creates an SDP offer and initiates a DataChannel."""
        if not self.is_ready:
            raise RuntimeError("aiortc is not available in environment.")

        pc = RTCPeerConnection(configuration=self.config)
        self.peer_connections[peer_id] = pc

        # Create DataChannel with SCTP reliable transport
        channel = pc.createDataChannel("omniswarm_p2p", ordered=True)
        self.data_channels[peer_id] = channel

        @channel.on("open")
        def on_open():
            logger.info(f"⚡ [WebRTC] Direct P2P DataChannel OPEN with peer '{peer_id}'!")
            # Trigger initial CRDT sync
            self.broadcast_crdt()

        @channel.on("message")
        def on_message(msg):
            self._on_channel_message(peer_id, msg)

        @pc.on("iceconnectionstatechange")
        def on_ice_change():
            logger.debug(f"[WebRTC ICE:{peer_id}] State changed to {pc.iceConnectionState}")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        return {
            "type": "offer",
            "sdp": pc.localDescription.sdp,
            "origin": self.node_id,
            "target": peer_id
        }

    async def handle_remote_offer(self, peer_id: str, offer_sdp: str) -> Dict[str, Any]:
        """Handles an incoming SDP offer and generates an SDP answer."""
        if not self.is_ready:
            raise RuntimeError("aiortc is not available in environment.")

        pc = RTCPeerConnection(configuration=self.config)
        self.peer_connections[peer_id] = pc

        @pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"⚡ [WebRTC] Incoming DataChannel '{channel.label}' established from '{peer_id}'!")
            self.data_channels[peer_id] = channel

            @channel.on("message")
            def on_msg(m):
                self._on_channel_message(peer_id, m)

        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_sdp, type="offer"))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return {
            "type": "answer",
            "sdp": pc.localDescription.sdp,
            "origin": self.node_id,
            "target": peer_id
        }

    async def apply_remote_answer(self, peer_id: str, answer_sdp: str):
        """Applies the SDP answer returned by the remote peer."""
        pc = self.peer_connections.get(peer_id)
        if not pc:
            raise ValueError(f"No active PeerConnection found for peer '{peer_id}'")

        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer_sdp, type="answer"))
        logger.info(f"[WebRTC] Remote answer applied for peer '{peer_id}'. Negotiating ICE...")

    def send_p2p_message(self, peer_id: str, payload: Dict[str, Any]) -> bool:
        """Sends a JSON message directly across the WebRTC DataChannel."""
        channel = self.data_channels.get(peer_id)
        if channel and channel.readyState == "open":
            channel.send(json.dumps(payload))
            return True
        return False

    def broadcast_p2p(self, payload: Dict[str, Any]) -> int:
        """Broadcasts a payload to all currently connected WebRTC peers."""
        count = 0
        data_str = json.dumps(payload)
        for peer_id, channel in self.data_channels.items():
            if channel.readyState == "open":
                channel.send(data_str)
                count += 1
        return count

    def broadcast_crdt(self):
        """Broadcasts current CRDT state to all peers."""
        payload = {
            "type": "CRDT_SYNC",
            "crdt": self.crdt.get_export_payload(),
            "origin": self.node_id,
            "timestamp": time.time()
        }
        self.broadcast_p2p(payload)

    async def close(self):
        """Closes all peer connections gracefully."""
        for pc in self.peer_connections.values():
            await pc.close()
        self.peer_connections.clear()
        self.data_channels.clear()
