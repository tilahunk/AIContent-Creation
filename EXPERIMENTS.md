# Experiments

All entries pending until measurable execution.

| ID | Hypothesis | Change | Measurement | Result | Conclusion |
|---|---|---|---|---|---|
| E01 | Cache repeated keyframe generation | Historical claim: run keyframe stage twice unchanged | JSONL cache-hit records | Aggregate logs contain keyframe hits, but no run IDs to verify the exact two-run sequence | Cache hits are observed; the documented experiment is not independently reproducible |
| E02 | Single-shot isolation | Historical claim: run `--stage keyframes --shot shot_003` | Per-run shot records | Existing JSONL has no run IDs to isolate this execution | Targeted generation has a code path and test coverage; historical claim remains unverified |
| E03 | FFmpeg assembly in both aspect ratios | Existing exports inspected; updated assembly exercised with synthetic fixtures | ffprobe dimensions, duration, audio/subtitle streams | Prior exports measured 75 s at 1080x1920 and 1920x1080, but the end card was trimmed. A temporary 6 s fixture after the fix produced both ratios with audio and subtitle streams; full project rerun remains pending. | The FFmpeg graph works on a synthetic fixture; the existing full exports are previews and need regeneration |
| E04-E10 | PENDING | PENDING | PENDING | PENDING | PENDING |
| E11 | Narration-only changes should not invalidate keyframes | Change one shot's narration, then its image prompt | Fake-provider generation counts in `tests/test_cache.py` | The regression test confirms narration reuses the keyframe and changing the image prompt regenerates it | Image-stage cache inputs are separated from narration inputs |
