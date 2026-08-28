from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required_permissions: frozenset[str]
    side_effects: bool
    handler: Callable[..., dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def public_schema(self, permissions: set[str]) -> list[dict[str, Any]]:
        result = []
        for spec in self._tools.values():
            if spec.required_permissions.issubset(permissions):
                result.append({
                    "name": spec.name,
                    "description": spec.description,
                    "required_permissions": sorted(spec.required_permissions),
                    "side_effects": spec.side_effects,
                })
        return result

    def names(self) -> list[str]:
        return sorted(self._tools)


registry = ToolRegistry()
