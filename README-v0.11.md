# Engola v0.11 patch — Free-first Knowledge & Research

This patch adds a production-oriented Research Vault without requiring paid AI tokens:

- Public webpage ingestion with SSRF protections.
- PDF text extraction using pure-Python `pypdf`.
- YouTube transcript ingestion using `youtube-transcript-api` (manual or generated captions when available).
- Private SQLite knowledge vault + keyword search.
- Wikipedia search through the public MediaWiki API.
- A new Research surface injected into the existing UI without replacing the working v0.10 frontend.
- A visual polish stylesheet that makes the existing dashboard feel more deliberate and product-designed.

The patch intentionally does **not** pretend to have email, browser automation, GitHub control, device control, or paid-model reasoning until those integrations are actually connected.

Research basis: YouTube transcript API is keyless and supports auto-generated subtitles; yt-dlp also supports writing subtitles/automatic subtitles. OpenStreetMap/Nominatim and Overpass are viable free map data sources but have strict rate/usage policies, so they should be cached and rate-limited. Telegram can be added later as an optional archive connector; BotFather tokens must remain secret.
