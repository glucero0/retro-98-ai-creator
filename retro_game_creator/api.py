"""JavaScript ↔ Python bridge exposed to the 98.css UI via pywebview."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from pathlib import Path
from typing import Any

from . import __version__
from .config import SUGGESTED_MODELS, load_config, save_config
from .gemini_provider import SUGGESTED_GEMINI_MODELS, resolve_api_key
from .generator import generate_creation, provider_status
from .presets import CREATION_TYPES, PLATFORM_OPTIONS, POPULAR_GAME_PRESETS
from .storage import ArchiveStore

logger = logging.getLogger(__name__)


class Api:
    """Methods on this class are callable from window.pywebview.api in the UI."""

    def __init__(self) -> None:
        self.config = load_config()
        self.store = ArchiveStore()
        self._window = None
        self._gen_lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._jobs_lock = threading.Lock()

    def set_window(self, window) -> None:  # noqa: ANN001 — pywebview Window
        self._window = window

    # ── Jobs (JS polls these — reliable vs evaluate_js from worker threads) ──

    def _set_job(self, job_id: str, **fields: Any) -> None:
        with self._jobs_lock:
            job = self._jobs.setdefault(job_id, {"id": job_id, "status": "queued"})
            job.update(fields)

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return {"id": job_id, "status": "missing", "error": "Unknown job id"}
            # Return a shallow copy so callers can mutate safely
            return dict(job)

    def ping(self) -> dict[str, Any]:
        """Health check used by the UI to verify the Python bridge."""
        return {"ok": True, "version": __version__}

    # ── Catalog / config ──────────────────────────────────────────────

    def get_bootstrap(self) -> dict[str, Any]:
        creations = self.store.load()
        return {
            "version": __version__,
            "config": self._public_config(),
            "suggestedModels": SUGGESTED_MODELS,
            "suggestedGeminiModels": SUGGESTED_GEMINI_MODELS,
            "platforms": PLATFORM_OPTIONS,
            "creationTypes": CREATION_TYPES,
            "presets": POPULAR_GAME_PRESETS,
            "creations": creations,
            "modelStatus": provider_status(self.config),
        }

    def _public_config(self) -> dict[str, Any]:
        cfg = self.config
        gemini = dict(cfg.get("gemini") or {})
        if gemini.get("api_key"):
            gemini["api_key_set"] = True
            gemini["api_key"] = ""
        else:
            gemini["api_key_set"] = bool(resolve_api_key(cfg.get("gemini") or {}))
        return {
            "backend": dict(cfg.get("backend") or {}),
            "gemini": gemini,
            "model": dict(cfg.get("model", {})),
            "generation": dict(cfg.get("generation", {})),
            "ui": dict(cfg.get("ui", {})),
            "paths": dict(cfg.get("paths", {})),
        }

    def get_model_status(self) -> dict[str, Any]:
        return provider_status(self.config)

    def save_settings(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Persist Control Panel changes."""
        if not isinstance(updates, dict):
            return {"ok": False, "error": "Invalid settings payload"}

        reload_model = bool(updates.pop("reload_model", False))

        self.config = save_config(updates, existing=self.config)

        result: dict[str, Any] = {
            "ok": True,
            "config": self._public_config(),
            "modelStatus": provider_status(self.config),
            "message": "Settings saved.",
        }

        provider = ((self.config.get("backend") or {}).get("provider") or "gemini").lower()
        if reload_model and provider in ("huggingface", "hf", "local", "phi"):
            try:
                from .llm import model_manager

                model_manager.unload()
                result["modelStatus"] = provider_status(self.config)
                result["message"] = "Settings saved. Local model will reload on next generation."
            except Exception:  # noqa: BLE001
                pass

        return result

    def preload_model(self) -> dict[str, Any]:
        """Download / load local HF model (Gemini needs no download)."""
        provider = ((self.config.get("backend") or {}).get("provider") or "gemini").lower()
        if provider in ("gemini", "google", "google-gemini"):
            status = provider_status(self.config)
            return {
                "ok": True,
                "message": status.get("detail") or "Gemini uses the cloud API — no local download.",
                "modelStatus": status,
            }

        job_id = f"load_{uuid.uuid4().hex[:10]}"
        self._set_job(
            job_id,
            status="running",
            kind="preload",
            progress={"message": "Starting model download / load…", "phase": "download"},
        )

        def _run() -> None:
            try:
                from .llm import model_manager

                model_manager.set_progress_callback(
                    lambda payload: self._on_job_progress(job_id, payload)
                )
                model_manager.ensure_loaded(self.config.get("model", {}))
                self._set_job(
                    job_id,
                    status="done",
                    progress={"message": "Model ready", "percent": 100, "phase": "ready"},
                    result={"modelStatus": model_manager.status},
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Model preload failed")
                self._set_job(job_id, status="error", error=str(exc))
            finally:
                self._push_best_effort(
                    "window.__onModelStatus && window.__onModelStatus()"
                )

        threading.Thread(target=_run, daemon=True, name="rgc-preload").start()
        return {"ok": True, "job_id": job_id, "message": "Model download / load started."}

    # ── Archives ──────────────────────────────────────────────────────

    def list_creations(self) -> list[dict[str, Any]]:
        return self.store.load()

    def save_creation(self, creation: dict[str, Any]) -> dict[str, Any]:
        return self.store.upsert(creation)

    def delete_creation(self, creation_id: str) -> list[dict[str, Any]]:
        return self.store.delete(creation_id)

    def import_creations(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self.store.import_items(items)

    def export_creations_json(self) -> str:
        return self.store.export_json()

    # ── Generation ────────────────────────────────────────────────────

    def create_creation(self, game: str, platform: str, creation_type: str) -> dict[str, Any]:
        """Start generation in a background thread; UI must poll get_job(job_id)."""
        logger.info("create_creation requested: %s / %s / %s", game, platform, creation_type)

        if not game or not platform or not creation_type:
            return {
                "ok": False,
                "error": "game, platform, and creationType are required.",
            }

        if not self._gen_lock.acquire(blocking=False):
            return {"ok": False, "error": "A generation is already in progress."}

        job_id = f"gen_{uuid.uuid4().hex[:10]}"
        self._set_job(
            job_id,
            status="running",
            kind="generate",
            progress={
                "message": f"Starting generation for {game}…",
                "phase": "generate",
                "title": "Generating document",
            },
        )

        def _run() -> None:
            try:
                result = generate_creation(
                    game=game.strip(),
                    platform=platform.strip(),
                    creation_type=creation_type.strip(),
                    config=self.config,
                    progress=lambda payload: self._on_job_progress(job_id, payload),
                )
                saved = self.store.upsert(result)
                self._set_job(
                    job_id,
                    status="done",
                    result=saved,
                    progress={"message": "Document ready", "percent": 100, "phase": "ready"},
                )
                try:
                    payload = json.dumps(saved, ensure_ascii=False)
                    self._push_best_effort(
                        f"window.__onGenerationComplete && window.__onGenerationComplete({payload})"
                    )
                except (TypeError, ValueError):
                    self._push_best_effort(
                        f"window.__onGenerationComplete && window.__onGenerationComplete("
                        f"JSON.parse({json.dumps(json.dumps(saved))}))"
                    )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Generation failed")
                err = str(exc)
                if "torch" in err.lower() or isinstance(exc, ModuleNotFoundError):
                    err = (
                        f"{exc}\n\nFor local HF backend install:\n"
                        "  pip install -r requirements-local.txt\n"
                        "Or switch backend to Gemini in Control Panel."
                    )
                self._set_job(job_id, status="error", error=err)
                self._push_best_effort(
                    f"window.__onGenerateError && window.__onGenerateError({json.dumps(err)})"
                )
            finally:
                self._gen_lock.release()

        threading.Thread(target=_run, daemon=True, name="rgc-generate").start()
        return {"ok": True, "job_id": job_id, "message": "Generation started."}

    def _on_job_progress(self, job_id: str, payload: Any) -> None:
        if isinstance(payload, str):
            data: dict[str, Any] = {"message": payload}
        elif isinstance(payload, dict):
            data = payload
        else:
            data = {"message": str(payload)}
        self._set_job(job_id, progress=data)
        self._push_best_effort(
            f"window.__onProgress && window.__onProgress({json.dumps(data)})"
        )

    def _push_best_effort(self, script: str) -> None:
        """Try evaluate_js; never raise — JS polling is the source of truth."""
        if self._window is None:
            return
        try:
            self._window.evaluate_js(script)
        except Exception:  # noqa: BLE001
            logger.debug("evaluate_js failed (UI should poll get_job)", exc_info=True)

    def export_creation_txt(self, creation: dict[str, Any]) -> str:
        """Render a plain-text document for save-as."""
        lines: list[str] = []
        lines.append(f"{creation.get('game', '')} — {creation.get('creationType', '')}")
        lines.append(f"Platform: {creation.get('platform', '')}")
        lines.append("=" * 60)
        meta = creation.get("meta") or {}
        for key in (
            "releaseYear",
            "developer",
            "publisher",
            "designer",
            "genre",
            "mediaFormat",
            "systemRequirements",
        ):
            if meta.get(key):
                lines.append(f"{key}: {meta[key]}")
        lines.append("")
        lines.append(creation.get("overview") or "")
        lines.append("")
        for section in creation.get("sections") or []:
            lines.append("-" * 40)
            lines.append(section.get("title") or "Section")
            lines.append(section.get("content") or "")
            for kv in section.get("keyValues") or []:
                lines.append(f"  • {kv.get('label', '')}: {kv.get('value', '')}")
            lines.append("")
        if creation.get("accuracyNote"):
            lines.append(f"Accuracy: {creation['accuracyNote']}")
        model_info = creation.get("_model") or {}
        if model_info.get("repo_id"):
            lines.append(f"Generated with: {model_info['repo_id']}")
        return "\n".join(lines)

    def save_file_dialog(self, default_name: str, content: str) -> dict[str, Any]:
        """Open a native save dialog and write text content."""
        import webview

        if self._window is None:
            return {"ok": False, "error": "No window"}
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
        )
        if not result:
            return {"ok": False, "cancelled": True}
        path = Path(result if isinstance(result, str) else result[0])
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(path)}

    def save_binary_file_dialog(self, default_name: str, base64_data: str) -> dict[str, Any]:
        """Open a native save dialog and write base64-decoded bytes (PNG/PDF)."""
        import base64
        import webview

        if self._window is None:
            return {"ok": False, "error": "No window"}
        if not isinstance(base64_data, str) or not base64_data:
            return {"ok": False, "error": "Empty payload"}

        # Allow data URLs: data:image/png;base64,AAAA…
        payload = base64_data
        if "," in payload and payload.strip().lower().startswith("data:"):
            payload = payload.split(",", 1)[1]

        try:
            raw = base64.b64decode(payload, validate=False)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"Invalid base64: {exc}"}

        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
        )
        if not result:
            return {"ok": False, "cancelled": True}
        path = Path(result if isinstance(result, str) else result[0])
        path.write_bytes(raw)
        return {"ok": True, "path": str(path)}

    def open_json_import(self) -> dict[str, Any]:
        import webview

        if self._window is None:
            return {"ok": False, "error": "No window"}
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=("JSON Files (*.json)",),
        )
        if not result:
            return {"ok": False, "cancelled": True}

        imported: list[dict[str, Any]] = []
        paths = result if isinstance(result, (list, tuple)) else [result]
        for p in paths:
            try:
                data = json.loads(Path(p).read_text(encoding="utf-8"))
                if isinstance(data, list):
                    imported.extend(data)
                elif isinstance(data, dict):
                    imported.append(data)
            except (OSError, json.JSONDecodeError) as exc:
                return {"ok": False, "error": f"Failed to read {p}: {exc}"}

        creations = self.store.import_items(imported)
        return {"ok": True, "creations": creations, "imported": len(imported)}
