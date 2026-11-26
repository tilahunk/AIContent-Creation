from pathlib import Path
import time

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.providers.base import Provider
from pipeline.providers.base import ProviderError
from pipeline.providers.mock import MockProvider
from pipeline.utils.hashing import content_hash


def _stamp(value: float) -> str:
    total_milliseconds = round(value * 1000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def _subtitle_text(root: Path, storyboard: dict, shot: dict, provider: Provider,
                   cache: ContentCache, run_logger: RunLogger,
                   force: bool) -> str:
    authored_translation = shot.get("subtitle_en")
    if provider.provider_name != "google-gemini-api":
        return authored_translation or "[English translation pending]"

    started = time.perf_counter()
    request = {
        "kind": "text",
        "output": str(
            root / "outputs" / "subtitles" / "translations"
            / f"{shot['id']}.txt"
        ),
        "prompt": (
            f"Translate this {storyboard['project']['language']} narration into "
            f"concise, faithful {storyboard['project']['subtitle_language']} subtitles. "
            "Return only the translation.\n\n"
            + shot["narration"]
        ),
        "model": provider.model_for("text"),
    }
    key = "translation:" + content_hash(request)
    cached = cache.get(key)
    if not force and cached and Path(cached).is_file():
        run_logger.log(
            stage="translation", shot_id=shot["id"],
            provider=provider.provider_name, model=provider.model_for("text"),
            parameters={"cache": True}, seed=None, status="success",
            cache_hit=True, output=cached, started=started,
        )
        return Path(cached).read_text(encoding="utf-8").strip()

    try:
        translated = provider.generate(request)
        text = Path(translated).read_text(encoding="utf-8").strip()
        if not text:
            raise ProviderError("Subtitle translation returned empty text")
    except (ProviderError, OSError) as error:
        run_logger.log(
            stage="translation", shot_id=shot["id"],
            provider=provider.provider_name, model=provider.model_for("text"),
            parameters={"target_language": storyboard["project"]["subtitle_language"]},
            seed=None, status="failure", error=str(error), started=started,
            retry_attempts=getattr(provider, "last_retry_attempts", 0),
        )
        if authored_translation:
            return authored_translation
        raise

    cache.put(key, translated)
    run_logger.log(
        stage="translation", shot_id=shot["id"],
        provider=provider.provider_name, model=provider.model_for("text"),
        parameters={"target_language": storyboard["project"]["subtitle_language"]},
        seed=None, status="success", cache_hit=False, output=translated,
        started=started,
        retry_attempts=getattr(provider, "last_retry_attempts", 0),
    )
    return text


def generate_narration(root: Path, storyboard: dict, provider: Provider,
                       cache: ContentCache, run_logger: RunLogger,
                       shot_id: str | None = None, force: bool = False) -> list[str]:
    outputs: list[str] = []
    elapsed = 0.0
    subtitles = root / "outputs" / "subtitles" / "film-en.srt"
    subtitles.parent.mkdir(parents=True, exist_ok=True)
    srt_entries = []

    for index, shot in enumerate(storyboard["shots"], start=1):
        duration = float(shot["duration_seconds"])
        selected = shot_id is None or shot["id"] == shot_id
        if selected and storyboard["audio"]["narration_enabled"]:
            started = time.perf_counter()
            request = {
                "kind": "narration",
                "duration_seconds": duration,
                "language": storyboard["project"]["language"],
                "text": shot["narration"],
                "output": str(
                    root / "outputs" / "audio" / f"{shot['id']}-narration.wav"
                ),
                "model": provider.model_for("narration"),
            }
            voice = getattr(provider, "voice", None)
            if voice:
                request["voice"] = voice
            key = "narration:" + content_hash(request)
            output = Path(request["output"])
            cached = cache.get(key)
            if not force and cached and Path(cached).is_file():
                result = cached
                run_logger.log(
                    stage="narration", shot_id=shot["id"],
                    provider=provider.provider_name,
                    model=provider.model_for("narration"),
                    parameters={"cache": True}, seed=None, status="success",
                    cache_hit=True, output=result, started=started,
                )
            else:
                try:
                    result = provider.generate(request)
                except ProviderError as error:
                    run_logger.log(
                        stage="narration", shot_id=shot["id"],
                        provider=provider.provider_name,
                        model=provider.model_for("narration"),
                        parameters={"language": request["language"]}, seed=None,
                        status="failure", error=str(error), started=started,
                        retry_attempts=getattr(provider, "last_retry_attempts", 0),
                    )
                    if provider.provider_name == "mock":
                        raise
                    fallback = MockProvider()
                    result = fallback.generate({
                        "kind": "narration", "duration_seconds": duration,
                        "output": str(output), "text": shot["narration"],
                    })
                    run_logger.log(
                        stage="narration", shot_id=shot["id"],
                        provider=fallback.provider_name,
                        model=fallback.model_for("narration"),
                        parameters={
                            "placeholder": True,
                            "fallback_for": provider.provider_name,
                        },
                        seed=None, status="success", output=result, started=started,
                    )
                else:
                    cache.put(key, result)
                    run_logger.log(
                        stage="narration", shot_id=shot["id"],
                        provider=provider.provider_name,
                        model=provider.model_for("narration"),
                        parameters={"language": request["language"]}, seed=None,
                        status="success", cache_hit=False, output=result,
                        started=started,
                        retry_attempts=getattr(provider, "last_retry_attempts", 0),
                    )
            outputs.append(result)

        text = _subtitle_text(
            root, storyboard, shot, provider, cache, run_logger, force
        )
        srt_entries.append(
            f"{index}\n{_stamp(elapsed)} --> {_stamp(elapsed + duration)}\n{text}\n"
        )
        elapsed += duration

    subtitles.write_text("\n".join(srt_entries), encoding="utf-8")
    return outputs
