import base64
import json
from pathlib import Path

from pipeline.providers.cloudflare import CloudflareProvider
from pipeline.providers.gemini import GeminiProvider


class FakeResponse:
    def __init__(self, value: dict):
        self.payload = json.dumps(value).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self.payload


def test_cloudflare_image_response_is_written(monkeypatch, tmp_path):
    image = b"small-image-fixture"
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: FakeResponse({
            "success": True,
            "result": {"image": base64.b64encode(image).decode("ascii")},
        }),
    )
    provider = CloudflareProvider("account-id", "secret-token", "@cf/test/model")
    output = tmp_path / "keyframe.jpg"
    result = provider.generate({
        "kind": "image", "prompt": "fictional landscape", "output": str(output),
    })
    assert Path(result).read_bytes() == image


def test_gemini_tts_uses_audio_interaction_and_writes_bytes(monkeypatch, tmp_path):
    audio = b"RIFF-test-audio"
    observed = {}

    def fake_urlopen(request, timeout):
        observed["url"] = request.full_url
        observed["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({
            "output_audio": {"data": base64.b64encode(audio).decode("ascii")},
        })

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    provider = GeminiProvider(
        "test-key", "gemini-3.8-flash", "gemini-3.8-flash-tts", "Kore"
    )
    output = tmp_path / "narration.wav"
    provider.generate({
        "kind": "narration", "text": "Test narration", "output": str(output),
    })
    assert observed["url"].endswith("/v1beta/interactions")
    assert observed["payload"]["model"] == "gemini-3.8-flash-tts"
    assert output.read_bytes() == audio


def test_gemini_retries_rate_limit(monkeypatch, tmp_path):
    import urllib.error

    calls = 0

    def fake_urlopen(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise urllib.error.HTTPError(request.full_url, 429, "limited", {}, None)
        return FakeResponse({"candidates": [{
            "content": {"parts": [{"text": '{"ok": true}'}]},
        }]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda _: None)
    provider = GeminiProvider(
        "test-key", "gemini-3.8-flash", "gemini-3.8-flash-tts",
        "Kore", retries=1,
    )
    output = tmp_path / "proposal.json"
    provider.generate({"kind": "text", "prompt": "return json", "output": str(output)})
    assert calls == 2
    assert provider.last_retry_attempts == 1
    assert output.read_text(encoding="utf-8") == '{"ok": true}'
