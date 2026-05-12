from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class Serializer(ABC):
    """Serialize Python values into bytes for transport."""

    @abstractmethod
    def dumps(self, payload: dict[str, Any]) -> bytes:
        raise NotImplementedError


class Deserializer(ABC):
    """Deserialize transport bytes into Python values."""

    @abstractmethod
    def loads(self, raw: bytes) -> dict[str, Any]:
        raise NotImplementedError


class JsonSerde(Serializer, Deserializer):
    """Default JSON serde used by built-in backends."""

    def dumps(self, payload: dict[str, Any]) -> bytes:
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    def loads(self, raw: bytes) -> dict[str, Any]:
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("decoded payload must be a JSON object")
        return value
