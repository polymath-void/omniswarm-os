#!/data/data/com.termux/files/usr/bin/python3
"""
Dynamic DocGen CLI
=============================================================================
Command-line interface for the Dynamic DocGen Living Architecture Engine.
Builds, serves, and watches documentation for Python & JS/TS codebases.
Works standalone on any target project directory.
=============================================================================
"""

import os
import sys
import json
import time
import shutil
import http.server
import socketserver
import argparse
from typing import Optional, List

DOCGEN_DIR = os.path.dirname(os.path.abspath(__file__))
if DOCGEN_DIR not in sys.path:
    sys.path.insert(0, DOCGEN_DIR)

from docgen.compiler import DocGenCompiler

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def run_build(target_dir: str, output_paths: Optional[List[str]] = None, bundle_ui: bool = False) -> dict:
    target = os.path.abspath(target_dir)
    print(f"\n{CYAN}{BOLD}⚡ Compiling Living Documentation for:{RESET} {target}")
    compiler = DocGenCompiler(root_dir=target)
    manifest = compiler.compile()

    stats = manifest["project"]["stats"]
    duration = manifest["project"]["build_duration_sec"]

    # Target manifest location
    target_manifest = os.path.join(target, "docs_manifest.json")
    targets_to_write = [target_manifest]

    # Also update DocGen's internal UI locations if DocGen is local
    docgen_ui_dist = os.path.join(DOCGEN_DIR, "docgen", "ui", "dist", "docs_manifest.json")
    docgen_ui_pub = os.path.join(DOCGEN_DIR, "docgen", "ui", "public", "docs_manifest.json")
    for d in [docgen_ui_dist, docgen_ui_pub]:
        if os.path.exists(os.path.dirname(d)) and d not in targets_to_write:
            targets_to_write.append(d)

    if output_paths:
        for out in output_paths:
            p = os.path.abspath(out)
            if p not in targets_to_write:
                targets_to_write.append(p)

    for out in targets_to_write:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            rel_label = os.path.relpath(out, target) if out.startswith(target) else out
            print(f"  {GREEN}✅ Written:{RESET} {rel_label}")
        except Exception as e:
            print(f"  {YELLOW}⚠️ Could not write {out}: {e}{RESET}")

    # Optionally copy static UI into target project
    if bundle_ui:
        dest_ui_dir = os.path.join(target, "docs_ui")
        src_dist = os.path.join(DOCGEN_DIR, "docgen", "ui", "dist")
        if os.path.exists(src_dist):
            try:
                shutil.copytree(src_dist, dest_ui_dir, dirs_exist_ok=True)
                print(f"  {GREEN}✅ Bundled Static UI into:{RESET} {os.path.relpath(dest_ui_dir, target)}/")
            except Exception as e:
                print(f"  {YELLOW}⚠️ Could not bundle UI: {e}{RESET}")

    print(f"\n{GREEN}{BOLD}🎉 Build Completed in {duration}s!{RESET}")
    print(f"  📁 Total Files      : {stats['total_files']}")
    print(f"  📝 Lines of Code    : {stats['total_loc']:,}")
    print(f"  🏛️ Classes Parsed   : {stats['total_classes']}")
    print(f"  ⚡ Functions/Methods: {stats['total_functions']}")
    print(f"  🧩 Avg Complexity   : {stats['avg_complexity']}")
    print(f"  🔗 Graph Nodes      : {len(manifest['graph']['nodes'])}")
    print(f"  🔗 Graph Edges      : {len(manifest['graph']['edges'])}\n")

    return manifest

class DynamicDocGenHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler that serves the DocGen UI while dynamically
    routing /docs_manifest.json to the target project's manifest.
    """
    target_manifest_path = None

    def do_GET(self):
        clean_path = self.path.split('?')[0]
        if clean_path in ["/docs_manifest.json", "/public/docs_manifest.json"]:
            if self.target_manifest_path and os.path.exists(self.target_manifest_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(self.target_manifest_path, "rb") as f:
                    self.wfile.write(f.read())
                return
        return super().do_GET()

def run_serve(target_or_dist: str, port: int = 8088):
    target = os.path.abspath(target_or_dist)
    docgen_dist = os.path.join(DOCGEN_DIR, "docgen", "ui", "dist")

    manifest_path = None
    serve_dir = docgen_dist

    # If target has a docs_manifest.json directly:
    if os.path.isfile(target) and target.endswith(".json"):
        manifest_path = target
        serve_dir = docgen_dist
    elif os.path.isdir(target):
        candidate_manifest = os.path.join(target, "docs_manifest.json")
        if os.path.exists(candidate_manifest):
            manifest_path = candidate_manifest
        candidate_index = os.path.join(target, "index.html")
        if os.path.exists(candidate_index):
            serve_dir = target
        else:
            serve_dir = docgen_dist

    if not os.path.exists(serve_dir):
        serve_dir = os.path.join(DOCGEN_DIR, "docgen", "ui", "public")

    DynamicDocGenHTTPHandler.target_manifest_path = manifest_path

    # Allow immediate socket reuse to prevent Address already in use
    socketserver.TCPServer.allow_reuse_address = True
    
    print(f"\n{MAGENTA}{BOLD}======================================================={RESET}")
    print(f"{MAGENTA}{BOLD}  🌐 Dynamic DocGen Living UI Server Running           {RESET}")
    print(f"{MAGENTA}{BOLD}  Local Address : http://localhost:{port}             {RESET}")
    print(f"{MAGENTA}{BOLD}  Serving UI    : {serve_dir}                         {RESET}")
    if manifest_path:
        print(f"{MAGENTA}{BOLD}  Manifest Target: {manifest_path}                    {RESET}")
    print(f"{MAGENTA}{BOLD}======================================================={RESET}\n")

    os.chdir(serve_dir)
    with socketserver.TCPServer(("", port), DynamicDocGenHTTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Stopping DocGen server...{RESET}")

def run_watch(target_dir: str, interval: float = 2.0):
    target = os.path.abspath(target_dir)
    print(f"{CYAN}👀 Watching {target} for code changes (interval: {interval}s)...{RESET}")
    last_run = time.time()
    run_build(target)

    try:
        while True:
            time.sleep(interval)
            changed = False
            for root, dirs, files in os.walk(target):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "dist", "build", "__pycache__"}]
                for file in files:
                    if file.endswith((".py", ".js", ".jsx", ".ts", ".tsx")):
                        fp = os.path.join(root, file)
                        try:
                            if os.path.getmtime(fp) > last_run:
                                changed = True
                                break
                        except Exception:
                            pass
                if changed:
                    break

            if changed:
                last_run = time.time()
                print(f"\n{YELLOW}🔄 Change detected. Re-indexing...{RESET}")
                run_build(target)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopping DocGen watcher.{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Dynamic DocGen Living Architecture CLI")
    subparsers = parser.add_subparsers(dest="command")

    build_p = subparsers.add_parser("build", help="Build living documentation manifest")
    build_p.add_argument("--dir", default=".", help="Root directory to analyze (default: current directory)")
    build_p.add_argument("--out", nargs="*", help="Custom output JSON path(s)")
    build_p.add_argument("--bundle-ui", action="store_true", help="Bundle static HTML/JS UI into target docs_ui/ directory")

    serve_p = subparsers.add_parser("serve", help="Serve static documentation UI")
    serve_p.add_argument("--dir", default=".", help="Project directory or dist path to serve (default: current directory)")
    serve_p.add_argument("--port", type=int, default=8088, help="Port to bind (default: 8088)")

    watch_p = subparsers.add_parser("watch", help="Continuously watch and re-index on change")
    watch_p.add_argument("--dir", default=".", help="Root directory to watch (default: current directory)")
    watch_p.add_argument("--interval", type=float, default=2.0, help="Check interval in seconds")

    args = parser.parse_args()

    if args.command == "build" or not args.command:
        target = getattr(args, "dir", ".")
        out = getattr(args, "out", None)
        bundle = getattr(args, "bundle_ui", False)
        run_build(target, out, bundle)
    elif args.command == "serve":
        run_serve(args.dir, args.port)
    elif args.command == "watch":
        run_watch(args.dir, args.interval)

if __name__ == "__main__":
    main()
