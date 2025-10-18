import os
import yaml


CONFIG_FILENAME = "chainfeed_control.yaml"
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", CONFIG_FILENAME)


class ChainFeedConfig:
    """Loads and exposes ChainFeed configuration like a dictionary."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        full_path = os.path.abspath(config_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Config file not found: {full_path}")

        with open(full_path, "r") as f:
            self._config = yaml.safe_load(f)

    def __getitem__(self, key):
        return self._config[key]

    def __contains__(self, key):
        return key in self._config

    def get(self, key, default=None):
        return self._config.get(key, default)

    def as_dict(self):
        """Return the entire configuration as a dict."""
        return dict(self._config)

    def __repr__(self):
        return f"<ChainFeedConfig keys={list(self._config.keys())}>"