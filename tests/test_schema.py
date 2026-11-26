import copy
import json
from pathlib import Path

import pytest

from pipeline.validator import validate_storyboard


ROOT = Path(__file__).resolve().parents[1]


def test_storyboard_validates():
    storyboard = validate_storyboard(ROOT)
    assert 8 <= len(storyboard["shots"]) <= 12
    assert sum(s["duration_seconds"] for s in storyboard["shots"]) == 75


def test_invalid_duration_is_rejected(tmp_path):
    storyboard = json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))
    storyboard["project"]["duration_seconds"] = 59
    path = tmp_path / "storyboard.json"
    path.write_text(json.dumps(storyboard), encoding="utf-8")
    with pytest.raises(ValueError, match="duration"):
        validate_storyboard(ROOT, path)


def test_duplicate_shot_id_is_rejected(tmp_path):
    storyboard = copy.deepcopy(json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8")))
    storyboard["shots"][1]["id"] = storyboard["shots"][0]["id"]
    path = tmp_path / "storyboard.json"
    path.write_text(json.dumps(storyboard), encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        validate_storyboard(ROOT, path)


def test_end_card_is_included_in_maximum_film_runtime(tmp_path):
    storyboard = copy.deepcopy(json.loads(
        (ROOT / "storyboard.json").read_text(encoding="utf-8")
    ))
    storyboard["project"]["duration_seconds"] = 90
    for index, shot in enumerate(storyboard["shots"]):
        shot["duration_seconds"] += 2 if index < 7 else 1
    path = tmp_path / "storyboard.json"
    path.write_text(json.dumps(storyboard), encoding="utf-8")

    with pytest.raises(ValueError, match="Final film runtime"):
        validate_storyboard(ROOT, path)
