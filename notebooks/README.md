# Nova AI documentary — free Kaggle GPU path

The notebook `nova-z-image-turbo-kaggle.ipynb` now does the complete pipeline:

1. Loads the open-weight **Tongyi-MAI/Z-Image-Turbo** image model (no FLUX, no Pollinations key).
2. Generates 15 original scene images.
3. Uses the Nova renderer and FFmpeg to create a 1080p documentary with English narration and synchronized captions.
4. Exposes the MP4 as a notebook download link.

## Run
- Open the notebook in GitHub and download the `.ipynb`, then import/upload it into Kaggle.
- In Kaggle Notebook settings choose **GPU** accelerator and turn **Internet** on.
- Run all cells in order.
- Download `nova_five_minute_documentary.mp4` from the final cell's file link or Kaggle output files.

Kaggle's free GPU availability and quota are limited and controlled by Kaggle. The first run downloads the model weights. No API key is required. The notebook generates and renders inside Kaggle; GitHub Actions' standard CPU runner cannot run this image model at no cost.
