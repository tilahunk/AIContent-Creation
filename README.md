# AI-Powered Heritage Short Film Generation Studio

This repository turns `storyboard.json` into a reproducible 60–90 second heritage short film. The JSON is the source of truth, and every stage is cacheable and independently runnable.

See [CONTRIBUTIONS.md](./CONTRIBUTIONS.md) for the implementation map, original
creative/technical deliverables, verification evidence, current limitations, and
publishing guidance.

## Prerequisites

- Windows or Linux
- Python 3.11+
- FFmpeg
- Optional provider API credentials

## Install

```powershell
python -m pip install -r requirements.txt
copy .env.example .env
```

## Commands

```powershell
python -m pipeline.cli validate
python -m pipeline.cli run
python -m pipeline.cli run --stage keyframes
python -m pipeline.cli run --stage shots --shot shot_003
python -m pipeline.cli run --script path\to\screenplay.txt
python -m pipeline.cli run --force
python -m pipeline.cli status
make film
make test
```

The `make` commands require GNU Make. On Windows without it, use the equivalent `python -m pipeline.cli ...` commands above.

The mock provider is the default and creates preview assets plus a Ken Burns FFmpeg fallback. Providers are independently selectable per stage; see `.env.example`. The Google Gemini and Cloudflare adapters use their documented HTTP APIs. Wan 2.2 and ACE-Step use the provided Kaggle file handoff because the local CLI does not start GPU jobs.

The mock outputs are not genuine model-generated narration, music, or keyframes. Mock narration produces a tone, and mock subtitles are marked `[English translation pending]` unless `subtitle_en` is supplied in the storyboard. A real-provider error is logged and a labeled local preview fallback is used for supported stages. Check `runs.jsonl` and `FAILURES.md` before treating any output as model generated.

## Zero-cost provider route

1. Copy `.env.example` to `.env`.
2. Set `IMAGE_PROVIDER=cloudflare` and add a Workers AI account ID/token.
3. Set `NARRATION_PROVIDER=gemini` and add a Gemini API key.
4. Run `python -m pipeline.cli run --stage keyframes` and `... --stage narration`.
5. Run the Wan and ACE-Step notebooks under `notebooks/`; download the generated MP4/WAV files, set `KAGGLE_WAN_OUTPUT_DIR` and `ACE_STEP_OUTPUT`, then run the matching stages.

`python -m pipeline.cli run --stage script` writes an AI storyboard proposal to `outputs/script/storyboard-proposal.json`; it never overwrites the approved `storyboard.json`.

To turn a screenplay into a film, set `GEMINI_API_KEY` in your local `.env`, then run `python -m pipeline.cli run --script path\to\screenplay.txt`. The generated storyboard is schema-validated and saved as `outputs/script/storyboard-proposal.json`; the approved `storyboard.json` is not overwritten. The pipeline then runs the configured generation stages. For model-generated clips and music, configure their providers and provide the downloaded Wan/ACE-Step outputs as described in `notebooks/README.md`; otherwise the documented mock/local preview output may be used.

The storyboard's `project.duration_seconds` is the shot-program runtime. An enabled end card is appended to the exports, so the final runtime is the project duration plus the end-card duration (4 seconds by default). The validator rejects a resulting runtime above 90 seconds. Audio exports mix per-shot narration and music, apply sidechain ducking when enabled, and use FFmpeg loudness normalization targeting -14 LUFS and -1 dBTP.

Free access, quotas, model availability, country eligibility, and terms are not guaranteed. See the dated evidence and unresolved checks in `COSTS.md`. The Google free-tier terms currently state that content may be used to improve Google products; do not send personal or sensitive content without appropriate consent.

## Outputs

- `outputs/keyframes/`
- `outputs/shots/`
- `outputs/audio/`
- `outputs/subtitles/film-en.srt`
- `outputs/final/heritage-vertical.mp4`
- `outputs/final/heritage-horizontal.mp4`

Final MP4s include an embedded English subtitle track. With a real Gemini narration provider, English subtitles are translated from each narration line; otherwise provide `subtitle_en` per shot or treat the marked pending-subtitle preview as unfinished.

## Configuration

Copy `.env.example` to `.env`. API keys must remain environment variables and must never be committed.

## Incremental regeneration

Outputs are keyed by content hashes. Changing a shot invalidates its keyframe and dependent video. Narration and music use separate hashes. `--force` deliberately regenerates all selected work.

## Current showcase

The original **The Next Page** screenplay, storyboard proposal, and live-action
agent brief are in `outputs/script/`. The locally rendered preview is an
illustrated animatic, not live-action actor footage. Generated media is excluded
from Git; use a release or another approved media host if the final MP4s must be
available alongside a public repository.
