from abc import ABC, abstractmethod
from typing import Any


class ProviderError(RuntimeError):
    pass


class Provider(ABC):
    provider_name = "unknown"
    output_extension = ".bin"

    def model_for(self, kind: str) -> str:
        return type(self).__name__

    @abstractmethod
    def generate(self, request: dict[str, Any]) -> str:
        """Generate an output and return its path."""

