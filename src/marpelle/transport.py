from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


TransportHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(slots=True)
class Endpoint:
    role: str
    route: str
    handler: TransportHandler
    metadata: dict[str, Any] = field(default_factory=dict)


class TransportRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Endpoint] = {}

    def add(self, endpoint: Endpoint) -> None:
        self._handlers[endpoint.role] = endpoint

    def get(self, role: str) -> Endpoint | None:
        return self._handlers.get(role)

    def handlers(self) -> dict[str, Endpoint]:
        return dict(self._handlers)


def _build_decorator(role: str):
    def decorator(route: str):
        def wrap(fn: TransportHandler):
            setattr(fn, "__marpelle_transport__", {"role": role, "route": route})
            return fn

        return wrap

    return decorator


publisher = _build_decorator("publisher")
subscriber = _build_decorator("subscriber")
unsubscriber = _build_decorator("unsubscriber")
requester = _build_decorator("requester")
responder = _build_decorator("responder")
