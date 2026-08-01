"""Local archives persistence (JSON file instead of browser localStorage)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import archives_path, load_config
from .presets import INITIAL_PRESET_CREATIONS


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_ids(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in items:
        if not item.get("id"):
            item["id"] = f"doc_{uuid.uuid4().hex[:10]}"
        if not item.get("createdAt"):
            item["createdAt"] = _now_iso()
    return items


class ArchiveStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or archives_path(load_config())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(list(INITIAL_PRESET_CREATIONS))

    def load(self) -> list[dict[str, Any]]:
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return _ensure_ids(data)
        except (OSError, json.JSONDecodeError):
            pass
        return _ensure_ids([dict(x) for x in INITIAL_PRESET_CREATIONS])

    def save(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(_ensure_ids(items), fh, indent=2, ensure_ascii=False)

    def upsert(self, creation: dict[str, Any]) -> dict[str, Any]:
        items = self.load()
        creation = dict(creation)
        if not creation.get("id"):
            creation["id"] = f"doc_{uuid.uuid4().hex[:10]}"
        if not creation.get("createdAt"):
            creation["createdAt"] = _now_iso()

        replaced = False
        for i, existing in enumerate(items):
            if existing.get("id") == creation["id"]:
                items[i] = creation
                replaced = True
                break
        if not replaced:
            items.insert(0, creation)
        self.save(items)
        return creation

    def delete(self, creation_id: str) -> list[dict[str, Any]]:
        items = [c for c in self.load() if c.get("id") != creation_id]
        self.save(items)
        return items

    def import_items(self, new_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items = self.load()
        existing_ids = {c.get("id") for c in items}
        merged: list[dict[str, Any]] = []
        for item in new_items:
            item = dict(item)
            if not item.get("id") or item["id"] in existing_ids:
                item["id"] = f"imported_{uuid.uuid4().hex[:10]}"
            existing_ids.add(item["id"])
            if not item.get("createdAt"):
                item["createdAt"] = _now_iso()
            merged.append(item)
        combined = merged + items
        self.save(combined)
        return combined

    def export_json(self) -> str:
        return json.dumps(self.load(), indent=2, ensure_ascii=False)
