"""Dry-run adapter: logs every signal as if filled, but places no real orders.

Recommended for the first 24-48 hours so you can verify routing + sizing
before risking real money.
"""
from __future__ import annotations
import logging
import time
import uuid

from .base import BaseAdapter

LOG = logging.getLogger("tbot_client.adapters.dryrun")


class DryRunAdapter(BaseAdapter):
    def place_order(self, signal: dict, size_usd: float) -> dict:
        sid = signal.get("signal_id", "?")
        fake_fill = signal.get("market_price", 0) or 1.0
        fake_order_id = f"dryrun_{uuid.uuid4().hex[:8]}"
        LOG.info("[DRYRUN] would place %s %s  size=$%.2f  fill=%s  order=%s",
                 signal.get("direction", "?"),
                 signal.get("market_id", "?")[:40],
                 size_usd, fake_fill, fake_order_id)
        return {
            "filled":          True,
            "fill_price":      float(fake_fill),
            "contracts":       int(size_usd / max(float(fake_fill), 0.01)),
            "broker_order_id": fake_order_id,
        }
