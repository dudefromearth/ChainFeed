# tests/test_variant_config.py

import pytest
from pathlib import Path
from utils.variant_config import load_variant_config

def test_load_valid_config(tmp_path):
    # Create a mock variant_config.yaml in a temp directory
    config_content = """
    variant: FatTail
    default_dte: 0
    max_dte: 5
    symbols:
      - symbol: SPX
        alias: S&P 500 Index
        dtes: [0, 1, 2]
      - symbol: ES
        alias: E-mini S&P
        dtes: [0, 1, 2]
    heartbeat:
      enabled: true
      interval_sec: 10
    """

    config_file = tmp_path / "variant_config.yaml"
    config_file.write_text(config_content)

    config = load_variant_config(config_file)

    assert config["variant"] == "FatTail"
    assert config["default_dte"] == 0
    assert config["symbols"][0]["symbol"] == "SPX"
    assert config["heartbeat"]["enabled"] is True

def test_missing_symbols_raises_error(tmp_path):
    config_content = """
    variant: BadConfig
    default_dte: 0
    """
    config_file = tmp_path / "bad_config.yaml"
    config_file.write_text(config_content)

    with pytest.raises(ValueError):
        load_variant_config(config_file)

def test_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        load_variant_config(Path("/nonexistent/path/config.yaml"))
