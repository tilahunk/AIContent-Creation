from pathlib import Path

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.stages.assemble import assemble


def _assembly_inputs(root: Path) -> tuple[dict, list[str], str]:
    shots_dir = root / "outputs" / "shots"
    audio_dir = root / "outputs" / "audio"
    subtitles_dir = root / "outputs" / "subtitles"
    shots_dir.mkdir(parents=True)
    audio_dir.mkdir(parents=True)
    subtitles_dir.mkdir(parents=True)

    shots = [
        {"id": "shot_001", "duration_seconds": 4},
        {"id": "shot_002", "duration_seconds": 4},
    ]
    shot_files = []
    for shot in shots:
        path = shots_dir / f"{shot['id']}.mp4"
        path.write_bytes(b"shot")
        shot_files.append(str(path))
        (audio_dir / f"{shot['id']}-narration.wav").write_bytes(b"voice")

    music = audio_dir / "music.wav"
    music.write_bytes(b"music")
    (subtitles_dir / "film-en.srt").write_text(
        "1\n00:00:00,000 --> 00:00:08,000\nTest\n", encoding="utf-8"
    )
    storyboard = {
        "project": {"duration_seconds": 8, "aspect_ratios": ["9:16"]},
        "audio": {
            "narration_enabled": True,
            "background_music_enabled": True,
            "music_ducking": True,
        },
        "end_card": {
            "enabled": True,
            "text": "Created with AI",
            "duration_seconds": 2,
        },
        "shots": shots,
    }
    return storyboard, shot_files, str(music)


def test_assembly_mixes_audio_includes_end_card_and_caches_inputs(
    monkeypatch, tmp_path
):
    storyboard, shot_files, music = _assembly_inputs(tmp_path)
    commands = []

    def fake_run(_ffmpeg, arguments):
        assert _ffmpeg == "ffmpeg"
        commands.append(arguments)
        Path(arguments[-1]).write_bytes(b"generated")

    monkeypatch.setattr("pipeline.stages.assemble.find_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr("pipeline.stages.assemble._run", fake_run)

    cache = ContentCache(tmp_path)
    logger = RunLogger(tmp_path / "runs.jsonl")
    outputs = assemble(
        tmp_path, storyboard, shot_files, music, cache, logger
    )

    final_command = next(
        command for command in commands
        if str(command[-1]).endswith("heritage-vertical.mp4")
    )
    graph = final_command[final_command.index("-filter_complex") + 1]
    assert "adelay=4000:all=1" in graph
    assert "asplit=2[voice_sidechain][voice_mix]" in graph
    assert "sidechaincompress=" in graph
    assert "loudnorm=I=-14:TP=-1" in graph
    assert final_command[final_command.index("-t") + 1] == "10.0"
    assert "-shortest" not in final_command
    assert len(outputs) == 1
    assert (tmp_path / "outputs" / "final" / "end-card.mp4").resolve().as_posix() in (
        tmp_path / "outputs" / "final" / "concat.txt"
    ).read_text(encoding="utf-8")

    command_count = len(commands)
    assemble(tmp_path, storyboard, shot_files, music, cache, logger)
    assert len(commands) == command_count

    narration = tmp_path / "outputs" / "audio" / "shot_002-narration.wav"
    narration.write_bytes(b"changed narration")
    assemble(tmp_path, storyboard, shot_files, music, cache, logger)
    assert len(commands) > command_count
