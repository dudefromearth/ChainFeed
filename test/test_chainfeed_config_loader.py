from config.chainfeed_config_loader import ChainFeedConfig

def test_config_loader_reads_defaults():
    config = ChainFeedConfig()

    assert "feeds" in config
    assert "symbols" in config
    assert "heartbeat" in config
    assert "expiration_cache" in config
    assert "providers" in config

    assert isinstance(config["symbols"], list)
    assert isinstance(config["feeds"], dict)
    assert isinstance(config["heartbeat"], dict)
    assert isinstance(config["expiration_cache"], dict)
    assert isinstance(config["providers"], dict)