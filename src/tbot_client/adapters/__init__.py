"""Broker adapters. Add one per broker; route via get_adapter()."""
from __future__ import annotations
import logging

from .dryrun import DryRunAdapter
from .kalshi import KalshiAdapter
from .oanda  import OandaAdapter
from .ibkr   import IbkrAdapter

LOG = logging.getLogger("tbot_client.adapters")


def get_adapter(surface_key: str, surface_cfg):
    """Return an adapter instance for this surface. Falls back to DryRun on error."""
    if surface_cfg.dry_run:
        LOG.info("surface %s in dry_run mode — using DryRunAdapter", surface_key)
        return DryRunAdapter(surface_cfg)

    broker_type = (surface_cfg.broker or {}).get("type", "").lower()
    try:
        if broker_type == "kalshi":
            return KalshiAdapter(surface_cfg)
        if broker_type == "oanda":
            return OandaAdapter(surface_cfg)
        if broker_type == "ibkr":
            return IbkrAdapter(surface_cfg)
    except Exception as e:
        LOG.error("adapter %s init failed (%s) — falling back to DryRun", broker_type, e)
        return DryRunAdapter(surface_cfg)

    LOG.error("unknown broker type %r for %s — falling back to DryRun", broker_type, surface_key)
    return DryRunAdapter(surface_cfg)
