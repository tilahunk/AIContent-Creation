from pathlib import Path
import time

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.providers.base import Provider
from pipeline.providers.base import ProviderError
from pipeline.providers.mock import MockProvider
from pipeline.utils.hashing import content_hash, file_hash


def generate_shots(root: Path, storyboard: dict, provider: Provider,
                   cache: ContentCache, run_logger: RunLogger,
                   shot_id: str | None = None, force: bool = False,
                   keyframe_extension: str = ".png") -> list[str]:
    outputs: list[str] = []
    for shot in storyboard["shots"]:
        if shot_id and shot["id"] != shot_id:
            continue
        started = time.perf_counter()
        keyframe = root / "outputs" / "keyframes" / f"{shot['id']}{keyframe_extension}"
        if not keyframe.exists():
            alternate_extension = ".jpg" if keyframe_extension == ".png" else ".png"
            alternate = root / "outputs" / "keyframes" / f"{shot['id']}{alternate_extension}"
            if alternate.exists():
                keyframe = alternate
        key = "video:" + content_hash({
            "keyframe": file_hash(keyframe) if keyframe.exists() else content_hash(str(keyframe)),
            "motion_prompt": shot["motion_prompt"],
            "duration": shot["duration_seconds"],
            "model": provider.model_for("video"),
        })
        output = root / "outputs" / "shots" / f"{shot['id']}.mp4"
        cached = cache.get(key)
        if not force and cached and Path(cached).exists():
            run_logger.log(stage="shots", shot_id=shot["id"], provider=provider.provider_name,
                           model=provider.model_for("video"), parameters={"cache": True},
                           seed=None, status="success", cache_hit=True, output=cached,
                           started=started)
            outputs.append(cached)
            continue
        request = {
            "kind": "video", "output": str(output),
            "shot_id": shot["id"], "keyframe": str(keyframe),
            "duration_seconds": shot["duration_seconds"],
            "motion_prompt": shot["motion_prompt"],
        }
        used_fallback = False
        try:
            result = provider.generate(request)
        except ProviderError as error:
            run_logger.log(
                stage="shots", shot_id=shot["id"], provider=provider.provider_name,
                model=provider.model_for("video"), parameters={"duration": shot["duration_seconds"]},
                seed=None, status="failure", error=str(error), started=started,
                retry_attempts=getattr(provider, "last_retry_attempts", 0),
            )
            if provider.provider_name == "mock":
                raise
            fallback = MockProvider()
            used_fallback = True
            request["keyframe"] = str(
                root / "outputs" / "keyframes" / f"{shot['id']}{keyframe_extension}"
            )
            result = fallback.generate(request)
            run_logger.log(
                stage="shots", shot_id=shot["id"], provider=fallback.provider_name,
                model=fallback.model_for("video"),
                parameters={"fallback": "ken_burns", "fallback_for": provider.provider_name},
                seed=None, status="success", output=result, started=started,
            )
        else:
            run_logger.log(
                stage="shots", shot_id=shot["id"], provider=provider.provider_name,
                model=provider.model_for("video"),
                parameters={"fallback": provider.provider_name == "mock", "duration": shot["duration_seconds"]},
                seed=None, status="success", output=result, started=started,
                retry_attempts=getattr(provider, "last_retry_attempts", 0),
            )
        if not used_fallback:
            cache.put(key, result)
        outputs.append(result)
    return outputs
