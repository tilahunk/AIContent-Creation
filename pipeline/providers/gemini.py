import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from pipeline.providers.base import Provider, ProviderError


class GeminiProvider(Provider):
    provider_name = "google-gemini-api"
    output_extension = ".wav"

    def __init__(self, api_key: str | None, text_model: str, tts_model: str,
                 voice: str, timeout_seconds: int = 120, retries: int = 3) -> None:
        self.api_key = api_key
        self.text_model = text_model
        self.tts_model = tts_model
        self.voice = voice
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.last_retry_attempts = 0

    def model_for(self, kind: str) -> str:
        return self.tts_model if kind == "narration" else self.text_model

    def _post_json(self, url: str, payload: dict) -> dict:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.last_retry_attempts = 0
        for attempt in range(self.retries + 1):
            outbound = urllib.request.Request(
                url,
                data=body,
                headers={
                    "x-goog-api-key": self.api_key or "",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(outbound, timeout=self.timeout_seconds) as response:
                    try:
                        return json.loads(response.read().decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as error:
                        raise ProviderError("Gemini API returned invalid JSON") from error
            except urllib.error.HTTPError as error:
                retryable = error.code in {408, 429, 500, 502, 503, 504}
                if not retryable or attempt >= self.retries:
                    raise ProviderError(f"Gemini API request failed with HTTP {error.code}") from error
                self.last_retry_attempts += 1
            except (urllib.error.URLError, TimeoutError) as error:
                if attempt >= self.retries:
                    raise ProviderError(f"Gemini API request failed: {type(error).__name__}") from error
                self.last_retry_attempts += 1
            if attempt < self.retries:
                time.sleep(min(2 ** attempt, 8))
        raise ProviderError("Gemini API request exhausted retries")

    def generate(self, request: dict) -> str:
        if not self.api_key:
            raise ProviderError("GEMINI_API_KEY is required")
        kind = request.get("kind")
        output = Path(request["output"])
        output.parent.mkdir(parents=True, exist_ok=True)

        if kind == "narration":
            interaction = self._post_json(
                "https://generativelanguage.googleapis.com/v1beta/interactions",
                {
                    "model": self.tts_model,
                    "input": [{
                        "type": "user_input",
                        "content": [{
                            "type": "text",
                            "text": request["text"],
                            "annotations": [{
                                "type": "speech_metadata",
                                "style": request.get("style", "warm, clear documentary narration"),
                            }],
                        }],
                    }],
                    "response_format": {"type": "audio"},
                    "generation_config": {
                        "speech_config": [{"voice": request.get("voice", self.voice)}]
                    },
                },
            )
            audio = interaction.get("output_audio", {}).get("data")
            if not audio:
                for step in interaction.get("steps", []):
                    for item in step.get("content", []):
                        if item.get("type") == "audio" and item.get("data"):
                            audio = item["data"]
            if not audio:
                raise ProviderError("Gemini TTS response did not include audio data")
            try:
                output.write_bytes(base64.b64decode(audio, validate=True))
            except ValueError as error:
                raise ProviderError("Gemini TTS response contained invalid base64 audio") from error
            return str(output)

        if kind == "text":
            result = self._post_json(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.text_model}:generateContent",
                {
                    "contents": [{"parts": [{"text": request["prompt"]}]}],
                    "generationConfig": {"temperature": request.get("temperature", 0.4)},
                },
            )
            try:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError) as error:
                raise ProviderError("Gemini response did not contain generated text") from error
            output.write_text(text, encoding="utf-8")
            return str(output)
        raise ProviderError(f"Gemini provider does not support {kind}")
