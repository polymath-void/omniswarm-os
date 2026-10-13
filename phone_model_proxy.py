#!/usr/bin/env python3
"""
OmniSwarm Phone Model Compute Proxy (Edge Node)
Binds to 127.0.0.1:57161 on Android Termux and transparently forwards all
embedding and completion HTTP requests to the PC Compute Host (192.168.0.111:57161).
Eliminates local llama-server CPU overhead, reduces heat, and prevents battery drain.
"""

import os
import sys
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import urllib.request
import urllib.error

LOCAL_PORT = 57161
REMOTE_HOST = os.environ.get("OMNISWARM_PC_HOST", "192.168.0.111")
REMOTE_PORT = int(os.environ.get("OMNISWARM_PC_PORT", "57161"))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ModelProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet logging

    def do_GET(self):
        self._forward_request("GET")

    def do_POST(self):
        self._forward_request("POST")

    def _forward_request(self, method):
        target_url = f"http://{REMOTE_HOST}:{REMOTE_PORT}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req_headers = {}
        for key, val in self.headers.items():
            if key.lower() not in ("host", "content-length", "connection"):
                req_headers[key] = val

        req = urllib.request.Request(
            target_url,
            data=body,
            headers=req_headers,
            method=method
        )

        try:
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                resp_data = resp.read()
                self.send_response(resp.status)
                for h_key, h_val in resp.getheaders():
                    if h_key.lower() not in ("transfer-encoding", "content-length", "connection"):
                        self.send_header(h_key, h_val)
                self.send_header("Content-Length", str(len(resp_data)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(resp_data)
        except urllib.error.HTTPError as e:
            err_data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(err_data)
        except Exception as e:
            err_msg = f'{{"error": "Compute proxy bridge error: {e}"}}'.encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_msg)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(err_msg)

def main():
    server_address = ("127.0.0.1", LOCAL_PORT)
    try:
        httpd = ThreadedHTTPServer(server_address, ModelProxyHandler)
        print(f"[PhoneModelProxy] HTTP Reverse Proxy active on 127.0.0.1:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT}")
        httpd.serve_forever()
    except Exception as e:
        print(f"[PhoneModelProxy] Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
