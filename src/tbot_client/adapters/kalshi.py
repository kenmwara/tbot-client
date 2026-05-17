"""Kalshi adapter — STUB.

To implement:
  1. Authenticate via Kalshi REST API on init using broker.api_email + api_password.
       POST /v1/log_in  →  capture bearer token
  2. In place_order():
       a. Convert size_usd to integer `count` of contracts using market_price as cost per contract.
       b. POST /v1/portfolio/orders with:
            {"ticker": signal["market_id"], "side": "yes" if direction=="YES" else "no",
             "count": count, "type": "limit",
             "yes_price": int(market_price * 100) if YES else None,
             "no_price":  int((1 - market_price) * 100) if NO else None,
             "client_order_id": signal["signal_id"]}
       c. Read response.order.order_id and response.order.status.
  3. Return {"filled": status == "filled", "fill_price": resp.fill_price,
             "contracts": count, "broker_order_id": order_id}.

Reference: https://docs.kalshi.com/api
Use the kalshi-python SDK if you prefer (pip install kalshi-python).
"""
from __future__ import annotations
import logging

from .base import BaseAdapter

LOG = logging.getLogger("tbot_client.adapters.kalshi")


class KalshiAdapter(BaseAdapter):
    def __init__(self, surface_cfg):
        super().__init__(surface_cfg)
        broker = surface_cfg.broker
        self.email      = broker.get("api_email")
        self.password   = broker.get("api_password")
        self.production = broker.get("production", False)
        if not (self.email and self.password):
            raise ValueError("kalshi adapter: api_email and api_password required")
        # TODO: authenticate, store self._token
        LOG.warning("KalshiAdapter is a STUB — implement authentication and order placement")

    def place_order(self, signal: dict, size_usd: float) -> dict:
        LOG.error("KalshiAdapter.place_order not yet implemented — signal %s",
                  signal.get("signal_id", "?")[:12])
        return {"filled": False, "reason": "kalshi_adapter_not_implemented"}
