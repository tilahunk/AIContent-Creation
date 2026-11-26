import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from pipeline.providers.base import Provider, ProviderError


class CloudflareProvider(Provider):
    provider_name = "cloudflare-workers-ai"
    output_extension = ".jpg"

    def __init__(self, account_id: str | None, api_token: str | None,
                 model: str, timeout_seconds: int = 120, retries: int = 3) -> None:
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.last_retry_attempts = 0

    def model_for(self, kind: str) -> str:
        return self.model

    def generate(self, request: dict) -> str:
        if not self.account_id or not self.api_token:
            raise ProviderError("CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required")
        if request.get("kind") != "image":
            raise ProviderError(f"Cloudflare provider does not support {request.get('kind')}")

        url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/ai/run/{self.model}"
        )
        body = json.dumps({
            "prompt": request["prompt"],
            "steps": int(request.get("steps", 4)),
            **({"seed": int(request["seed"])} if request.get("seed") is not None else {}),
        }).encode("utf-8")
        self.last_retry_attempts = 0
        for attempt in range(self.retries + 1):
            outbound = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(outbound, timeout=self.timeout_seconds) as response:
                    try:
                        payload = json.loads(response.read().decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as error:
                        raise ProviderError("Cloudflare Workers AI returned invalid JSON") from error
                if payload.get("success") is False:
                    raise ProviderError("Cloudflare Workers AI returned success=false")
                result = payload.get("result", {})
                encoded_image = result.get("image") if isinstance(result, dict) else None
                if not encoded_image:
                    raise ProviderError("Cloudflare response did not contain result.image")
                try:
                    image_bytes = base64.b64decode(encoded_image, validate=True)
                except ValueError as error:
                    raise ProviderError("Cloudflare returned invalid base64 image data") from error
                output = Path(request["output"])
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(image_bytes)
                return str(output)
            except urllib.error.HTTPError as error:
                retryable = error.code in {408, 429, 500, 502, 503, 504}
                if not retryable or attempt >= self.retries:
                    raise ProviderError(f"Cloudflare Workers AI request failed with HTTP {error.code}") from error
                self.last_retry_attempts += 1
            except (urllib.error.URLError, TimeoutError) as error:
                if attempt >= self.retries:
                    raise ProviderError(f"Cloudflare Workers AI request failed: {type(error).__name__}") from error
                self.last_retry_attempts += 1
            if attempt < self.retries:
                time.sleep(min(2 ** attempt, 8))
        raise ProviderError("Cloudflare Workers AI request exhausted retries")
