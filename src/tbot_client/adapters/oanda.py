"""OANDA adapter — STUB with most plumbing done.

Translation from operator signal to OANDA market order:

  signal.market_id  → "EUR_USD" (already OANDA-format)
  signal.direction  → "BUY" or "SELL" (operator emits these literal strings for FX)
  size_usd          → units. For non-JPY USD-base pairs roughly: units = size_usd
                       For accurate sizing use account-currency conversion.
  signal.metadata   → {stop_loss, take_profit, atr, eta_hours}

OANDA REST: POST {host}/v3/accounts/{account_id}/orders
  body = {"order": {"type": "MARKET", "instrument": "EUR_USD",
                    "units": str(signed_units),
                    "stopLossOnFill":   {"price": "1.0900"},
                    "takeProfitOnFill": {"price": "1.0950"}}}

Recommend the oandapyV20 SDK (pip install oandapyV20).
"""
from __future__ import annotations
import logging

from .base import BaseAdapter

LOG = logging.getLogger("tbot_client.adapters.oanda")


class OandaAdapter(BaseAdapter):
    def __init__(self, surface_cfg):
        super().__init__(surface_cfg)
        broker = surface_cfg.broker
        self.account_id = broker.get("account_id")
        self.api_token  = broker.get("api_token")
        self.practice   = broker.get("practice", True)
        if not (self.account_id and self.api_token):
            raise ValueError("oanda adapter: account_id and api_token required")
        self.host = "https://api-fxpractice.oanda.com" if self.practice \
                    else "https://api-fxtrade.oanda.com"
        LOG.warning("OandaAdapter is a STUB — implement order placement against %s", self.host)

    def place_order(self, signal: dict, size_usd: float) -> dict:
        LOG.error("OandaAdapter.place_order not yet implemented — signal %s",
                  signal.get("signal_id", "?")[:12])
        return {"filled": False, "reason": "oanda_adapter_not_implemented"}
