import os
import shutil
from pathlib import Path

from pipeline.providers.base import Provider, ProviderError


class WanProvider(Provider):
    provider_name = "kaggle-wan"
    output_extension = ".mp4"

    def __init__(self, output_dir: Path | None) -> None:
        self.output_dir = output_dir

    def model_for(self, kind: str) -> str:
        return os.getenv("WAN_MODEL", "Wan2.2-TI2V-5B")

    def generate(self, request: dict) -> str:
        if not self.output_dir:
            raise ProviderError("Set KAGGLE_WAN_OUTPUT_DIR to the downloaded Kaggle Wan results")
        shot_id = request["shot_id"]
        source = self.output_dir / f"{shot_id}.mp4"
        if not source.is_file():
            raise ProviderError(f"Kaggle Wan result not found for {shot_id}: {source}")
        output = Path(request["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        return str(output)
