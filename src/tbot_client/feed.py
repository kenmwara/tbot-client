"""Long-poll the operator's signal feed and dispatch each signal to the router."""
from __future__ import annotations
import logging
from datetime import datetime, timezone

import requests

LOG = logging.getLogger("tbot_client.feed")


class FeedPoller:
    def __init__(self, cfg, router, state):
        self.cfg = cfg
        self.router = router
        self.state = state
        self._session = requests.Session()

    def tick(self) -> None:
        params = {
            "since": self.state.cursor(),
            "token": self.cfg.operator.subscriber_token,
            "limit": 50,
        }
        try:
            r = self._session.get(self.cfg.operator.feed_url, params=params, timeout=15)
        except requests.RequestException as e:
            LOG.warning("feed request failed: %s", e)
            return

        if r.status_code == 401:
            LOG.error("operator returned 401 — token revoked or invalid; stopping until restart")
            raise SystemExit(2)
        if r.status_code != 200:
            LOG.warning("feed returned HTTP %s: %s", r.status_code, r.text[:200])
            return

        try:
            body = r.json()
        except Exception:
            LOG.warning("feed body not JSON: %s", r.text[:200])
            return

        signals = body.get("signals") or []
        if not signals:
            LOG.debug("feed tick — no new signals (cursor=%s)", self.state.cursor()[:12] or "(none)")
            return

        LOG.info("feed tick — %d new signal(s)", len(signals))
        for sig in signals:
            sid = sig.get("signal_id")
            if not sid:
                continue
            if self.state.seen(sid):
                LOG.debug("dedup skip %s", sid[:12])
                self.state.advance_cursor(sid)
                continue
            if self._is_expired(sig):
                LOG.info("stale signal %s — skipping", sid[:12])
                self.router.callback(sig, "ack", decision="stale", reason="ttl_expired")
                self.state.mark_seen(sid)
                self.state.advance_cursor(sid)
                continue
            try:
                self.router.process(sig)
            except Exception as e:
                LOG.exception("router failure on %s: %s", sid[:12], e)
            finally:
                self.state.mark_seen(sid)
                self.state.advance_cursor(sid)

        self.state.save()

    def _is_expired(self, sig: dict) -> bool:
        exp = sig.get("expires_at")
        if not exp:
            return False
        try:
            dt = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
            return dt < datetime.now(timezone.utc)
        except Exception:
            return False
