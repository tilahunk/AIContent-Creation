import subprocess
import struct
import zlib
from pathlib import Path
from typing import Any

from pipeline.providers.base import Provider
from pipeline.utils.video import find_ffmpeg


def _png(path: Path, width: int = 320, height: int = 180,
         rgb: tuple[int, int, int] = (180, 130, 80)) -> None:
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


class MockProvider(Provider):
    provider_name = "mock"
    output_extension = ".png"

    def model_for(self, kind: str) -> str:
        return {
            "image": "mock-keyframe-v1",
            "video": "mock-ken-burns-v1",
            "music": "mock-sine-preview-v1",
            "narration": "mock-audio-preview-v1",
        }.get(kind, "mock-v1")

    def generate(self, request: dict[str, Any]) -> str:
        output = Path(request["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        kind = request["kind"]
        if kind == "image":
            index = int(request["shot_id"].split("_")[-1])
            _png(output, rgb=((170 + index * 5) % 256, 120, 75))
        elif kind == "video":
            ffmpeg = find_ffmpeg()
            keyframe = Path(request["keyframe"])
            duration = float(request["duration_seconds"])
            if keyframe.exists():
                video_filter = (
                    "scale=800:-1,crop=640:360,zoompan="
                    "z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':"
                    "y='ih/2-(ih/zoom/2)':d=1:s=640x360:fps=24"
                )
                arguments = [
                    "-loop", "1", "-i", str(keyframe), "-t", str(duration),
                    "-vf", video_filter,
                ]
            else:
                arguments = [
                    "-f", "lavfi", "-i", f"color=c=0x4f321f:s=640x360:d={duration}",
                    "-t", str(duration),
                ]
            subprocess.run([
                ffmpeg, "-y", *arguments, "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-an", str(output),
            ], check=True, capture_output=True)
        elif kind in {"music", "narration"}:
            ffmpeg = find_ffmpeg()
            subprocess.run([
                ffmpeg, "-y", "-f", "lavfi", "-i",
                f"sine=frequency=220:duration={request['duration_seconds']}",
                "-c:a", "pcm_s16le", str(output),
            ], check=True, capture_output=True)
        else:
            raise RuntimeError(f"Unsupported mock request kind: {kind}")
        return str(output)
