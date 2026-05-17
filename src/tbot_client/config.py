"""Config loader with light validation. YAML in, dataclasses out."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class OperatorConfig:
    feed_url: str
    callback_base: str
    subscriber_token: str


@dataclass
class RuntimeConfig:
    poll_interval_seconds: int = 30
    dry_run: bool = False
    log_level: str = "INFO"
    state_dir: str = "~/.tbot"
    max_signal_age_seconds: int = 600


@dataclass
class SurfaceConfig:
    name: str
    enabled: bool = False
    bankroll: float = 0.0
    max_concurrent: int = 0
    dry_run: bool = False
    broker: dict = field(default_factory=dict)
    size_multiplier: float = 1.0


@dataclass
class ClientConfig:
    operator: OperatorConfig
    runtime: RuntimeConfig
    surfaces: dict   # name -> SurfaceConfig


def load_config(path: str) -> ClientConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    raw = yaml.safe_load(p.read_text())

    op = raw.get("operator") or {}
    if not op.get("subscriber_token") or "REPLACE_WITH" in op.get("subscriber_token", ""):
        raise ValueError("operator.subscriber_token is missing or unset")

    operator = OperatorConfig(
        feed_url        = op["feed_url"],
        callback_base   = op.get("callback_base") or op["feed_url"].rsplit("/api/", 1)[0],
        subscriber_token= op["subscriber_token"],
    )

    rt = raw.get("runtime") or {}
    runtime = RuntimeConfig(
        poll_interval_seconds  = int(rt.get("poll_interval_seconds", 30)),
        dry_run                = bool(rt.get("dry_run", False)),
        log_level              = str(rt.get("log_level", "INFO")),
        state_dir              = str(rt.get("state_dir", "~/.tbot")),
        max_signal_age_seconds = int(rt.get("max_signal_age_seconds", 600)),
    )

    size_mult = raw.get("size_multipliers") or {}
    surfaces = {}
    for name, sc in (raw.get("surfaces") or {}).items():
        sc = sc or {}
        surfaces[name] = SurfaceConfig(
            name           = name,
            enabled        = bool(sc.get("enabled", False)),
            bankroll       = float(sc.get("bankroll", 0.0)),
            max_concurrent = int(sc.get("max_concurrent", 0)),
            dry_run        = bool(sc.get("dry_run", False)) or runtime.dry_run,
            broker         = sc.get("broker") or {},
            size_multiplier= float(size_mult.get(name, 1.0)),
        )

    return ClientConfig(operator=operator, runtime=runtime, surfaces=surfaces)
