# Architecture

`storyboard.json` is validated against JSON Schema before execution. The orchestrator dispatches independent stages. The screenplay mode writes and validates `outputs/script/storyboard-proposal.json`; it never overwrites the approved storyboard.

1. keyframes: composed style/character/image prompt and model hash
2. shots: keyframe file content, motion prompt, duration, and model hash
3. music: style, duration, per-shot music cues, and model hash
4. narration: text, language, duration, model, and configured voice
5. assembly: content hashes of all required media inputs, storyboard audio/end-card settings, aspect ratios, and export format

Provider adapters implement `Provider.generate`. Provider selection is stage-specific via environment settings. `CloudflareProvider` handles image inference; `GeminiProvider` handles text proposals and TTS. Kaggle's Wan and ACE-Step workflows are exported/imported through explicit file handoffs and do not claim remote execution from the local CLI. The mock adapter requires no quota and verifies orchestration and FFmpeg assembly.

The character reference image is generated and stored but is not supplied as an image-conditioning input to the current Cloudflare text-to-image adapter, so character identity is not guaranteed. The Wan adapter copies manually generated clips; it does not invoke a model or consume the motion prompt itself.

Provider errors are written to `runs.jsonl`. Image, music, narration, and video stages may then create an explicitly labeled local preview fallback; fallback outputs are not cached under the real provider's success key. Successful outputs are content-cached using model IDs and stage inputs. Assembly reuses exports only when every required input hash and output file matches; `--force` bypasses that cache.

Assembly appends the configured end card after the shot program. It mixes the narration clips at their shot offsets with background music, uses sidechain compression when `music_ducking` is enabled, and applies FFmpeg `loudnorm` targeting -14 LUFS/-1 dBTP. English captions are generated from Gemini when selected, read from per-shot `subtitle_en` values when authored, or explicitly marked pending in mock previews. MP4 exports carry an embedded `mov_text` subtitle stream.

## Privacy and free-tier terms

Credentials are read from environment variables, never logged. Requests to Google and Cloudflare send storyboard prompts/text to those services. Google AI Studio's free-tier page states that submitted content may be used to improve products. The project owner must review current terms and consent before using personal content.
