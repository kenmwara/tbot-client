"""Exchange adapter — STUB.

Routes the operator's ST and LT signals to your exchange account. To implement against your exchange's REST API:
  1. On init, authenticate with broker.api_key + api_secret (use the exchange's sandbox while production is false).
  2. In place_order():
       a. Convert size_usd to an integer order quantity at signal["market_price"].
       b. Place a limit order for signal["market_id"] in signal["direction"], using signal["signal_id"] as the
          client order id so a retry can never double-fill.
       c. Read back the order id and status.
  3. Return {"filled": status == "filled", "fill_price": ..., "contracts": quantity, "broker_order_id": order_id}.
"""
from __future__ import annotations
import logging

from .base import BaseAdapter

LOG = logging.getLogger("tbot_client.adapters.exchange")


class ExchangeAdapter(BaseAdapter):
    def __init__(self, surface_cfg):
        super().__init__(surface_cfg)
        broker = surface_cfg.broker
        self.api_key    = broker.get("api_key")
        self.api_secret = broker.get("api_secret")
        self.production = broker.get("production", False)
        if not (self.api_key and self.api_secret):
            raise ValueError("exchange adapter: api_key and api_secret required")
        # TODO: authenticate, store the session token
        LOG.warning("ExchangeAdapter is a STUB — implement authentication and order placement")

    def place_order(self, signal: dict, size_usd: float) -> dict:
        LOG.error("ExchangeAdapter.place_order not yet implemented — signal %s",
                  signal.get("signal_id", "?")[:12])
        return {"filled": False, "reason": "exchange_adapter_not_implemented"}
