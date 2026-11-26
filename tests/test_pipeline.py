from pipeline.orchestrator import Orchestrator
from pipeline.config import Settings


def test_single_shot_keyframe_is_generated(tmp_path):
    root = tmp_path
    (root / "schema").mkdir()
    (root / "outputs" / "keyframes").mkdir(parents=True)
    (root / "storyboard.json").write_text(__import__("json").dumps({
        "project": {"title":"x","description":"x","duration_seconds":75,"language":"am","subtitle_language":"en","aspect_ratios":["9:16","16:9"]},
        "creative_direction":{"audience":"x","emotional_goal":"x","visual_style":"x","music_style":"x"},
        "characters":[{"id":"main_character","description":"x","reference_image":"x"}],
        "shots":[{"id":f"shot_{i:03}","duration_seconds":9 if i<8 else 12,"purpose":"x","image_prompt":"x","motion_prompt":"x","narration":"x","music_cue":"x","transition":"cut"} for i in range(1,9)],
        "audio":{"narration_enabled":True,"background_music_enabled":True,"music_ducking":True},
        "end_card":{"enabled":True,"text":"Created with AI"}
    }), encoding="utf-8")
    __import__("shutil").copyfile(
        __import__("pathlib").Path(__file__).resolve().parents[1] / "schema" / "storyboard.schema.json",
        root / "schema" / "storyboard.schema.json")
    settings = Settings.from_environment(root)
    orchestrator = Orchestrator(settings)
    storyboard = orchestrator.validate()
    assert storyboard["shots"][0]["id"] == "shot_001"


def test_missing_gemini_key_is_explicit():
    import os
    from pipeline.providers.gemini import GeminiProvider
    from pipeline.providers.base import ProviderError
    os.environ.pop("GEMINI_API_KEY", None)
    try:
        GeminiProvider(
            None, "gemini-3.8-flash", "gemini-3.8-flash-tts", "Kore"
        ).generate({"kind": "narration"})
    except ProviderError as error:
        assert "GEMINI_API_KEY" in str(error)
    else:
        raise AssertionError("Missing API key should raise")


def test_script_proposal_never_overwrites_approved_storyboard(tmp_path):
    import json
    import shutil
    from pathlib import Path
    from pipeline.orchestrator import Orchestrator

    root = Path(__file__).resolve().parents[1]
    (tmp_path / "schema").mkdir()
    shutil.copyfile(
        root / "schema" / "storyboard.schema.json",
        tmp_path / "schema" / "storyboard.schema.json",
    )
    (tmp_path / "storyboard.json").write_text(
        (root / "storyboard.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    screenplay = tmp_path / "screenplay.txt"
    screenplay.write_text("A family restores an old weaving tradition.", encoding="utf-8")

    approved = tmp_path / "storyboard.json"
    approved_before = approved.read_text(encoding="utf-8")
    storyboard = json.loads(approved_before)

    class ProposalProvider:
        provider_name = "test"

        def model_for(self, _kind):
            return f"test-model-{_kind}"

        def generate(self, request):
            assert "A family restores an old weaving tradition." in request["prompt"]
            output = Path(request["output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(storyboard), encoding="utf-8")
            return str(output)

    orchestrator = Orchestrator(Settings.from_environment(tmp_path))
    orchestrator.script_provider = ProposalProvider()
    results = orchestrator.run(stage="script", script_path=screenplay)
    assert Path(results["script"][0]).name == "storyboard-proposal.json"
    assert json.loads(approved.read_text(encoding="utf-8")) == storyboard


def test_empty_screenplay_is_rejected(tmp_path):
    import pytest
    from pipeline.orchestrator import generate_script_proposal
    from pipeline.logger import RunLogger

    class UnusedProvider:
        def generate(self, _request):
            raise AssertionError(
                f"Provider should not be called for an empty screenplay: {_request!r}"
            )

    with pytest.raises(ValueError, match="empty"):
        generate_script_proposal(
            tmp_path, " \n ", UnusedProvider(), RunLogger(tmp_path / "runs.jsonl")
        )
