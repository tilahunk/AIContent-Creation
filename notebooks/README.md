# Kaggle GPU handoff

The local CLI does not start a Kaggle session or upload assets. Run the models in Kaggle, then download the results and point the local adapters at them.

## Wan 2.2 TI2V-5B

1. Generate keyframes locally and create a private Kaggle dataset containing `storyboard.json` and `outputs/keyframes/`.
2. Start a Kaggle Notebook with Internet enabled and GPU enabled. GPU model and quota depend on account availability; do not assume two T4s or a fixed weekly allowance.
3. Follow the [official Wan2.2 instructions](https://github.com/Wan-Video/Wan2.2/blob/main/README.md) to install, obtain the `Wan2.2-TI2V-5B` weights, and run image-to-video generation. The official documented TI2V-5B single-GPU command specifies at least 24 GB VRAM; a Kaggle GPU may not satisfy it.
4. Save each completed clip as `shot_001.mp4`, etc. in a results folder. Only copy successful outputs.
5. Download that folder and set `KAGGLE_WAN_OUTPUT_DIR` to it. Run `python -m pipeline.cli run --stage shots`.

## ACE-Step 1.5 music

1. Use the [official ACE-Step 1.5 project](https://ace-step.github.io/ace-step-v1.5.github.io/) in a Kaggle GPU Notebook. Follow its current installation and inference instructions; check the exact model-weight licence.
2. Generate an instrumental track using the `music_style` in `storyboard.json`, review it, and save the selected track as WAV.
3. Download it and set `ACE_STEP_OUTPUT` to the WAV path. Set `MUSIC_PROVIDER=ace-step`, then run `python -m pipeline.cli run --stage music`.

These are handoff instructions, not claims that a Kaggle job or model generation has already been executed. Keep the Kaggle dataset private if the storyboard, prompts, or images contain personal information.
