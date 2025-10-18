# utils/variant_config.py

import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "variant_config.yaml"

def load_variant_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    if "symbols" not in config:
        raise ValueError("Configuration must include 'symbols' list")

    return config