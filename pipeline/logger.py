import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, *, stage: str, shot_id: str | None = None, provider: str,
            model: str, parameters: dict[str, Any], seed: int | None,
            status: str, cache_hit: bool = False, output: str | None = None,
            error: str | None = None, started: float | None = None,
            retry_attempts: int = 0) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "shot_id": shot_id,
            "provider": provider,
            "model": model,
            "parameters": parameters,
            "seed": seed,
            "latency_ms": 0 if started is None else int((time.perf_counter() - started) * 1000),
            "cost_usd": None,
            "status": status,
            "cache_hit": cache_hit,
            "output": output,
            "error": error,
            "retry_attempts": retry_attempts,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
