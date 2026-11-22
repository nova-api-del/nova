# Nova media sources and AI fallback

Nova tries sources in this order for each scene:

1. NASA Image and Video Library — public search API, no API key. NASA media usage guidance still applies; third-party material may have separate rights.
2. Pixabay Video API — free API access, requires `PIXABAY_API_KEY`. Downloaded clips are checked with ffprobe. Follow Pixabay Content License and API display/attribution rules.
3. Pexels Video API — free API access when a key is available, requires `PEXELS_API_KEY`. New API key issuance may be paused; this source is optional. Follow Pexels API terms and credit contributors.
4. Internet Archive — no API key. Nova accepts only items whose metadata clearly identifies a reusable CC BY, CC BY-SA, or public-domain/CC0 license. Items with NC/ND or unclear rights are skipped.
5. Wikimedia Commons — no API key. Each file's license and creator credit are recorded in the output metadata.

## Optional AI-generated scenes

If all video sources fail for a scene, Nova can request an AI-generated documentary-style image from Pollinations and animate it with a slow FFmpeg camera move. This is not a generated video clip. It is limited to two scenes per Short, and the quality gate still requires at least three distinct real video clips.

Set the GitHub Actions repository secret `POLLINATIONS_API_KEY` to enable this fallback. The provider's current API requires authentication; model availability and pricing/credits can change, so do not assume it is unlimited or free. Optionally set repository variable `POLLINATIONS_IMAGE_MODEL`; default: `black-forest-labs/flux.1-schnell`.

## GitHub Actions secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret** and add any keys you already have:

- `PIXABAY_API_KEY` — optional; Pixabay's API key is free to request.
- `PEXELS_API_KEY` — optional; free API, but new key issuance may currently be paused.
- `POLLINATIONS_API_KEY` — optional; enables AI-image fallback, subject to provider terms and current credits/pricing.

No key is required for NASA, Wikimedia Commons, or Internet Archive. Never put API keys directly in source files or commit them to Git.

## Quality rules

- No text-card or blank-background fallback.
- Every scene must be a distinct moving scene.
- At least three distinct real video sources are required.
- At most two AI-generated stills may be animated into moving scenes.
- Source URL, source/provider, license information, and attribution are retained in each Short's JSON metadata.
- Missing/invalid downloads are rejected before editing.

## No YouTube downloads

Nova no longer downloads footage from YouTube (no `yt-dlp`, no `YOUTUBE_COOKIES` secret). Reusing other creators' videos violates YouTube's terms, risks copyright strikes, and makes a channel ineligible for monetization ("reused content"). `cinematic_shorts.py` now uses licensed sources only: NASA, Pixabay, Pexels, Internet Archive (CC/PD only) and Wikimedia Commons. If no licensed video exists for a scene, up to two scenes per Short may use a licensed still image with a camera move; otherwise the build fails instead of using unlicensed material.

The `YOUTUBE_COOKIES` secret is no longer used. You can delete it from Settings → Secrets and variables → Actions.
