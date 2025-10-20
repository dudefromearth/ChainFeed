"""
config/chainfeed_config_loader.py
---------------------------------
Centralized YAML configuration loader for ChainFeed.
Supports group definitions for feed orchestration.
"""

import yaml
import os


def load_groups_config(path: str = None):
    """
    Load the YAML configuration that defines asset groups
    and their member instruments (SPX, ES, SPY, etc.).
    """
    if path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "groups.yaml")

    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ groups.yaml not found at {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        raise ValueError("❌ groups.yaml must contain a top-level list of groups")

    return data