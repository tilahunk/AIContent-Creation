# Failures

This journal records actual failures only.

| Date | Stage | Error | Root cause | Resolution | Limitation |
|---|---|---|---|---|---|
| 2026-11-26 | Environment | `ffmpeg` and `python` were initially absent or redirected to Windows aliases | Runtime not configured | Installed Python 3.12 and FFmpeg with winget | New terminals may need PATH refresh |
| 2026-11-26 | Assembly end card | FFmpeg drawtext returned exit status 3221225477 | The winget FFmpeg build crashed while resolving text rendering | Replaced end card text rendering with a pure-bitmap PPM image | The end card is verified as visible bitmap text in mock output |
| 2026-11-26 | Subtitle burn-in | The subtitles filter could not complete in this FFmpeg environment | Subtitle renderer/filter dependencies unavailable | Embedded English SRT as an MP4 subtitle track; retained standalone SRT | Hard-burned subtitles remain pending a compatible FFmpeg/subtitle renderer |
| 2026-11-26 | Cloud model execution | No provider request was attempted during the earlier implementation update | External provider access was not verified at that time | Implemented provider selection and explicit mock fallbacks | External model access, current quota, and Amharic voice quality remain unverified |
| 2026-11-26 | Assembly audio mix | FFmpeg rejected a reused narration filter output label when it was consumed by both sidechain compression and the final mix | A labelled FFmpeg audio stream can only be consumed once without splitting it | Split the voice stream for the sidechain and mix branches; verified both aspect-ratio exports with a temporary synthetic fixture | Full project re-export with real model assets remains pending |
