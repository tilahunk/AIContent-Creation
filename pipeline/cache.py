import json
from pathlib import Path
from typing import Any


class ContentCache:
    def __init__(self, root: Path) -> None:
        self.path = root / ".pipeline-cache.json"
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str) -> str | None:
        value = self.data.get(key)
        return value if isinstance(value, str) else None

    def put(self, key: str, output: str) -> None:
        self.data[key] = output
        self.save()
