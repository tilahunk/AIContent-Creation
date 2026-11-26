import os

from pipeline.config import Settings
from pipeline.providers.ace_step import ACEStepProvider
from pipeline.providers.base import Provider, ProviderError
from pipeline.providers.cloudflare import CloudflareProvider
from pipeline.providers.gemini import GeminiProvider
from pipeline.providers.mock import MockProvider
from pipeline.providers.wan import WanProvider


def create_provider(name: str, settings: Settings) -> Provider:
    if name == "mock":
        return MockProvider()
    if name == "cloudflare":
        return CloudflareProvider(
            os.getenv("CLOUDFLARE_ACCOUNT_ID"),
            os.getenv("CLOUDFLARE_API_TOKEN"),
            settings.cloudflare_model,
            settings.timeout_seconds,
            settings.retries,
        )
    if name == "gemini":
        return GeminiProvider(
            os.getenv("GEMINI_API_KEY"),
            settings.gemini_text_model,
            settings.gemini_tts_model,
            settings.gemini_tts_voice,
            settings.timeout_seconds,
            settings.retries,
        )
    if name == "wan":
        return WanProvider(settings.kaggle_wan_output_dir)
    if name in {"ace-step", "ace_step"}:
        return ACEStepProvider(settings.ace_step_output)
    raise ProviderError(f"Unknown provider '{name}'")
