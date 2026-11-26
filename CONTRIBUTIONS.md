# Project implementation and contribution summary

## Project

AI-Powered Heritage Short Film Generation Studio is a Python pipeline that
validates a structured storyboard, generates or imports per-shot media, and
assembles short-film exports with FFmpeg. The approved `storyboard.json` is the
source of truth for the pipeline.

## Implementation

1. `schema/storyboard.schema.json` defines the accepted project, character,
   shot, audio, and end-card data.
2. `pipeline/validator.py` checks the JSON schema, shot-duration sum, unique shot
   IDs, and final runtime.
3. `pipeline/orchestrator.py` coordinates keyframes, shots, music, narration,
   subtitles, and assembly. `pipeline/cache.py` keys reusable outputs by content.
4. `pipeline/providers/` contains the mock, Cloudflare, Gemini, Wan, and
   ACE-Step adapters. Cloudflare handles still images. Wan and ACE-Step import
   outputs created through the documented external GPU handoff; the local CLI
   does not run those models.
5. `pipeline/stages/` implements each media stage. `pipeline/stages/assemble.py`
   uses FFmpeg to produce vertical and horizontal H.264/AAC MP4s with an
   embedded English subtitle track.
6. `tests/` covers storyboard validation, provider behavior, caching, stage
   orchestration, narration, and assembly.

## Original creative and technical deliverables

The `outputs/script/` source files in this submission include:

- An original English screenplay and a dialogue-led live-action production brief
  for **The Next Page**, set in a fictional contemporary Addis Ababa neighborhood.
- A schema-valid, eight-shot storyboard proposal with Ethiopian woven-cloth
  wardrobe direction and English subtitle text.
- `render_illustrations.py`, which creates original local SVG/PNG illustrated
  frames using hand-authored vector shapes and textile patterns.
- `generate_offline_narration.ps1`, which creates local English narration WAVs
  with the installed Windows Speech API.
- `build_illustrated_film.py`, which uses the project's FFmpeg pipeline to
  assemble the illustrated preview with an original locally synthesized score
  and the offline narration WAVs.

Generated media is intentionally excluded from source control. The local
illustrated preview is not live-action footage and does not contain filmed
actors. The production brief is an instruction for a separate video-generation
agent; it is not itself a video generator.

## Validation evidence

- `python -m pytest -q`: 15 tests passed in the local environment.
- `python -m pipeline.cli validate`: approved storyboard validated with 8 shots.
- The illustrated preview was checked with `ffprobe`: both 16:9 and 9:16
  exports are 79 seconds and contain H.264 video, AAC audio, and an embedded
  subtitle stream.

These checks do not establish audience response, live-action production quality,
or successful external API credentials.

## Reproduce the source pipeline

Install dependencies and FFmpeg as described in `README.md`, then run:

```powershell
python -m pipeline.cli validate
python -m pytest -q
python -m pipeline.cli run
```

By default, the media providers are mocks. Configure providers and supply the
required imported Wan/ACE-Step assets before describing any output as
model-generated. The original illustrated preview can be regenerated on Windows
with Chrome or Edge, FFmpeg, and the installed Microsoft Speech voices:

```powershell
python outputs\script\render_illustrations.py
.\outputs\script\generate_offline_narration.ps1
```

Then assemble the illustrated preview:

```powershell
python outputs\script\build_illustrated_film.py
```

The workspace has not yet been published to GitHub. Create the repository and
add its actual URL here before submission; do not invent a repository link.

## Publishing and security

`.env` is ignored and must never be committed. Use `.env.example` for blank
configuration names. The local cache, run log, generated MP4/WAV/PNG/SVG media,
and build outputs are also excluded. Review staged files before pushing and
rotate any credential that has been exposed.
