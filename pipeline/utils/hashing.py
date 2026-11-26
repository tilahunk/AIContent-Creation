import hashlib
import json
from pathlib import Path
from typing import Any


def content_hash(value: Any) -> str:
    if isinstance(value, (str, bytes)):
        payload = value if isinstance(value, bytes) else value.encode("utf-8")
    else:
        payload = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

