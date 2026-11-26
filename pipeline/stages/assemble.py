import json
import re
import subprocess
import textwrap
import time
from pathlib import Path

from pipeline.cache import ContentCache
from pipeline.logger import RunLogger
from pipeline.utils.hashing import content_hash, file_hash
from pipeline.utils.video import find_ffmpeg


_GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00110", "00110"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00110", "00100"],
    ":": ["00000", "00110", "00110", "00000", "00110", "00110", "00000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "'": ["00100", "00100", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
}


def _run(ffmpeg: str, arguments: list[str]) -> None:
    try:
        subprocess.run([ffmpeg, "-y", *arguments], check=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        details = (error.stderr or b"").decode("utf-8", "replace").strip()
        raise RuntimeError(
            f"FFmpeg failed with exit code {error.returncode}: {details[-3000:]}"
        ) from error


def _write_end_card_image(path: Path, text: str, width: int = 640,
                          height: int = 360) -> None:
    disclosure = text.strip().upper()
    if not re.search(r"\bAI\b", disclosure):
        disclosure = f"{disclosure} - MADE WITH AI"
    lines = textwrap.wrap(disclosure, width=24, break_long_words=True) or ["MADE WITH AI"]
    scale = 4
    glyph_width = 5 * scale
    spacing = scale
    line_height = 7 * scale + 2 * scale
    total_height = len(lines) * line_height - 2 * scale
    origin_y = max(0, (height - total_height) // 2)
    pixels = bytearray((36, 22, 15) * width * height)

    for line_index, line in enumerate(lines):
        line_width = len(line) * (glyph_width + spacing) - spacing
        origin_x = max(0, (width - line_width) // 2)
        for char_index, char in enumerate(line):
            pattern = _GLYPHS.get(char, _GLYPHS["?"])
            char_x = origin_x + char_index * (glyph_width + spacing)
            for row, pattern_line in enumerate(pattern):
                for column, bit in enumerate(pattern_line):
                    if bit != "1":
                        continue
                    for y in range(origin_y + line_index * line_height + row * scale,
                                   origin_y + line_index * line_height + (row + 1) * scale):
                        for x in range(char_x + column * scale,
                                       char_x + (column + 1) * scale):
                            offset = (y * width + x) * 3
                            pixels[offset:offset + 3] = bytes((255, 255, 245))

    path.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + bytes(pixels))


def _audio_filter(storyboard: dict, music_index: int | None,
                  narration_inputs: list[tuple[int, float, float]],
                  total_duration: float) -> tuple[str, str | None]:
    filters: list[str] = []
    audio = storyboard["audio"]
    music_label = None
    voice_label = None

    if music_index is not None:
        filters.append(
            f"[{music_index}:a]volume=0.25,apad=whole_dur={total_duration:g}[music]"
        )
        music_label = "music"

    voice_labels = []
    for index, (input_index, offset, duration) in enumerate(narration_inputs):
        delay_ms = round(offset * 1000)
        label = f"voice_{index}"
        filters.append(
            f"[{input_index}:a]atrim=duration={duration:g},asetpts=PTS-STARTPTS,"
            f"adelay={delay_ms}:all=1,apad=whole_dur={total_duration:g}[{label}]"
        )
        voice_labels.append(label)
    if voice_labels:
        if len(voice_labels) == 1:
            voice_label = voice_labels[0]
        else:
            inputs = "".join(f"[{label}]" for label in voice_labels)
            filters.append(
                f"{inputs}amix=inputs={len(voice_labels)}:duration=longest:"
                "dropout_transition=0:normalize=0[voice]"
            )
            voice_label = "voice"

    if music_label and voice_label:
        if audio["music_ducking"]:
            filters.append(f"[{voice_label}]asplit=2[voice_sidechain][voice_mix]")
            filters.append(
                "[music][voice_sidechain]sidechaincompress=threshold=0.05:ratio=8:"
                "attack=20:release=250[ducked_music]"
            )
            music_label = "ducked_music"
            voice_label = "voice_mix"
        filters.append(
            f"[{music_label}][{voice_label}]amix=inputs=2:duration=longest:"
            "dropout_transition=0:normalize=0,"
            "loudnorm=I=-14:TP=-1:LRA=11[audio]"
        )
        return ";".join(filters), "audio"

    label = voice_label or music_label
    if label:
        filters.append(f"[{label}]loudnorm=I=-14:TP=-1:LRA=11[audio]")
        return ";".join(filters), "audio"
    return ";".join(filters), None


def assemble(root: Path, storyboard: dict, shot_files: list[str],
             music_file: str, cache: ContentCache, run_logger: RunLogger,
             force: bool = False) -> list[str]:
    started = time.perf_counter()
    final_dir = root / "outputs" / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    srt = root / "outputs" / "subtitles" / "film-en.srt"
    project_duration = float(storyboard["project"]["duration_seconds"])
    end_card = storyboard["end_card"]
    end_card_enabled = end_card["enabled"]
    end_card_duration = (
        float(end_card.get("duration_seconds", 4)) if end_card_enabled else 0
    )
    film_duration = project_duration + end_card_duration
    audio = storyboard["audio"]
    music_enabled = audio["background_music_enabled"]
    narration_enabled = audio["narration_enabled"]
    narration_files = [
        str(root / "outputs" / "audio" / f"{shot['id']}-narration.wav")
        for shot in storyboard["shots"]
    ] if narration_enabled else []

    required_inputs = list(shot_files) + [str(srt)]
    if music_enabled:
        required_inputs.append(music_file)
    required_inputs.extend(narration_files)
    for path in required_inputs:
        if not Path(path).is_file():
            raise RuntimeError(f"Missing assembly input: {path}")

    output_names = [
        "heritage-vertical.mp4" if ratio == "9:16" else "heritage-horizontal.mp4"
        for ratio in storyboard["project"]["aspect_ratios"]
    ]
    outputs = [str(final_dir / name) for name in output_names]
    cache_key = "assembly:" + content_hash({
        "inputs": {
            str(Path(path).resolve()): file_hash(Path(path))
            for path in required_inputs
        },
        "project": storyboard["project"],
        "audio": audio,
        "end_card": end_card,
        "output_format": "h264-aac-mov_text-loudnorm-v2",
    })
    cached = cache.get(cache_key)
    if not force and cached:
        cached_outputs = json.loads(cached)
        if cached_outputs and all(Path(path).is_file() for path in cached_outputs):
            for output in cached_outputs:
                run_logger.log(
                    stage="assemble", provider="ffmpeg",
                    model="ffmpeg-assembly-v2", parameters={"cache": True},
                    seed=None, status="success", cache_hit=True, output=output,
                    started=started,
                )
            return cached_outputs

    ffmpeg = find_ffmpeg()
    end_card_file = final_dir / "end-card.mp4"
    if end_card_enabled:
        end_card_image = final_dir / "end-card.ppm"
        _write_end_card_image(end_card_image, end_card["text"])
        _run(ffmpeg, [
            "-loop", "1", "-i", str(end_card_image),
            "-t", str(end_card_duration), "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-r", "24", "-an", str(end_card_file),
        ])

    concat = final_dir / "concat.txt"
    listed = [*shot_files]
    if end_card_enabled:
        listed.append(str(end_card_file))
    concat.write_text(
        "".join(f"file '{Path(path).resolve().as_posix()}'\n" for path in listed),
        encoding="utf-8",
    )
    base = final_dir / "base.mp4"
    _run(ffmpeg, [
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c", "copy", str(base),
    ])

    input_arguments = ["-i", str(base)]
    next_input = 1
    music_index = None
    if music_enabled:
        music_index = next_input
        input_arguments.extend(["-i", music_file])
        next_input += 1

    narration_inputs: list[tuple[int, float, float]] = []
    offset = 0.0
    if narration_enabled:
        for shot, narration_file in zip(storyboard["shots"], narration_files):
            narration_inputs.append((
                next_input, offset, float(shot["duration_seconds"])
            ))
            input_arguments.extend(["-i", narration_file])
            next_input += 1
            offset += float(shot["duration_seconds"])

    subtitle_index = next_input
    input_arguments.extend(["-i", str(srt)])

    audio_filter, audio_label = _audio_filter(
        storyboard, music_index, narration_inputs, film_duration
    )
    for ratio, output in zip(storyboard["project"]["aspect_ratios"], outputs):
        width, height = (1080, 1920) if ratio == "9:16" else (1920, 1080)
        filter_chain = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},format=yuv420p"
        )
        filters = [f"[0:v]{filter_chain}[video]"]
        if audio_filter:
            filters.append(audio_filter)
        arguments = [
            *input_arguments,
            "-filter_complex", ";".join(filters),
            "-map", "[video]",
            "-map", f"{subtitle_index}:s",
            "-t", str(film_duration),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:s", "mov_text",
        ]
        if audio_label:
            arguments.extend(["-map", f"[{audio_label}]", "-c:a", "aac", "-b:a", "192k"])
        else:
            arguments.append("-an")
        arguments.append(output)
        _run(ffmpeg, arguments)

    cache.put(cache_key, json.dumps(outputs, ensure_ascii=False))
    for output in outputs:
        run_logger.log(
            stage="assemble", provider="ffmpeg",
            model="ffmpeg-assembly-v2",
            parameters={
                "aspect_ratios": storyboard["project"]["aspect_ratios"],
                "duration_seconds": film_duration,
                "narration": narration_enabled,
                "music": music_enabled,
                "music_ducking": audio["music_ducking"],
                "loudness_target_lufs": -14,
                "true_peak_limit_dbtp": -1,
            },
            seed=None, status="success", output=output, started=started,
        )
    return outputs
