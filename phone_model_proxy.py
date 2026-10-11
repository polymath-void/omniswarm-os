#!/usr/bin/env python3
"""
OmniSwarm Phone Model Compute Proxy (Edge Node)
Binds to 127.0.0.1:57161 on Android Termux and transparently forwards all
embedding and completion requests to the PC Compute Host (192.168.0.111:57161).
Eliminates local llama-server CPU overhead, reduces heat, and prevents battery drain.
"""

import os
import sys
import time
import socket
import select
import threading

LOCAL_PORT = 57161
REMOTE_HOST = os.environ.get("OMNISWARM_PC_HOST", "192.168.0.111")
REMOTE_PORT = int(os.environ.get("OMNISWARM_PC_PORT", "57161"))

def pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.close()
        except Exception:
            pass
        try:
            dst.close()
        except Exception:
            pass

def handle_connection(client_sock):
    try:
        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_sock.settimeout(10.0)
        remote_sock.connect((REMOTE_HOST, REMOTE_PORT))
        remote_sock.settimeout(None)

        t1 = threading.Thread(target=pipe, args=(client_sock, remote_sock), daemon=True)
        t2 = threading.Thread(target=pipe, args=(remote_sock, client_sock), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except Exception as e:
        try:
            client_sock.close()
        except Exception:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(("127.0.0.1", LOCAL_PORT))
    except Exception as e:
        print(f"[PhoneModelProxy] Error binding to 127.0.0.1:{LOCAL_PORT}: {e}")
        sys.exit(1)

    server.listen(64)
    print(f"[PhoneModelProxy] Forwarding 127.0.0.1:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT}")
    
    while True:
        try:
            client, _ = server.accept()
            th = threading.Thread(target=handle_connection, args=(client,), daemon=True)
            th.start()
        except Exception as e:
            time.sleep(0.5)

if __name__ == "__main__":
    main()
