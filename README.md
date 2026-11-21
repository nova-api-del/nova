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


## Original AI-image long-form documentaries (no Pollinations key)

The long-form pipeline now uses **Tongyi-MAI/Z-Image-Turbo** directly through Diffusers on a free Kaggle GPU notebook. It does not use FLUX, Pollinations, or a paid image-generation API.

1. Open `notebooks/nova-z-image-turbo-kaggle.ipynb` in Kaggle (or import the notebook from this repository).
2. In Kaggle Notebook settings, enable **Internet** and select **GPU** under Accelerator. Free GPU availability and quotas are controlled by Kaggle; a queue may apply.
3. Run all cells. The notebook downloads the open Z-Image Turbo model, generates 15 original 1024×576 images, and creates `nova_ai_frames.zip`.
4. Download that ZIP and upload it to this repository at `input/ai_frames.zip` (create the `input` folder if needed).
5. The **Nova AI Image Documentary Render** workflow starts automatically. It creates the five-minute 1080p video, English voice-over, animated camera movement, and synchronized coloured captions. Download the MP4 from the workflow Artifacts.

The Kaggle GPU stage is the only step that needs a GPU. GitHub Actions performs the final video assembly on a CPU runner. No API key or paid API is required; Kaggle's free GPU quota and availability are not guaranteed. The render workflow refuses to substitute stock images: it verifies that all 15 scenes came from Z-Image Turbo.
