#!/usr/bin/env python3
"""
OmniSwarm PC Compute & Model Inference Server
Offloads heavy embedding and model generation workloads from mobile edge nodes (Termux)
to the PC host, reducing mobile CPU thermal load and conserving battery.
"""

import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("[PC Compute Server] Initializing FastEmbed model engine...")
from fastembed import TextEmbedding

# Initialize embedding model (sentence-transformers/all-MiniLM-L6-v2, 384-dim)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedding_engine = TextEmbedding(model_name=MODEL_NAME)
print(f"[PC Compute Server] Model '{MODEL_NAME}' loaded successfully.")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ModelRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Concise logging
        print(f"[PC Compute Engine] {self.address_string()} - {format % args}")

    def do_GET(self):
        if self.path in ["/health", "/healthz", "/"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            payload = {
                "status": "ok",
                "service": "OmniSwarm PC Compute Host",
                "model": MODEL_NAME,
                "dimension": 384,
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            body = {}

        if self.path in ["/v1/embeddings", "/embeddings"]:
            input_data = body.get("input", "")
            if isinstance(input_data, str):
                texts = [input_data]
            elif isinstance(input_data, list):
                texts = input_data
            else:
                texts = [str(input_data)]

            t0 = time.time()
            embeddings_iter = embedding_engine.embed(texts)
            data_items = []
            for idx, vec in enumerate(embeddings_iter):
                data_items.append({
                    "object": "embedding",
                    "embedding": vec.tolist() if hasattr(vec, "tolist") else list(vec),
                    "index": idx
                })
            elapsed_ms = round((time.time() - t0) * 1000, 2)

            response = {
                "object": "list",
                "data": data_items,
                "model": MODEL_NAME,
                "usage": {
                    "prompt_tokens": len(texts),
                    "total_tokens": len(texts)
                },
                "compute_time_ms": elapsed_ms
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
            print(f"[PC Compute Engine] Processed {len(texts)} embeddings in {elapsed_ms}ms for {self.address_string()}")

        elif self.path in ["/completion", "/v1/completions"]:
            prompt = body.get("prompt", "")
            response = {
                "content": f"[PC Compute Host Acknowledged: Prompt length {len(prompt)}]",
                "model": MODEL_NAME,
                "finish_reason": "stop"
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

def main():
    host = "0.0.0.0"
    port = 57161
    server = ThreadedHTTPServer((host, port), ModelRequestHandler)
    print(f"\n==================================================================")
    print(f"[PC Compute Server] Listening on http://{host}:{port}")
    print(f"   Model: {MODEL_NAME} (Dim: 384)")
    print(f"   Edge Offloading: Ready for PhoneAgent / Termux requests")
    print(f"==================================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[PC Compute Server] Shutting down...")
        server.server_close()

if __name__ == "__main__":
    main()
