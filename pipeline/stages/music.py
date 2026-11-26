from pathlib import Path
import time

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.providers.base import Provider
from pipeline.providers.base import ProviderError
from pipeline.providers.mock import MockProvider
from pipeline.utils.hashing import content_hash


def generate_music(root: Path, storyboard: dict, provider: Provider,
                   cache: ContentCache, run_logger: RunLogger,
                   force: bool = False) -> str:
    started = time.perf_counter()
    duration = float(storyboard["project"]["duration_seconds"])
    request = {
        "kind": "music",
        "duration_seconds": duration,
        "music_style": storyboard["creative_direction"]["music_style"],
        "music_cues": [
            {"shot_id": shot["id"], "cue": shot["music_cue"]}
            for shot in storyboard["shots"]
        ],
        "model": provider.model_for("music"),
    }
    key = "music:" + content_hash(request)
    output = str(root / "outputs" / "audio" / "music.wav")
    cached = cache.get(key)
    if not force and cached and Path(cached).exists():
        run_logger.log(stage="music", provider=provider.provider_name,
                       model=provider.model_for("music"),
                       parameters=request, seed=None, status="success",
                       cache_hit=True, output=cached, started=started)
        return cached
    used_fallback = False
    try:
        result = provider.generate({"output": output, **request})
    except ProviderError as error:
        run_logger.log(
            stage="music", provider=provider.provider_name,
            model=provider.model_for("music"), parameters=request,
            seed=None, status="failure", error=str(error), started=started,
            retry_attempts=getattr(provider, "last_retry_attempts", 0),
        )
        if provider.provider_name == "mock":
            raise
        fallback = MockProvider()
        used_fallback = True
        result = fallback.generate({"output": output, **request})
        run_logger.log(
            stage="music", provider=fallback.provider_name,
            model=fallback.model_for("music"),
            parameters={"placeholder": True, "fallback_for": provider.provider_name},
            seed=None, status="success", output=result, started=started,
        )
    else:
        run_logger.log(
            stage="music", provider=provider.provider_name,
            model=provider.model_for("music"), parameters=request,
            seed=None, status="success", output=result, started=started,
            retry_attempts=getattr(provider, "last_retry_attempts", 0),
        )
    if not used_fallback:
        cache.put(key, result)
    return result
