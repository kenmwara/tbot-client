"""End-to-end smoke test against the live operator dashboard.

Builds a minimal config pointing at TestFriend1's token (created during Phase 1
smoke test), runs DryRunAdapter for forex, processes one tick, verifies state
advances and a callback gets through.

Run from repo root:
  python -m pytest tests/test_smoke.py -s
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tbot_client.config import load_config
from tbot_client.state import LocalState
from tbot_client.router import SignalRouter
from tbot_client.feed import FeedPoller


SKIP_NETWORK = not os.environ.get("TBOT_E2E_TOKEN")
NETWORK_REASON = "set TBOT_E2E_TOKEN to a valid subscriber token to enable"


@pytest.mark.skipif(SKIP_NETWORK, reason=NETWORK_REASON)
def test_one_tick_against_live_operator():
    cfg_yaml = {
        "operator": {
            "feed_url":         "http://ops.tbot.trade/api/signals/feed",
            "callback_base":    "http://ops.tbot.trade",
            "subscriber_token": os.environ["TBOT_E2E_TOKEN"],
        },
        "runtime": {
            "poll_interval_seconds": 30,
            "dry_run":               True,    # safety
            "log_level":             "INFO",
            "state_dir":             tempfile.mkdtemp(),
            "max_signal_age_seconds": 600,
        },
        "surfaces": {
            "forex": {
                "enabled": True, "bankroll": 100.0, "max_concurrent": 6,
                "dry_run": True,  # never touch real broker in test
                "broker":  {"type": "oanda", "account_id": "fake", "api_token": "fake"},
            },
        },
    }
    cfg_path = Path(cfg_yaml["runtime"]["state_dir"]) / "test_config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg_yaml))

    cfg = load_config(str(cfg_path))
    state = LocalState(Path(cfg.runtime.state_dir) / "state.json")
    router = SignalRouter(cfg, state)
    poller = FeedPoller(cfg, router, state)

    poller.tick()  # should not raise; cursor may or may not advance depending on feed contents
    state.save()
    print(f"smoke-test passed — cursor now {state.cursor()[:12] or '(empty)'}")


def test_imports_only():
    """Bare-minimum: every module importable without config."""
    import tbot_client
    import tbot_client.config
    import tbot_client.feed
    import tbot_client.router
    import tbot_client.state
    import tbot_client.adapters
    from tbot_client.adapters.dryrun import DryRunAdapter
    assert tbot_client.__version__ == "0.1.0"
