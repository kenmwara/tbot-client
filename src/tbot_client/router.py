"""Decides which surface a signal belongs to and dispatches to the right adapter."""
from __future__ import annotations
import logging
from typing import Optional

import requests

from .adapters import get_adapter

LOG = logging.getLogger("tbot_client.router")


# Operator's `surface` field -> subscriber config key
SURFACE_MAP = {
    "ST":  "kalshi_st",
    "LT":  "kalshi_lt",
    "FX":  "forex",
    "STK": "stocks",
}


class SignalRouter:
    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self._adapters = {}   # surface_key -> Adapter instance
        self._session = requests.Session()

    def _adapter_for(self, surface_key: str):
        if surface_key not in self._adapters:
            sc = self.cfg.surfaces.get(surface_key)
            if not sc:
                return None
            self._adapters[surface_key] = get_adapter(surface_key, sc)
        return self._adapters[surface_key]

    def process(self, sig: dict) -> None:
        sid     = sig.get("signal_id", "?")
        surface = sig.get("surface", "?")
        surface_key = SURFACE_MAP.get(surface)
        if not surface_key:
            LOG.info("skip %s — unknown surface %r", sid[:12], surface)
            self.callback(sig, "ack", decision="filtered", reason=f"unknown_surface:{surface}")
            return

        sc = self.cfg.surfaces.get(surface_key)
        if not sc or not sc.enabled:
            LOG.info("skip %s — surface %s disabled in config", sid[:12], surface_key)
            self.callback(sig, "ack", decision="filtered", reason="surface_disabled")
            return

        if self.state.open_count(surface_key) >= sc.max_concurrent:
            LOG.info("skip %s — %s at concurrent cap (%d)", sid[:12], surface_key, sc.max_concurrent)
            self.callback(sig, "ack", decision="filtered", reason="local_concurrent_cap")
            return

        # Sizing: verbatim Kelly% × bankroll × per-surface multiplier
        kelly_pct = float(sig.get("kelly_size_pct") or 0)
        size_usd  = round(sc.bankroll * kelly_pct * sc.size_multiplier, 2)
        if size_usd <= 0:
            LOG.info("skip %s — computed size 0 (kelly=%.4f, bankroll=%.2f)",
                     sid[:12], kelly_pct, sc.bankroll)
            self.callback(sig, "ack", decision="filtered", reason="size_zero")
            return

        # Ack accepted BEFORE placing — operator sees we received it
        self.callback(sig, "ack", decision="accepted")

        adapter = self._adapter_for(surface_key)
        if adapter is None:
            LOG.error("no adapter for %s", surface_key)
            return

        try:
            result = adapter.place_order(sig, size_usd)
        except Exception as e:
            LOG.exception("adapter %s.place_order failed: %s", surface_key, e)
            return

        if result and result.get("filled"):
            self.state.add_open(surface_key, sig["signal_id"])
            self.state.bump("executed_count")
            self.callback(sig, "executed",
                          fill_price=result.get("fill_price"),
                          size_usd=size_usd,
                          contracts=result.get("contracts"),
                          broker_order_id=result.get("broker_order_id"),
                          bankroll_pct=round(size_usd / sc.bankroll, 4))
            LOG.info("EXEC %s %s @ %s  size=$%.2f", sid[:12], surface_key,
                     result.get("fill_price"), size_usd)
        else:
            reason = (result or {}).get("reason", "unknown_failure")
            LOG.warning("FAIL %s %s — %s", sid[:12], surface_key, reason)
            self.callback(sig, "ack", decision="filtered", reason=reason)

    def callback(self, sig: dict, event: str, **kwargs) -> None:
        """Fire-and-forget callback to operator's /api/signals/{id}/{event}."""
        sid = sig.get("signal_id")
        if not sid:
            return
        url  = f"{self.cfg.operator.callback_base}/api/signals/{sid}/{event}"
        body = {"token": self.cfg.operator.subscriber_token, **kwargs}
        try:
            self._session.post(url, json=body, timeout=10)
            if event == "ack":
                self.state.bump("ack_count")
            elif event == "resolved":
                self.state.bump("resolved_count")
        except Exception as e:
            LOG.warning("callback %s for %s failed: %s", event, sid[:12], e)
