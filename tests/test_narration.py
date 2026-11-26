from pathlib import Path

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.stages.narration import generate_narration


def test_single_shot_rerun_keeps_full_subtitle_timeline(tmp_path):
    class PreviewProvider:
        provider_name = "mock"

        def __init__(self):
            self.requests = []

        def model_for(self, _kind):
            return f"mock-preview-{_kind}"

        def generate(self, request):
            self.requests.append(request)
            output = Path(request["output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"preview-audio")
            return str(output)

    storyboard = {
        "project": {
            "language": "am",
            "subtitle_language": "en",
        },
        "audio": {"narration_enabled": True},
        "shots": [
            {
                "id": "shot_001",
                "duration_seconds": 8,
                "narration": "line one",
                "subtitle_en": "Authored translation.",
            },
            {
                "id": "shot_002",
                "duration_seconds": 8,
                "narration": "line two",
            },
        ],
    }
    provider = PreviewProvider()
    outputs = generate_narration(
        tmp_path, storyboard, provider, ContentCache(tmp_path),
        RunLogger(tmp_path / "runs.jsonl"), shot_id="shot_002",
    )

    subtitles = (tmp_path / "outputs" / "subtitles" / "film-en.srt").read_text(
        encoding="utf-8"
    )
    assert len(outputs) == 1
    assert len(provider.requests) == 1
    assert "00:00:00,000 --> 00:00:08,000\nAuthored translation." in subtitles
    assert "00:00:08,000 --> 00:00:16,000\n[English translation pending]" in subtitles
