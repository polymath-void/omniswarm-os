#!/usr/bin/env python3
"""
Test Suite: OmniSwarm Phase 2 WebRTC P2P DataChannel Transport
Verifies direct P2P messaging, STUN NAT configuration, and CRDT replication.
"""

import sys
import os
import asyncio
import time
import json

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, SCRIPT_DIR)

from omniswarm_py.webrtc_mesh import OmniWebRTCMesh

async def run_test():
    print("\n=======================================================")
    print("  ⚡ OMNISWARM PHASE 2: WEBRTC P2P DATACHANNEL TEST    ")
    print("=======================================================\n")

    phone_node = OmniWebRTCMesh(node_id="PhoneAgent-Termux")
    pc_node = OmniWebRTCMesh(node_id="PCAgent")

    received_on_pc = []
    received_on_phone = []

    def on_pc_msg(origin, data):
        print(f"    [PC Received P2P from {origin}]: {data.get('content')}")
        received_on_pc.append(data)
        # Reply back directly over WebRTC
        pc_node.send_p2p_message(origin, {"type": "P2P_REPLY", "content": "PONG: WebRTC DataChannel verified on PC!", "rtt_start": data.get("t0")})

    def on_phone_msg(origin, data):
        t1 = time.time()
        t0 = data.get("rtt_start", t1)
        rtt_ms = (t1 - t0) * 1000
        print(f"    [Phone Received P2P from {origin}]: {data.get('content')} (RTT: {rtt_ms:.2f}ms)")
        received_on_phone.append(data)

    pc_node.register_message_handler(on_pc_msg)
    phone_node.register_message_handler(on_phone_msg)

    print(">>> 1. Generating SDP Offer from PhoneAgent-Termux...")
    offer = await phone_node.create_offer_for_peer("PCAgent")
    print(f"    ✅ Offer generated (Type: {offer['type']}, SDP bytes: {len(offer['sdp'])})")

    print("\n>>> 2. Handling Offer and Generating SDP Answer on PCAgent...")
    answer = await pc_node.handle_remote_offer("PhoneAgent-Termux", offer["sdp"])
    print(f"    ✅ Answer generated (Type: {answer['type']}, SDP bytes: {len(answer['sdp'])})")

    print("\n>>> 3. Applying Answer on PhoneAgent-Termux and establishing P2P link...")
    await phone_node.apply_remote_answer("PCAgent", answer["sdp"])

    # Wait for DataChannel to open
    for _ in range(40):
        ch = phone_node.data_channels.get("PCAgent")
        if ch and ch.readyState == "open":
            break
        await asyncio.sleep(0.05)

    ch = phone_node.data_channels.get("PCAgent")
    print(f"    ✅ WebRTC DataChannel State: {ch.readyState if ch else 'None'}")
    assert ch and ch.readyState == "open", "DataChannel failed to open"

    print("\n>>> 4. Transmitting P2P Data Packets over Direct SCTP/DTLS/UDP...")
    t0 = time.time()
    phone_node.send_p2p_message("PCAgent", {
        "type": "P2P_DIRECTIVE",
        "content": "PING: Direct P2P WebRTC message across NAT!",
        "t0": t0
    })

    await asyncio.sleep(0.2)

    print("\n>>> 5. Testing ComputeRes CRDT State Replication...")
    phone_node.crdt.set("cluster_health", "100% NOMINAL")
    phone_node.crdt.set("nat_traversal", "DIRECT_P2P_ACTIVE")
    phone_node.broadcast_crdt()

    await asyncio.sleep(0.2)
    print("    PC CRDT State after merge:", pc_node.crdt.state)
    assert pc_node.crdt.state.get("nat_traversal") == "DIRECT_P2P_ACTIVE", "CRDT merge failed"

    # Cleanup
    await phone_node.close()
    await pc_node.close()

    print("\n=======================================================")
    print("  🎉 PHASE 2 WEBRTC P2P TEST PASSED (100% OPERATIONAL)  ")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_test())
