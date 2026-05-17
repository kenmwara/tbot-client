"""Local persistent state: feed cursor, per-surface open positions, HWM."""
from __future__ import annotations
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List

LOG = logging.getLogger("tbot_client.state")


class LocalState:
    """Single-writer JSON-backed state. Not concurrent — one client process per machine."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._data = {
            "feed_cursor":      "",       # last signal_id we processed
            "open_positions":   {},       # surface -> [signal_id, ...]
            "high_water_marks": {},       # surface -> float
            "processed_signals": [],      # rolling list of recent ids (dedup)
            "executed_count":   0,
            "ack_count":        0,
            "resolved_count":   0,
        }
        if path.exists():
            try:
                self._data.update(json.loads(path.read_text()))
                LOG.info("loaded state from %s — cursor=%s, open_positions=%s",
                         path, self._data["feed_cursor"][:12] or "(none)",
                         {k: len(v) for k,v in self._data["open_positions"].items()})
            except Exception as e:
                LOG.warning("state file unreadable, starting fresh: %s", e)

    def save(self) -> None:
        with self._lock:
            try:
                self.path.write_text(json.dumps(self._data, indent=2, default=str))
            except Exception as e:
                LOG.error("state save failed: %s", e)

    # ── Cursor ─────────────────────────────────────────────────────────
    def cursor(self) -> str:
        return self._data["feed_cursor"]

    def advance_cursor(self, signal_id: str) -> None:
        with self._lock:
            self._data["feed_cursor"] = signal_id

    # ── Dedup ──────────────────────────────────────────────────────────
    def seen(self, signal_id: str) -> bool:
        return signal_id in self._data["processed_signals"]

    def mark_seen(self, signal_id: str, max_keep: int = 1000) -> None:
        with self._lock:
            pl = self._data["processed_signals"]
            if signal_id not in pl:
                pl.append(signal_id)
            if len(pl) > max_keep:
                self._data["processed_signals"] = pl[-max_keep:]

    # ── Open positions ─────────────────────────────────────────────────
    def open_count(self, surface: str) -> int:
        return len(self._data["open_positions"].get(surface, []))

    def add_open(self, surface: str, signal_id: str) -> None:
        with self._lock:
            self._data["open_positions"].setdefault(surface, []).append(signal_id)

    def remove_open(self, surface: str, signal_id: str) -> None:
        with self._lock:
            lst = self._data["open_positions"].get(surface, [])
            if signal_id in lst:
                lst.remove(signal_id)

    # ── Counters ───────────────────────────────────────────────────────
    def bump(self, key: str) -> None:
        with self._lock:
            self._data[key] = self._data.get(key, 0) + 1
