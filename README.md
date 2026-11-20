# Nova — Daily Shorts Automation

This repository generates one English vertical YouTube Short each day using Edge TTS (no paid voice API key), Pillow-generated visual cards, FFmpeg, and GitHub Actions. The scheduled build runs at 19:00 Asia/Baghdad.

## Run
Open **Actions → Nova Daily Short → Run workflow**. The MP4 and metadata are uploaded as a workflow artifact for 7 days.

## Publishing limitation
The workflow currently generates a Short; it does not publish it to YouTube or Metricool. A GitHub artifact is not a public media URL, and no YouTube OAuth or Metricool publishing credential is configured. Automatic publishing must be added and tested before claiming it is live.

## Content
The generator rotates through a small set of English educational scripts and original graphic cards. Expand `TOPICS` in `scripts/generate_short.py` to add topics. Verify factual claims before publication.


## Nova Shorts Factory (current pipeline)

The `Nova Shorts Factory` workflow builds six vertical videos, adds English voice-over and burned-in timed captions, validates the rendered video/audio streams, and uploads both workflow artifacts and downloadable GitHub Release assets. It rotates the topic set between days to reduce immediate repetition. Release assets can be used as public media URLs when scheduling through a connected publishing service.

The factory does **not** itself authenticate to YouTube or TikTok. Publishing is a separate step through the connected Metricool accounts or a properly configured platform API. Never store access tokens in source files; use repository Actions secrets.
