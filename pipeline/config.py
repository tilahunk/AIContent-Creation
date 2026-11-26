from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    root: Path
    storyboard_path: Path
    image_provider: str
    video_provider: str
    music_provider: str
    narration_provider: str
    script_provider: str
    cloudflare_model: str
    gemini_text_model: str
    gemini_tts_model: str
    gemini_tts_voice: str
    kaggle_wan_output_dir: Path | None
    ace_step_output: Path | None
    timeout_seconds: int
    retries: int

    @classmethod
    def from_environment(cls, root: Path) -> "Settings":
        load_dotenv(root / ".env")

        def optional_path(name: str) -> Path | None:
            value = os.getenv(name)
            return Path(value).expanduser() if value else None

        return cls(
            root=root,
            storyboard_path=root / "storyboard.json",
            image_provider=os.getenv("IMAGE_PROVIDER", "mock").lower(),
            video_provider=os.getenv("VIDEO_PROVIDER", "mock").lower(),
            music_provider=os.getenv("MUSIC_PROVIDER", "mock").lower(),
            narration_provider=os.getenv("NARRATION_PROVIDER", "mock").lower(),
            script_provider=os.getenv("SCRIPT_PROVIDER", "gemini").lower(),
            cloudflare_model=os.getenv(
                "CLOUDFLARE_IMAGE_MODEL",
                "@cf/black-forest-labs/flux-1-schnell",
            ),
            gemini_text_model=os.getenv("GEMINI_TEXT_MODEL", "gemini-3.8-flash"),
            gemini_tts_model=os.getenv("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
            gemini_tts_voice=os.getenv("GEMINI_TTS_VOICE", "Kore"),
            kaggle_wan_output_dir=optional_path("KAGGLE_WAN_OUTPUT_DIR"),
            ace_step_output=optional_path("ACE_STEP_OUTPUT"),
            timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120")),
            retries=int(os.getenv("REQUEST_RETRIES", "3")),
        )

