#!/usr/bin/env python3
"""
Dynamic DocGen CLI
=============================================================================
Command-line interface for the Dynamic DocGen Living Architecture Engine.
Builds, serves, and watches documentation for Python & JS/TS codebases.
=============================================================================
"""

import os
import sys
import json
import time
import http.server
import socketserver
import argparse
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from docgen.compiler import DocGenCompiler

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def run_build(target_dir: str, output_paths: Optional[list] = None) -> dict:
    target = os.path.abspath(target_dir)
    print(f"\n{CYAN}{BOLD}⚡ Compiling Living Documentation for:{RESET} {target}")
    compiler = DocGenCompiler(root_dir=target)
    manifest = compiler.compile()

    stats = manifest["project"]["stats"]
    duration = manifest["project"]["build_duration_sec"]

    # Default output locations
    if not output_paths:
        output_paths = [
            os.path.join(target, "docs_manifest.json"),
            os.path.join(target, "docgen", "ui", "public", "docs_manifest.json"),
            os.path.join(target, "docgen", "ui", "dist", "docs_manifest.json")
        ]

    for out in output_paths:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            print(f"  {GREEN}✅ Written:{RESET} {os.path.relpath(out, target)}")
        except Exception as e:
            print(f"  {YELLOW}⚠️ Could not write {out}: {e}{RESET}")

    print(f"\n{GREEN}{BOLD}🎉 Build Completed in {duration}s!{RESET}")
    print(f"  📁 Total Files      : {stats['total_files']}")
    print(f"  📝 Lines of Code    : {stats['total_loc']:,}")
    print(f"  🏛️ Classes Parsed   : {stats['total_classes']}")
    print(f"  ⚡ Functions/Methods: {stats['total_functions']}")
    print(f"  🧩 Avg Complexity   : {stats['avg_complexity']}")
    print(f"  🔗 Graph Nodes      : {len(manifest['graph']['nodes'])}")
    print(f"  🔗 Graph Edges      : {len(manifest['graph']['edges'])}\n")

    return manifest

def run_serve(dist_dir: str, port: int = 8088):
    target = os.path.abspath(dist_dir)
    if not os.path.exists(target):
        # Fallback to docgen/ui or project root
        ui_public = os.path.join(SCRIPT_DIR, "docgen", "ui", "public")
        target = ui_public if os.path.exists(ui_public) else SCRIPT_DIR

    os.chdir(target)
    handler = http.server.SimpleHTTPRequestHandler
    
    print(f"\n{MAGENTA}{BOLD}======================================================={RESET}")
    print(f"{MAGENTA}{BOLD}  🌐 Dynamic DocGen Living UI Server Running           {RESET}")
    print(f"{MAGENTA}{BOLD}  Local Address : http://localhost:{port}             {RESET}")
    print(f"{MAGENTA}{BOLD}  Serving Path  : {target}                            {RESET}")
    print(f"{MAGENTA}{BOLD}======================================================={RESET}\n")

    with socketserver.TCPServer(("", port), handler) as httpd:
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
            # Check if any .py, .js, .ts file modified since last_run
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
    build_p.add_argument("--dir", default=".", help="Root directory to analyze")
    build_p.add_argument("--out", nargs="*", help="Custom output JSON path(s)")

    serve_p = subparsers.add_parser("serve", help="Serve static documentation UI")
    serve_p.add_argument("--dir", default="./docgen/ui/dist", help="Directory to serve")
    serve_p.add_argument("--port", type=int, default=8088, help="Port to bind")

    watch_p = subparsers.add_parser("watch", help="Continuously watch and re-index on change")
    watch_p.add_argument("--dir", default=".", help="Root directory to watch")
    watch_p.add_argument("--interval", type=float, default=2.0, help="Check interval in seconds")

    args = parser.parse_args()

    if args.command == "build" or not args.command:
        run_build(getattr(args, "dir", "."), getattr(args, "out", None))
    elif args.command == "serve":
        run_serve(args.dir, args.port)
    elif args.command == "watch":
        run_watch(args.dir, args.interval)

if __name__ == "__main__":
    main()
