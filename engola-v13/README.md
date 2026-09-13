# Engola v0.13 — Knowledge Acquisition + Telegram Archive + Media Recovery

This patch is designed for the current v0.12 architecture.

## What it adds
- External text import into the Knowledge Vault from Termux.
- Telegram document archiving without adding a Telegram SDK dependency.
- Metadata for category, authority, SHA-256 and Telegram message/file IDs.
- Restored YouTube media endpoint with watch/Shorts/embed/live URL parsing and privacy-enhanced embed.
- Transcript-first Study & Learn that does not claim audiovisual viewing.
- A Termux acquisition helper for public PDFs/web pages/text.

## Railway environment variables
Set these as Railway secrets (never put them in browser code):
- `ENGOLA_INGEST_TOKEN` — long random token for Termux -> Engola knowledge import.
- `ENGOLA_TELEGRAM_BOT_TOKEN` — optional Telegram bot token.
- `ENGOLA_TELEGRAM_CHAT_ID` — optional private archive chat/channel ID.

`ENGOLA_TELEGRAM_BOT_TOKEN` and `ENGOLA_TELEGRAM_CHAT_ID` are only needed on the Termux machine for archiving; do not expose them to the frontend.

## Termux setup
Copy `tools/engola_knowledge.py` and `tools/archive.py` to `~/` or `~/engola-tools/`.

Example environment:
```bash
export ENGOLA_URL="https://calm-perfection-production-faba.up.railway.app"
export ENGOLA_INGEST_TOKEN="<same secret configured on Railway>"
export ENGOLA_TELEGRAM_BOT_TOKEN="<Telegram bot token>"
export ENGOLA_TELEGRAM_CHAT_ID="<private archive chat/channel id>"
```

Then:
```bash
python ~/engola_knowledge.py "https://example.org/document.pdf" --title "Example document" --category accounting --authority official --archive
```

The script downloads the original to the phone, hashes it, optionally sends it to Telegram, extracts text, and sends only metadata + extracted text to Engola. Railway does not need to keep the original PDF.

## Important
The current Knowledge Vault remains SQLite-backed. This patch is an external archive/ingestion bridge, not yet a full semantic/vector database. That is intentional; semantic retrieval is the next intelligence-layer improvement.
