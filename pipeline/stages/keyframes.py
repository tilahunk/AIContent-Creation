from pathlib import Path
import time

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.providers.base import Provider
from pipeline.providers.base import ProviderError
from pipeline.providers.mock import MockProvider
from pipeline.utils.hashing import content_hash


def generate_keyframes(root: Path, storyboard: dict, provider: Provider,
                       cache: ContentCache, run_logger: RunLogger,
                       shot_id: str | None = None, force: bool = False) -> list[str]:
    outputs: list[str] = []
    if not shot_id:
        for character in storyboard["characters"]:
            reference = root / "outputs" / "references" / f"{character['id']}{provider.output_extension}"
            reference.parent.mkdir(parents=True, exist_ok=True)
            reference_key = "reference:" + content_hash({
                "character": character,
                "visual_style": storyboard["creative_direction"]["visual_style"],
                "model": provider.model_for("image"),
            })
            cached_reference = cache.get(reference_key)
            if not force and cached_reference and Path(cached_reference).exists():
                character["reference_image"] = cached_reference
                continue
            reference_started = time.perf_counter()
            reference_request = {
                "kind": "image",
                "output": str(reference),
                "shot_id": "shot_001",
                "prompt": character["description"],
            }
            reference_fallback = False
            try:
                reference_output = provider.generate(reference_request)
            except ProviderError as error:
                run_logger.log(
                    stage="keyframes", provider=provider.provider_name,
                    model=provider.model_for("image"), parameters={"reference_id": character["id"]},
                    seed=None, status="failure", error=str(error), started=reference_started,
                    retry_attempts=getattr(provider, "last_retry_attempts", 0),
                )
                if provider.provider_name == "mock":
                    raise
                fallback = MockProvider()
                reference_fallback = True
                reference_request["output"] = str(
                    root / "outputs" / "references" / f"{character['id']}.png"
                )
                reference_output = fallback.generate(reference_request)
                run_logger.log(
                    stage="keyframes", provider=fallback.provider_name,
                    model=fallback.model_for("image"),
                    parameters={"reference_id": character["id"], "fallback_for": provider.provider_name},
                    seed=None, status="success", output=reference_output, started=reference_started,
                )
            else:
                run_logger.log(
                    stage="keyframes", provider=provider.provider_name,
                    model=provider.model_for("image"), parameters={"reference_id": character["id"]},
                    seed=None, status="success", output=reference_output, started=reference_started,
                    retry_attempts=getattr(provider, "last_retry_attempts", 0),
                )
            if not reference_fallback:
                cache.put(reference_key, reference_output)
            character["reference_image"] = reference_output
    for shot in storyboard["shots"]:
        if shot_id and shot["id"] != shot_id:
            continue
        started = time.perf_counter()
        character_context = " ".join(
            character["description"] for character in storyboard["characters"]
        )
        prompt = (
            f"{storyboard['creative_direction']['visual_style']}. "
            f"{character_context}. {shot['image_prompt']}"
        )
        key = "keyframe:" + content_hash({
            "shot_id": shot["id"],
            "prompt": prompt,
            "model": provider.model_for("image"),
        })
        output = root / "outputs" / "keyframes" / f"{shot['id']}{provider.output_extension}"
        cached = cache.get(key)
        if not force and cached and Path(cached).exists():
            run_logger.log(stage="keyframes", shot_id=shot["id"], provider=provider.provider_name,
                           model=provider.model_for("image"), parameters={"cache": True},
                           seed=None, status="success", cache_hit=True, output=cached,
                           started=started)
            outputs.append(cached)
            continue
        request = {
            "kind": "image", "output": str(output),
            "shot_id": shot["id"], "prompt": prompt,
        }
        used_fallback = False
        try:
            result = provider.generate(request)
        except ProviderError as error:
            run_logger.log(
                stage="keyframes", shot_id=shot["id"], provider=provider.provider_name,
                model=provider.model_for("image"), parameters={"prompt_version": 1},
                seed=None, status="failure", error=str(error), started=started,
                retry_attempts=getattr(provider, "last_retry_attempts", 0),
            )
            if provider.provider_name == "mock":
                raise
            fallback = MockProvider()
            used_fallback = True
            request["output"] = str(root / "outputs" / "keyframes" / f"{shot['id']}.png")
            result = fallback.generate(request)
            run_logger.log(
                stage="keyframes", shot_id=shot["id"], provider=fallback.provider_name,
                model=fallback.model_for("image"),
                parameters={"prompt_version": 1, "fallback_for": provider.provider_name},
                seed=None, status="success", output=result, started=started,
            )
        else:
            run_logger.log(
                stage="keyframes", shot_id=shot["id"], provider=provider.provider_name,
                model=provider.model_for("image"),
                parameters={"prompt_version": 1, "format": provider.output_extension},
                seed=None, status="success", output=result, started=started,
                retry_attempts=getattr(provider, "last_retry_attempts", 0),
            )
        if not used_fallback:
            cache.put(key, result)
        outputs.append(result)
    return outputs
