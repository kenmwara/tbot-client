"""IBKR adapter — STUB.

Two implementation paths:

1. **ibeam (recommended)**: run ibeam locally, point gateway_url at http://localhost:5000/v1/api.
   POST /v1/api/iserver/account/{accountId}/orders with a bracket order spec.
   See operator's /root/st-trading-bot/agents/_ibkr.py for working examples.

2. **ibapi direct**: heavier, requires TWS or Gateway running with API enabled.
   Use the ibapi package and the EClient/EWrapper pattern.

For most subscribers ibeam is simpler — it handles session keepalive and 2FA flows.
"""
from __future__ import annotations
import logging

from .base import BaseAdapter

LOG = logging.getLogger("tbot_client.adapters.ibkr")


class IbkrAdapter(BaseAdapter):
    def __init__(self, surface_cfg):
        super().__init__(surface_cfg)
        broker = surface_cfg.broker
        self.gateway_url = broker.get("gateway_url", "http://localhost:5000/v1/api")
        self.account_id  = broker.get("account_id")
        if not self.account_id:
            raise ValueError("ibkr adapter: account_id required")
        LOG.warning("IbkrAdapter is a STUB — implement bracket order placement via %s", self.gateway_url)

    def place_order(self, signal: dict, size_usd: float) -> dict:
        LOG.error("IbkrAdapter.place_order not yet implemented — signal %s",
                  signal.get("signal_id", "?")[:12])
        return {"filled": False, "reason": "ibkr_adapter_not_implemented"}
