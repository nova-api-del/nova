# Nova hybrid video factory

Nova now uses a **real-footage-first** production strategy:
- NASA / Wikimedia / Internet Archive footage
- optional Pixabay / Pexels when keys exist
- optional AI-generated moving scenes through Wan2.1
- FFmpeg vertical assembly, English TTS and captions
- Quality Gate before publishing

## AI backend

The repository includes `scripts/wan2x_ai.py` and a separate
`Nova AI GPU Worker` workflow. Wan2.1 T2V-1.3B is Apache-2.0 and is the
smallest official Wan2.1 text-to-video model. It needs a CUDA/NVIDIA GPU;
GitHub-hosted free runners do not provide that GPU, so the normal free
workflow remains real-footage-first instead of silently producing a broken
video.

When a free/owned GPU runner is connected, the AI worker can generate short
moving scenes and Nova can use them as up to two fallback scenes.

Source: https://github.com/Wan-Video/Wan2.1
