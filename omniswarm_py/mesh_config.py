import os
import json
from typing import Dict, Any, Optional

DEFAULT_CONFIG_FILE = "mesh_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "node_id": "OmniNode",
    "role": "edge",              # "hub" or "edge"
    "hub_host": "bore.pub",      # Default to Virtual Hub endpoint or 127.0.0.1
    "rpc_port": 33458,           # Virtual Hub RPC port or 5565
    "pub_port": 5566,
    "auto_tunnel": False,
    "tunnel_provider": "bore"
}

def get_workspace_root() -> str:
    """Finds the root workspace directory where omniswarm-os is rooted."""
    current = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(current)
    if os.path.exists(os.path.join(parent, "requirements.txt")):
        return parent
    return os.getcwd()

def get_config_path(workspace_root: Optional[str] = None) -> str:
    root = workspace_root or get_workspace_root()
    return os.path.join(root, DEFAULT_CONFIG_FILE)

def load_mesh_config(workspace_root: Optional[str] = None) -> Dict[str, Any]:
    """Loads mesh configuration from mesh_config.json or environment variables."""
    config = dict(DEFAULT_CONFIG)
    config_file = get_config_path(workspace_root)
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8-sig") as f:
                disk_config = json.load(f)
                config.update(disk_config)
        except Exception as e:
            print(f"[MeshConfig] Warning: Failed to read {config_file}: {e}")

    # Environment variables take highest priority
    if "OMNIOS_NODE_ID" in os.environ:
        config["node_id"] = os.environ["OMNIOS_NODE_ID"]
    if "OMNIOS_ROLE" in os.environ:
        config["role"] = os.environ["OMNIOS_ROLE"].lower()
    if "OMNIOS_HUB_HOST" in os.environ:
        config["hub_host"] = os.environ["OMNIOS_HUB_HOST"]
    if "OMNIOS_HUB_PORT" in os.environ:
        try:
            config["rpc_port"] = int(os.environ["OMNIOS_HUB_PORT"])
        except ValueError:
            pass
    if "OMNIOS_PUB_PORT" in os.environ:
        try:
            config["pub_port"] = int(os.environ["OMNIOS_PUB_PORT"])
        except ValueError:
            pass

    return config

def save_mesh_config(config: Dict[str, Any], workspace_root: Optional[str] = None) -> str:
    """Saves mesh configuration to disk."""
    config_file = get_config_path(workspace_root)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return config_file
