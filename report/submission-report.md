# Heritage AI Studio Submission Report

## Status

The storyboard-driven pipeline and a local illustrated preview are implemented.
Live-action actor footage, audience testing, and production evidence have not
been supplied and are not claimed.

## Original work and implementation

See [CONTRIBUTIONS.md](../CONTRIBUTIONS.md) for the component map and
reproducibility instructions. This submission includes the Python pipeline, its
schema and tests, an original short-film screenplay and storyboard, and local
SVG/PNG illustration-generation scripts.

## Verification

- `python -m pytest -q`: 15 tests passed.
- `python -m pipeline.cli validate`: the approved storyboard passed validation.
- The locally assembled illustrated preview was inspected with `ffprobe` in
  both aspect ratios; each is 79 seconds with H.264 video, AAC audio, and an
  embedded subtitle track.

## Limitations

- The preview is an illustrated animatic with offline synthetic audio, not a
  live-action film with actors and recorded conversation.
- The default video, music, and narration providers are mocks. Cloudflare
  produces still images; Wan and ACE-Step require externally generated assets
  imported through the documented handoff.
- Provider credentials, current quotas, and production/API quality have not
  been verified here.
- No GitHub repository or remote URL is configured in this workspace. Add the
  actual public repository URL after creating and publishing the repository.
