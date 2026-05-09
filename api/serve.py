#!/usr/bin/env python3
"""
LAN launcher for the Modly FastAPI backend.

Wan2GP can keep running on its own port (usually 8100). This launcher exposes
Modly as a separate service, usually on 8765, with /api/* aliases for dashboard
clients.
"""

from __future__ import annotations

import argparse
import os
import socket

import uvicorn


def _lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Modly API on the local network")
    parser.add_argument("--host", default=os.environ.get("MODLY_API_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MODLY_API_PORT", "8765")))
    parser.add_argument("--token", default=os.environ.get("MODLY_API_TOKEN"))
    parser.add_argument("--cors-origins", default=os.environ.get("MODLY_CORS_ORIGINS", "*"))
    parser.add_argument("--models-dir", default=os.environ.get("MODELS_DIR"))
    parser.add_argument("--workspace-dir", default=os.environ.get("WORKSPACE_DIR"))
    parser.add_argument("--extensions-dir", default=os.environ.get("EXTENSIONS_DIR"))
    parser.add_argument("--selected-model-id", default=os.environ.get("SELECTED_MODEL_ID"))
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload for development")
    args = parser.parse_args()

    if args.token:
        os.environ["MODLY_API_TOKEN"] = args.token
    if args.cors_origins is not None:
        os.environ["MODLY_CORS_ORIGINS"] = args.cors_origins
    if args.models_dir:
        os.environ["MODELS_DIR"] = args.models_dir
    if args.workspace_dir:
        os.environ["WORKSPACE_DIR"] = args.workspace_dir
    if args.extensions_dir:
        os.environ["EXTENSIONS_DIR"] = args.extensions_dir
    if args.selected_model_id:
        os.environ["SELECTED_MODEL_ID"] = args.selected_model_id

    lan_ip = _lan_ip()
    print(f"Modly API on http://{args.host}:{args.port}", flush=True)
    print(f"  LAN health: http://{lan_ip}:{args.port}/api/health", flush=True)
    print(f"  auth:       {'bearer token required for LAN clients' if args.token else 'OFF (trusted LAN mode)'}", flush=True)
    print(f"  cors:       {args.cors_origins}", flush=True)

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
