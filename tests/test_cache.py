from pathlib import Path

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.stages.keyframes import generate_keyframes
from pipeline.utils.hashing import content_hash


def test_cache_hit_and_miss(tmp_path):
    cache = ContentCache(tmp_path)
    key = content_hash({"shot": "shot_001"})
    assert cache.get(key) is None
    cache.put(key, str(tmp_path / "result.png"))
    reloaded = ContentCache(tmp_path)
    assert reloaded.get(key) == str(tmp_path / "result.png")


def test_narration_change_does_not_invalidate_keyframe(tmp_path):
    class ImageProvider:
        provider_name = "test-image"
        output_extension = ".png"

        def __init__(self):
            self.calls = 0

        def model_for(self, _kind):
            return f"test-model-{_kind}"

        def generate(self, request):
            self.calls += 1
            output = Path(request["output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"image")
            return str(output)

    storyboard = {
        "creative_direction": {"visual_style": "warm cinematic"},
        "characters": [],
        "shots": [{
            "id": "shot_001",
            "image_prompt": "A fictional village at dawn",
            "narration": "First line",
        }],
    }
    provider = ImageProvider()
    cache = ContentCache(tmp_path)
    logger = RunLogger(tmp_path / "runs.jsonl")
    generate_keyframes(tmp_path, storyboard, provider, cache, logger)

    storyboard["shots"][0]["narration"] = "Changed narration"
    generate_keyframes(tmp_path, storyboard, provider, cache, logger)
    assert provider.calls == 1

    storyboard["shots"][0]["image_prompt"] = "A fictional village at sunset"
    generate_keyframes(tmp_path, storyboard, provider, cache, logger)
    assert provider.calls == 2
