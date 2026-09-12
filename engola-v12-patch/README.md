# Engola v0.12 — Android Device Companion

Free-first, owner-controlled device telemetry bridge for Termux/Android.

## What it adds
- One-time owner-generated pairing code (10 minute expiry, single use)
- Hashed device tokens stored server-side
- Outbound-only companion heartbeat
- Battery, charging, Wi-Fi name/type, storage, Android model/version telemetry
- Device page in the existing Engola UI
- No remote device commands in v0.12

## Termux companion
The companion uses only Python standard library plus optional Termux:API commands. Official Termux:API provides commands such as `termux-battery-status` and `termux-wifi-connectioninfo`.

Install the Termux package when ready:
`pkg install termux-api`

Then copy `tools/engola_companion.py` to `~/engola_companion.py`.

From Engola's Device page, generate a code and run:
`ENGOLA_URL="https://your-engola.up.railway.app" ENGOLA_PAIR_CODE="ABCDEFGH" python ~/engola_companion.py`

The token is saved as `~/.engola-companion.json` with mode 0600 where supported.
