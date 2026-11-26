import json
import math
import os
import shutil
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.cache import ContentCache
from pipeline.config import Settings
from pipeline.logger import RunLogger
from pipeline.orchestrator import Orchestrator
from pipeline.stages.assemble import assemble


PACKAGE = ROOT / "outputs" / "the-next-page-film"
SAMPLE_RATE = 22050


def stamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_subtitles(storyboard, target):
    elapsed = 0.0
    entries = []
    for index, shot in enumerate(storyboard["shots"], start=1):
        duration = float(shot["duration_seconds"])
        entries.append(
            f"{index}\n{stamp(elapsed)} --> {stamp(elapsed + duration)}\n"
            f"{shot['subtitle_en']}\n"
        )
        elapsed += duration
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(entries), encoding="utf-8")


def write_original_score(path, duration):
    path.parent.mkdir(parents=True, exist_ok=True)
    notes = (220.0, 261.63, 293.66, 349.23, 392.0, 349.23, 293.66, 261.63)
    frames_per_chunk = SAMPLE_RATE
    total_frames = round(duration * SAMPLE_RATE)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(SAMPLE_RATE)
        start = 0
        while start < total_frames:
            end = min(start + frames_per_chunk, total_frames)
            samples = bytearray()
            for frame in range(start, end):
                time = frame / SAMPLE_RATE
                note_index = int(time / 1.2) % len(notes)
                age = time % 1.2
                frequency = notes[note_index]
                envelope = math.exp(-3.3 * age)
                pluck = envelope * (
                    math.sin(2 * math.pi * frequency * age)
                    + 0.24 * math.sin(4 * math.pi * frequency * age)
                    + 0.08 * math.sin(6 * math.pi * frequency * age)
                )
                pad = (
                    0.28 * math.sin(2 * math.pi * 110.0 * time)
                    + 0.18 * math.sin(2 * math.pi * 164.81 * time)
                )
                pulse_age = time % 2.4
                pulse = (
                    0.12 * math.sin(2 * math.pi * 72 * pulse_age)
                    * math.exp(-18 * pulse_age)
                    if pulse_age < 0.18 else 0.0
                )
                fade = min(1.0, time / 2.5, max(0.0, (duration - time) / 3.0))
                value = (0.105 * pluck + 0.035 * pad + pulse) * fade
                value = max(-0.75, min(0.75, value))
                left = int(value * 32767)
                right = int(value * 32767 * (0.96 + 0.04 * math.sin(time * 0.22)))
                samples.extend(struct.pack("<hh", left, right))
            audio.writeframesraw(samples)
            start = end
        audio.writeframes(b"")


def main():
    for key in ("IMAGE_PROVIDER", "VIDEO_PROVIDER", "MUSIC_PROVIDER", "NARRATION_PROVIDER"):
        os.environ[key] = "mock"

    storyboard_path = PACKAGE / "storyboard.json"
    if not storyboard_path.is_file():
        raise FileNotFoundError(f"Missing film storyboard: {storyboard_path}")

    settings = Settings.from_environment(PACKAGE)
    orchestrator = Orchestrator(settings)
    storyboard = orchestrator.validate()
    keyframes = PACKAGE / "outputs" / "keyframes"
    missing_frames = [
        keyframes / f"{shot['id']}.png"
        for shot in storyboard["shots"]
        if not (keyframes / f"{shot['id']}.png").is_file()
    ]
    if missing_frames:
        raise FileNotFoundError(
            "Missing illustrated keyframes: " + ", ".join(str(path) for path in missing_frames)
        )

    narration_files = [
        PACKAGE / "outputs" / "audio" / f"{shot['id']}-narration.wav"
        for shot in storyboard["shots"]
    ]
    missing_narration = [path for path in narration_files if not path.is_file()]
    if missing_narration:
        raise FileNotFoundError(
            "Missing offline narration WAVs: "
            + ", ".join(str(path) for path in missing_narration)
        )

    orchestrator.run(stage="shots", force=True)
    write_subtitles(
        storyboard,
        PACKAGE / "outputs" / "subtitles" / "film-en.srt",
    )
    music = PACKAGE / "outputs" / "audio" / "music.wav"
    total_duration = float(storyboard["project"]["duration_seconds"])
    if storyboard["end_card"]["enabled"]:
        total_duration += float(storyboard["end_card"].get("duration_seconds", 4))
    write_original_score(music, total_duration)

    shot_files = [
        str(PACKAGE / "outputs" / "shots" / f"{shot['id']}.mp4")
        for shot in storyboard["shots"]
    ]
    outputs = assemble(
        PACKAGE,
        storyboard,
        shot_files,
        str(music),
        ContentCache(PACKAGE),
        RunLogger(PACKAGE / "runs.jsonl"),
        force=True,
    )
    names = ("the-next-page-vertical.mp4", "the-next-page-horizontal.mp4")
    for source, name in zip(outputs, names):
        destination = PACKAGE / name
        shutil.copy2(source, destination)
        print(destination)


if __name__ == "__main__":
    main()
