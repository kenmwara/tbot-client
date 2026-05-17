"""Adapter contract. Subclass for each broker."""
from __future__ import annotations
from typing import Optional


class BaseAdapter:
    """Each adapter takes a SurfaceConfig and exposes place_order(signal, size_usd).

    Return dict shape (success):
        {"filled": True, "fill_price": 1.0950, "contracts": 100, "broker_order_id": "abc"}

    Return dict shape (failure):
        {"filled": False, "reason": "rejected: insufficient_funds"}
    """

    def __init__(self, surface_cfg):
        self.cfg = surface_cfg

    def place_order(self, signal: dict, size_usd: float) -> dict:
        raise NotImplementedError("subclass must implement place_order")
