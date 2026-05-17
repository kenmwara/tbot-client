"""Entry point: python -m tbot_client"""
from __future__ import annotations
import logging
import signal
import sys
import time
from pathlib import Path

from .config import load_config
from .feed import FeedPoller
from .router import SignalRouter
from .state import LocalState

LOG = logging.getLogger("tbot_client")


def _setup_logging(level: str, state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    handlers = [logging.StreamHandler(sys.stdout),
                logging.FileHandler(state_dir / "client.log")]
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)sZ  %(levelname)-5s  %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=handlers,
    )


def main(config_path: str = "config.yaml") -> int:
    cfg = load_config(config_path)
    state_dir = Path(cfg.runtime.state_dir).expanduser()
    _setup_logging(cfg.runtime.log_level, state_dir)

    LOG.info("tbot-client starting — operator=%s, dry_run=%s",
             cfg.operator.feed_url, cfg.runtime.dry_run)

    state = LocalState(state_dir / "state.json")
    router = SignalRouter(cfg, state)
    poller = FeedPoller(cfg, router, state)

    stop = {"flag": False}
    def _shutdown(signum, frame):
        LOG.info("received signal %s — shutting down", signum)
        stop["flag"] = True
    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while not stop["flag"]:
            try:
                poller.tick()
            except Exception as e:
                LOG.exception("poll tick failed: %s", e)
            for _ in range(cfg.runtime.poll_interval_seconds):
                if stop["flag"]: break
                time.sleep(1)
    finally:
        state.save()
        LOG.info("tbot-client stopped cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "config.yaml"))
