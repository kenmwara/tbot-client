# tbot-client

A small program a subscriber runs on their own computer. It picks up T BOT's trade ideas, sizes each one to the subscriber's own settings, and places it on **their own** broker account.

T BOT operator never touches your funds, never sees your broker credentials, and never executes trades on your behalf. This client is what does the work on your machine.

---

<img src="images/flow.png" width="100%" alt="How it works, in five steps. 1. Check for trade ideas: Every 30 seconds, using the subscriber's own pass. 2. Skip the unsafe ones: Too old (over 10 minutes), too big, or below the broker's minimum. 3. Size the trade: A set share of the subscriber's own money. 4. Trade on their own account: With their own broker; a practice mode logs everything without trading. 5. Report back: Only what happened is sent back, never passwords or keys. Safeguards: Your keys: Login details never leave the subscriber's computer; Safety: Old or oversized trades are skipped; Try it first: Practice mode places nothing.">

## What it does

1. **Polls** `/api/signals/feed` every 30 seconds using your subscriber token.
2. For each new signal:
   - Computes your dollar size: `your_bankroll × signal.kelly_size_pct`.
   - Routes to the appropriate broker adapter (exchange / OANDA / IBKR), if you've enabled that surface.
   - Places the order with the same direction + size as the signal.
   - POSTs an `ack` callback with `accepted` / `filtered` / `stale`.
   - If filled, POSTs `executed` with your fill price + size.
   - On position close, POSTs `resolved` with your realized P&L.
3. Skips signals where:
   - Surface is disabled in your config.
   - You're at your concurrent-positions cap for that surface.
   - The signal is past its 600-second TTL.
   - Your bankroll is below the broker's minimum order size.

## Architecture

<img src="images/architecture.png" width="100%" alt="Architecture diagram of tbot-client. On the subscriber's own machine (Python, under systemd or pm2): feed.py polls the operator's signal feed every 30 seconds with the subscriber's token; router.py skips a signal if its surface is off, the position cap is reached, it is older than 600 seconds or the bankroll is below the broker minimum, then sizes it as bankroll times the signal's suggested share; dry-run mode logs every decision without placing an order. config.yaml holds the broker credentials and never leaves the machine; broker adapters for the exchange, OANDA, IBKR and dry-run place orders straight on the subscriber's own accounts; ~/.tbot/ keeps the decision log and state. Only acks, fills and results go back to the operator at ops.tbot.trade, never keys.">

---

## Install

```bash
git clone https://github.com/kenmwara/tbot-client.git
cd tbot-client
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml — paste your subscriber token, choose surfaces, enter broker creds
python -m tbot_client
```

Recommend running under `systemd` or `pm2` for production. See `deploy/` for sample unit files.

## Configuration

See `config.example.yaml` for the full schema. Minimal valid config:

```yaml
operator:
  feed_url: "https://ops.tbot.trade/api/signals/feed"
  subscriber_token: "tbot_..."     # from your welcome email

surfaces:
  forex:
    enabled: true
    bankroll: 1000.0
    broker: oanda
    oanda:
      account_id: "001-001-12345-001"
      api_token: "..."             # your own OANDA token
      practice: true               # start in OANDA practice mode

  exchange_st:
    enabled: false                 # opt in by setting true
  exchange_lt:
    enabled: false
  stocks:
    enabled: false
```

## Dry-run mode

Set `dry_run: true` at any surface level (or globally under `runtime:`) to log signals without placing orders. Recommended for the first 24-48 hours so you can verify routing before risking real money.

## Logs

- `~/.tbot/client.log` — verbose decision trace (chatty by design)
- `~/.tbot/state.json` — local high-water marks + concurrent-position tracker

## Failure modes

<img src="images/client-failures.png" width="100%" alt="Five problems a subscriber can hit, and what to do. What you see: The trade-idea feed refuses the login (HTTP 401). Likely cause: The operator switched off this subscriber's pass. What to do: Email the operator. What you see: The broker refuses the login (HTTP 401). Likely cause: The broker's login has expired. What to do: Renew it on the broker's site, then update the settings file. What you see: Trade ideas keep coming back as 'stale'. Likely cause: The computer's clock is off, or the network is slow. What to do: Check the clock (date -u), and check for new ideas more often. What you see: 'insufficient_funds'. Likely cause: Less money in that account than the broker's minimum trade. What to do: Top up that broker account. What you see: Ideas arrive but nothing trades. Likely cause: Practice mode is on somewhere, or that market is switched off. What to do: Check the settings file.">

<details><summary>The same, as a table</summary>

| Symptom | Likely cause | What to do |
|---|---|---|
| HTTP 401 from feed | Token revoked by operator | Email operator |
| HTTP 401 from broker | Broker token expired | Renew on your broker's site, update config |
| `"reason": "stale"` ack repeatedly | Client clock out of sync OR network slow | Check `date -u`; reduce poll interval |
| `"reason": "insufficient_funds"` | Surface bankroll < broker minimum | Top up that broker account |
| Signals received but never executed | `dry_run: true` somewhere, or surface disabled | Check config |

</details>

## License

Provided as-is to T BOT beta subscribers. No warranty. Not investment advice. See `TBOT_TERM_SHEET_v2.md` (sent separately).
