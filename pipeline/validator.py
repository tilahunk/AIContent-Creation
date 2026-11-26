import json
from pathlib import Path

from jsonschema import Draft202012Validator


def validate_storyboard(root: Path, storyboard_path: Path | None = None) -> dict:
    storyboard_path = storyboard_path or root / "storyboard.json"
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    schema = json.loads((root / "schema" / "storyboard.schema.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(storyboard), key=lambda error: list(error.path))
    if errors:
        messages = "; ".join(f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors)
        raise ValueError(f"Storyboard validation failed: {messages}")

    shots = storyboard["shots"]
    actual = sum(float(shot["duration_seconds"]) for shot in shots)
    target = float(storyboard["project"]["duration_seconds"])
    if abs(actual - target) > 0.01:
        raise ValueError(f"Shot runtime {actual:g}s does not match project duration {target:g}s")
    end_card = storyboard["end_card"]
    end_card_duration = (
        float(end_card.get("duration_seconds", 4)) if end_card["enabled"] else 0
    )
    film_runtime = target + end_card_duration
    if film_runtime > 90:
        raise ValueError(f"Final film runtime {film_runtime:g}s exceeds 90s")
    ids = [shot["id"] for shot in shots]
    if len(ids) != len(set(ids)):
        raise ValueError("Shot identifiers must be unique")
    return storyboard
