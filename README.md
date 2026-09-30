# budilnik

Small VPS alarm for the Binance Futures **CRCLUSDT** mark price.

Defaults:

- high trigger: price **> 88**
- low trigger: price **< 76**
- MacroDroid webhook repeats every 60 seconds while price remains outside the safe range
- when price returns to 76..88, the alarm state resets
- websocket watchdog: 15 seconds
- reconnect delay: 5 seconds

The MacroDroid webhook is **not stored in Git**. Put it in `/etc/budilnik.env` on the server.

## Environment

Required:

```bash
MACRODROID_WEBHOOK=https://trigger.macrodroid.com/...
```

Optional overrides:

```bash
SYMBOL=CRCLUSDT
LOW_PRICE=76
HIGH_PRICE=88
ALARM_REPEAT_SECONDS=60
MESSAGE_TIMEOUT=15
RECONNECT_DELAY=5
```

## Update deployed code

```bash
cd /opt/budilnik
sudo -u budilnik git pull --ff-only
sudo systemctl restart budilnik
sudo journalctl -u budilnik -f
```
