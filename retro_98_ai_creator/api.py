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
from .gemini_provider import (
    SUGGESTED_GEMINI_MODELS,
    list_available_gemini_models,
    resolve_api_key as resolve_gemini_key,
)
from .creation_utils import AmbiguousGameError
from .generator import generate_creation, provider_status
from .openrouter_provider import (
    SUGGESTED_OPENROUTER_MODELS,
    resolve_api_key as resolve_openrouter_key,
)
from .presets import CREATION_TYPES, PLATFORM_OPTIONS, PLATFORMS, POPULAR_GAME_PRESETS
from .storage import ArchiveStore

logger = logging.getLogger(__name__)


class Api:
    """Methods on this class are callable from window.pywebview.api in the UI."""

    def __init__(self) -> None:
        self.config = load_config()
        self.store = ArchiveStore()
        self._window = None
        self._ui_origin: str | None = None
        self._gen_lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._jobs_lock = threading.Lock()
        self._cancel_events: dict[str, threading.Event] = {}

    def set_window(self, window) -> None:  # noqa: ANN001 — pywebview Window
        self._window = window

    def set_ui_origin(self, origin: str | None) -> None:
        """Localhost origin that serves UI + /media/ (for WebView-safe video URLs)."""
        self._ui_origin = (origin or "").rstrip("/") or None

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

    def check_modality_match(self, prompt: str = "") -> dict[str, Any]:
        """Preflight: can this prompt run on the active backend?"""
        from .generator import _active_model_and_provider
        from .modality import check_prompt_model_compatibility

        model_id, provider = _active_model_and_provider(self.config)
        result = check_prompt_model_compatibility(
            prompt or "",
            model_id,
            provider=provider,
            gemini_cfg=self.config.get("gemini") if provider == "gemini" else None,
            openrouter_cfg=(
                self.config.get("openrouter") if provider == "openrouter" else None
            ),
        )
        return result

    # ── Catalog / config ──────────────────────────────────────────────

    def get_bootstrap(self) -> dict[str, Any]:
        creations = self.store.load()
        return {
            "version": __version__,
            "config": self._public_config(),
            "suggestedModels": SUGGESTED_MODELS,
            "suggestedGeminiModels": SUGGESTED_GEMINI_MODELS,
            "suggestedOpenRouterModels": SUGGESTED_OPENROUTER_MODELS,
            "platforms": PLATFORM_OPTIONS,
            "hardwarePlatforms": PLATFORMS,
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
            gemini["api_key_set"] = bool(resolve_gemini_key(cfg.get("gemini") or {}))

        openrouter = dict(cfg.get("openrouter") or {})
        if openrouter.get("api_key"):
            openrouter["api_key_set"] = True
            openrouter["api_key"] = ""
        else:
            openrouter["api_key_set"] = bool(
                resolve_openrouter_key(cfg.get("openrouter") or {})
            )

        return {
            "backend": dict(cfg.get("backend") or {}),
            "gemini": gemini,
            "openrouter": openrouter,
            "huggingface": dict(cfg.get("huggingface") or {}),
            "prompt": dict(cfg.get("prompt") or {}),
            "ui": dict(cfg.get("ui") or {}),
            "paths": dict(cfg.get("paths") or {}),
        }

    def get_model_status(self) -> dict[str, Any]:
        return provider_status(self.config)

    def list_gemini_models(self) -> dict[str, Any]:
        """Fetch generateContent models available to the saved Gemini API key."""
        key = resolve_gemini_key(self.config.get("gemini") or {})
        if not key:
            return {
                "ok": False,
                "error": "Paste a Gemini API key and Save before refreshing the model list.",
                "models": SUGGESTED_GEMINI_MODELS,
                "source": "fallback",
            }
        try:
            models = list_available_gemini_models(key)
            return {
                "ok": True,
                "models": models,
                "source": "live",
                "count": len(models),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_gemini_models failed: %s", exc)
            return {
                "ok": False,
                "error": str(exc),
                "models": SUGGESTED_GEMINI_MODELS,
                "source": "fallback",
            }

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
        """Download / load local HF model (API backends need no download)."""
        provider = ((self.config.get("backend") or {}).get("provider") or "gemini").lower()
        if provider in ("gemini", "google", "google-gemini"):
            status = provider_status(self.config)
            return {
                "ok": True,
                "message": status.get("detail") or "Gemini uses the cloud API — no local download.",
                "modelStatus": status,
            }
        if provider in ("openrouter", "open-router", "or"):
            status = provider_status(self.config)
            return {
                "ok": True,
                "message": status.get("detail")
                or "OpenRouter uses the cloud API — no local download.",
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
                model_manager.ensure_loaded(self.config.get("huggingface") or {})
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

    def create_creation(
        self,
        game: str,
        platform: str,
        creation_type: str,
        exact_title: bool = False,
        creation_description: str = "",
    ) -> dict[str, Any]:
        """Start generation in a background thread; UI must poll get_job(job_id)."""
        logger.info(
            "create_creation requested: %s / %s / %s (exact=%s)",
            game,
            platform,
            creation_type,
            exact_title,
        )

        if not game or not platform or not creation_type:
            return {
                "ok": False,
                "error": "game, platform, and creationType are required.",
            }

        from .generator import _active_model_and_provider
        from .modality import check_prompt_model_compatibility

        desc_preview = (creation_description or "").strip() or game
        model_id, provider = _active_model_and_provider(self.config)
        compat = check_prompt_model_compatibility(
            desc_preview,
            model_id,
            provider=provider,
            gemini_cfg=self.config.get("gemini") if provider == "gemini" else None,
            openrouter_cfg=(
                self.config.get("openrouter") if provider == "openrouter" else None
            ),
        )
        if not compat.get("ok"):
            return {
                "ok": False,
                "error": compat.get("error") or "Model modality mismatch.",
                "modalityMismatch": True,
                "promptModality": compat.get("promptModality"),
                "modelModality": compat.get("modelModality"),
                "suggestions": compat.get("suggestions") or [],
            }

        if not self._gen_lock.acquire(blocking=False):
            return {"ok": False, "error": "A generation is already in progress."}

        job_id = f"gen_{uuid.uuid4().hex[:10]}"
        desc_override = (creation_description or "").strip()
        cancel_evt = threading.Event()
        with self._jobs_lock:
            self._cancel_events[job_id] = cancel_evt
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

        def _progress(payload: Any) -> None:
            from .cancellation import GenerationCancelled

            if cancel_evt.is_set():
                raise GenerationCancelled("Cancelled by user")
            self._on_job_progress(job_id, payload)

        def _run() -> None:
            from .cancellation import GenerationCancelled

            try:
                result = generate_creation(
                    game=game.strip(),
                    platform=platform.strip(),
                    creation_type=creation_type.strip(),
                    config=self.config,
                    progress=_progress,
                    exact_title=bool(exact_title),
                    creation_description=desc_override or None,
                    cancel_event=cancel_evt,
                )
                if cancel_evt.is_set():
                    raise GenerationCancelled("Cancelled by user")
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
            except GenerationCancelled:
                logger.info("Generation cancelled: %s", job_id)
                self._set_job(
                    job_id,
                    status="cancelled",
                    error="Cancelled",
                    progress={
                        "message": "Cancelled",
                        "percent": 100,
                        "phase": "cancelled",
                    },
                )
                self._push_best_effort(
                    "window.__onGenerateCancelled && window.__onGenerateCancelled()"
                )
            except AmbiguousGameError as exc:
                logger.info("Ambiguous game title: %s (%d candidates)", exc.user_game, len(exc.candidates))
                choice = {
                    "kind": "ambiguous",
                    "query": exc.user_game,
                    "candidates": exc.candidates,
                    "platform": platform.strip(),
                    "creationType": creation_type.strip(),
                }
                self._set_job(
                    job_id,
                    status="needs_choice",
                    result=choice,
                    progress={
                        "message": "Multiple matches — choose a title",
                        "percent": 100,
                        "phase": "choice",
                    },
                )
                try:
                    payload = json.dumps(choice, ensure_ascii=False)
                    self._push_best_effort(
                        f"window.__onNeedsChoice && window.__onNeedsChoice({payload})"
                    )
                except (TypeError, ValueError):
                    self._push_best_effort(
                        f"window.__onNeedsChoice && window.__onNeedsChoice("
                        f"JSON.parse({json.dumps(json.dumps(choice))}))"
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
                with self._jobs_lock:
                    self._cancel_events.pop(job_id, None)
                self._gen_lock.release()

        threading.Thread(target=_run, daemon=True, name="rgc-generate").start()
        return {"ok": True, "job_id": job_id, "message": "Generation started."}

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Request cancellation of a running generation (or model-load) job."""
        job_id = (job_id or "").strip()
        if not job_id:
            return {"ok": False, "error": "Missing job id"}
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return {"ok": False, "error": "Unknown job id"}
            status = str(job.get("status") or "")
            if status in ("done", "error", "cancelled", "needs_choice", "missing"):
                return {"ok": False, "error": f"Job already finished ({status})"}
            evt = self._cancel_events.get(job_id)
            if evt is None:
                return {"ok": False, "error": "Job is not cancellable"}
            evt.set()
            job["status"] = "cancelling"
            job["progress"] = {
                "message": "Cancelling…",
                "phase": "cancel",
                "title": "Cancelling",
            }
        logger.info("Cancel requested for job %s", job_id)
        return {"ok": True, "job_id": job_id, "message": "Cancel requested"}

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
        """Export only the generated text body (no prompt or metadata)."""
        modality = str((creation or {}).get("modality") or "text").lower()
        if modality in {"image", "video"}:
            raise RuntimeError(f"TXT export is not available for {modality} creations.")

        lines: list[str] = []
        overview = str(creation.get("overview") or "").strip()
        sections = creation.get("sections") or []
        skip_overview = False
        if overview and sections:
            body = str((sections[0] or {}).get("content") or "").strip()
            clipped = overview.rstrip("…").rstrip(".").strip()
            if body.startswith(clipped) or (
                str(creation.get("creationType") or "") == "Text" and body
            ):
                skip_overview = True
        if overview and not skip_overview:
            lines.append(overview)
            lines.append("")
        for section in sections:
            title = str((section or {}).get("title") or "").strip()
            hide_title = (not title) or (title.casefold() == "response")
            if not hide_title:
                lines.append(title)
                lines.append("")
            content = str((section or {}).get("content") or "")
            if content:
                lines.append(content)
            for kv in (section or {}).get("keyValues") or []:
                lines.append(f"  • {kv.get('label', '')}: {kv.get('value', '')}")
            lines.append("")
        return "\n".join(lines).strip() + ("\n" if lines else "")

    def get_media_payload(self, creation: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return media for Viewer: data URL (image) or http URL (video)."""
        from .media_store import media_data_url, media_file_uri, mime_for_path, resolve_media_path

        creation = creation or {}
        media_path = creation.get("mediaPath")
        mime = creation.get("mimeType")
        path = resolve_media_path(media_path)
        if path is None:
            return {"ok": False, "error": "Media file not found"}
        mime = mime or mime_for_path(path)
        modality = str(creation.get("modality") or "").lower()
        if modality == "video" or (mime or "").startswith("video/"):
            # Prefer same-origin HTTP URL — WebView blocks file:// from localhost pages.
            http_url = None
            if self._ui_origin:
                http_url = f"{self._ui_origin}/media/{path.name}"
            uri = http_url or media_file_uri(media_path)
            return {
                "ok": True,
                "modality": "video",
                "mimeType": mime,
                "fileUrl": uri,
                "mediaPath": media_path,
            }
        data_url = media_data_url(media_path, mime)
        if not data_url:
            return {"ok": False, "error": "Could not read media"}
        return {
            "ok": True,
            "modality": "image",
            "mimeType": mime,
            "dataUrl": data_url,
            "mediaPath": media_path,
        }

    def replace_creation_media(
        self, creation_id: str, base64_data: str, mime_type: str = "image/png"
    ) -> dict[str, Any]:
        """Overwrite a creation's media file from a base64 payload (Viewer Edit Apply)."""
        import base64

        from .media_store import write_media_bytes

        creation_id = (creation_id or "").strip()
        if not creation_id:
            return {"ok": False, "error": "Missing creation id"}
        items = self.store.load()
        target = next((c for c in items if c.get("id") == creation_id), None)
        if not target:
            return {"ok": False, "error": "Creation not found"}
        if str(target.get("modality") or "").lower() != "image":
            return {"ok": False, "error": "Only image creations can be edited this way"}

        payload = base64_data or ""
        if "," in payload and payload.strip().lower().startswith("data:"):
            header, payload = payload.split(",", 1)
            if "image/jpeg" in header or "image/jpg" in header:
                mime_type = "image/jpeg"
            elif "image/png" in header:
                mime_type = "image/png"
            elif "image/webp" in header:
                mime_type = "image/webp"
        try:
            raw = base64.b64decode(payload, validate=False)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"Invalid base64: {exc}"}
        if not raw:
            return {"ok": False, "error": "Empty image payload"}

        stored = write_media_bytes(
            creation_id, raw, mime_type=mime_type or "image/png", config=self.config
        )
        target = dict(target)
        target["mediaPath"] = stored["mediaPath"]
        target["mimeType"] = stored["mimeType"]
        target["modality"] = "image"
        saved = self.store.upsert(target)
        return {"ok": True, "creation": saved}

    def ffmpeg_status(self) -> dict[str, Any]:
        """Whether system ffmpeg/ffprobe are available for Video Edit."""
        from .video_edit import ffmpeg_available

        return ffmpeg_available()

    def get_video_info(self, creation_id: str) -> dict[str, Any]:
        """Return duration/size for a video creation."""
        from .media_store import resolve_media_path
        from .video_edit import FfmpegNotFoundError, probe_video_info

        creation_id = (creation_id or "").strip()
        target = next((c for c in self.store.load() if c.get("id") == creation_id), None)
        if not target:
            return {"ok": False, "error": "Creation not found"}
        if str(target.get("modality") or "").lower() != "video":
            return {"ok": False, "error": "Not a video creation"}
        path = resolve_media_path(target.get("mediaPath"))
        if path is None:
            return {"ok": False, "error": "Media file not found"}
        try:
            info = probe_video_info(path)
        except FfmpegNotFoundError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "creationId": creation_id, **info}

    def _render_edited_video(
        self, creation_id: str, ops: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any] | None, Path | None, Any]:
        """
        Resolve a video creation and render edits to a temp MP4.

        Returns (error_dict, dest_path, target_creation). On success error_dict is None
        and dest_path points at the rendered file (caller must delete it).
        """
        from .media_store import resolve_media_path
        from .video_edit import FfmpegNotFoundError, apply_edits, temp_mp4_path

        creation_id = (creation_id or "").strip()
        ops = ops or {}
        target = next((c for c in self.store.load() if c.get("id") == creation_id), None)
        if not target:
            return {"ok": False, "error": "Creation not found"}, None, None
        if str(target.get("modality") or "").lower() != "video":
            return {"ok": False, "error": "Only video creations can be edited this way"}, None, None
        path = resolve_media_path(target.get("mediaPath"))
        if path is None:
            return {"ok": False, "error": "Media file not found"}, None, None

        dest = temp_mp4_path("r98edit_")
        try:
            segments = ops.get("segments")
            if segments:
                from .video_edit import assemble_segments

                assemble_segments(
                    path,
                    dest,
                    list(segments),
                    filters=ops.get("filters"),
                    crop=ops.get("crop"),
                    rotation=float(ops.get("rotation") or 0),
                )
            else:
                apply_edits(
                    path,
                    dest,
                    filters=ops.get("filters"),
                    crop=ops.get("crop"),
                    rotation=float(ops.get("rotation") or 0),
                    trim=ops.get("trim"),
                )
            return None, dest, target
        except FfmpegNotFoundError as exc:
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass
            return {"ok": False, "error": str(exc)}, None, None
        except Exception as exc:  # noqa: BLE001
            logger.exception("render edited video failed")
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass
            return {"ok": False, "error": str(exc)}, None, None

    def edit_video(self, creation_id: str, ops: dict[str, Any] | None = None) -> dict[str, Any]:
        """Apply filters/crop/rotate/trim to a video creation and overwrite its media."""
        from .media_store import write_media_bytes

        err, dest, target = self._render_edited_video(creation_id, ops)
        if err is not None:
            return err
        assert dest is not None and target is not None
        try:
            raw = dest.read_bytes()
            stored = write_media_bytes(
                creation_id, raw, mime_type="video/mp4", config=self.config
            )
            target = dict(target)
            target["mediaPath"] = stored["mediaPath"]
            target["mimeType"] = stored["mimeType"]
            target["modality"] = "video"
            saved = self.store.upsert(target)
            return {"ok": True, "creation": saved}
        except Exception as exc:  # noqa: BLE001
            logger.exception("edit_video failed")
            return {"ok": False, "error": str(exc)}
        finally:
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass

    def export_edited_video(
        self, creation_id: str, ops: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Render video edits and save via a file dialog (does not overwrite Archives)."""
        import webview

        if self._window is None:
            return {"ok": False, "error": "No window"}

        err, dest, target = self._render_edited_video(creation_id, ops)
        if err is not None:
            return err
        assert dest is not None and target is not None
        try:
            title = (target.get("title") or target.get("game") or "video").strip()
            safe = (
                "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)[:40].strip()
                or "video"
            )
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=f"{safe}.mp4",
            )
            if not result:
                return {"ok": False, "cancelled": True}
            out = Path(result if isinstance(result, str) else result[0])
            out.write_bytes(dest.read_bytes())
            return {"ok": True, "path": str(out)}
        except Exception as exc:  # noqa: BLE001
            logger.exception("export_edited_video failed")
            return {"ok": False, "error": str(exc)}
        finally:
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass

    def split_video(self, creation_id: str, time_s: float) -> dict[str, Any]:
        """Split a video at time_s into two new library creations (A before, B after)."""
        import uuid

        from .creation_utils import build_media_creation, title_from_prompt
        from .media_store import resolve_media_path, write_media_bytes
        from .video_edit import FfmpegNotFoundError, split_at, temp_mp4_path

        creation_id = (creation_id or "").strip()
        target = next((c for c in self.store.load() if c.get("id") == creation_id), None)
        if not target:
            return {"ok": False, "error": "Creation not found"}
        if str(target.get("modality") or "").lower() != "video":
            return {"ok": False, "error": "Only video creations can be split"}
        path = resolve_media_path(target.get("mediaPath"))
        if path is None:
            return {"ok": False, "error": "Media file not found"}

        dest_a = temp_mp4_path("r98split_a_")
        dest_b = temp_mp4_path("r98split_b_")
        try:
            split_at(path, dest_a, dest_b, float(time_s))
            base_title = (
                target.get("title") or target.get("game") or title_from_prompt(target.get("prompt") or "")
            )
            prompt = target.get("prompt") or base_title
            model_info = target.get("_model")
            creations_out: list[dict[str, Any]] = []
            for label, dest in (("A", dest_a), ("B", dest_b)):
                cid = f"doc_{uuid.uuid4().hex[:10]}"
                stored = write_media_bytes(
                    cid, dest.read_bytes(), mime_type="video/mp4", config=self.config
                )
                creation = build_media_creation(
                    modality="video",
                    prompt=prompt,
                    media_path=stored["mediaPath"],
                    mime_type=stored["mimeType"],
                    title=f"{base_title} ({label})",
                    model_info=model_info if isinstance(model_info, dict) else None,
                    creation_id=cid,
                )
                creations_out.append(self.store.upsert(creation))
            return {"ok": True, "creations": creations_out}
        except FfmpegNotFoundError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            logger.exception("split_video failed")
            return {"ok": False, "error": str(exc)}
        finally:
            for p in (dest_a, dest_b):
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass

    def splice_videos(self, creation_ids: list[str] | None = None) -> dict[str, Any]:
        """Concatenate ordered video creations into a new library video."""
        import uuid

        from .creation_utils import build_media_creation
        from .media_store import resolve_media_path, write_media_bytes
        from .video_edit import FfmpegNotFoundError, concat_videos, temp_mp4_path

        ids = [str(i).strip() for i in (creation_ids or []) if str(i).strip()]
        if len(ids) < 2:
            return {"ok": False, "error": "Select at least two videos to splice"}

        items = self.store.load()
        by_id = {c.get("id"): c for c in items}
        paths: list[Path] = []
        titles: list[str] = []
        for cid in ids:
            target = by_id.get(cid)
            if not target:
                return {"ok": False, "error": f"Creation not found: {cid}"}
            if str(target.get("modality") or "").lower() != "video":
                return {"ok": False, "error": f"Not a video: {cid}"}
            path = resolve_media_path(target.get("mediaPath"))
            if path is None:
                return {"ok": False, "error": f"Media missing for {cid}"}
            paths.append(path)
            titles.append(str(target.get("title") or target.get("game") or cid))

        dest = temp_mp4_path("r98splice_")
        try:
            concat_videos(paths, dest)
            new_id = f"doc_{uuid.uuid4().hex[:10]}"
            stored = write_media_bytes(
                new_id, dest.read_bytes(), mime_type="video/mp4", config=self.config
            )
            title = " + ".join(titles)[:80]
            creation = build_media_creation(
                modality="video",
                prompt=f"Spliced: {title}",
                media_path=stored["mediaPath"],
                mime_type=stored["mimeType"],
                title=title or "Spliced Video",
                creation_id=new_id,
            )
            saved = self.store.upsert(creation)
            return {"ok": True, "creation": saved}
        except FfmpegNotFoundError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            logger.exception("splice_videos failed")
            return {"ok": False, "error": str(exc)}
        finally:
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass

    def export_creation_media(self, creation: dict[str, Any] | None = None) -> dict[str, Any]:
        """Save the native media file via a file dialog (PNG/JPEG/MP4/…)."""
        import webview

        from .media_store import extension_for_mime, mime_for_path, resolve_media_path

        if self._window is None:
            return {"ok": False, "error": "No window"}
        creation = creation or {}
        path = resolve_media_path(creation.get("mediaPath"))
        if path is None:
            return {"ok": False, "error": "Media file not found"}
        mime = creation.get("mimeType") or mime_for_path(path)
        ext = extension_for_mime(mime, fallback=path.suffix or ".bin")
        title = (creation.get("title") or creation.get("game") or "creation").strip()
        safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)[:40].strip() or "creation"
        default_name = f"{safe}{ext}"
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
        )
        if not result:
            return {"ok": False, "cancelled": True}
        dest = Path(result if isinstance(result, str) else result[0])
        dest.write_bytes(path.read_bytes())
        return {"ok": True, "path": str(dest)}

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

    def import_text_file(self, save_to_archives: bool = False) -> dict[str, Any]:
        """Open a text file for use as a Studio prompt / text basis."""
        import webview

        from .creation_utils import build_text_creation_from_plain

        if self._window is None:
            return {"ok": False, "error": "No window"}
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Text Files (*.txt;*.md;*.markdown;*.csv)", "All Files (*.*)"),
        )
        if not result:
            return {"ok": False, "cancelled": True}
        path = Path(result if isinstance(result, str) else result[0])
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        title = path.stem.strip() or "Imported text"
        out: dict[str, Any] = {
            "ok": True,
            "modality": "text",
            "text": text,
            "title": title,
            "path": str(path),
        }
        if save_to_archives:
            creation = build_text_creation_from_plain(
                text,
                prompt=f"Imported from {path.name}",
                title=title,
                model_info={"provider": "import", "repo_id": path.name},
            )
            out["creation"] = self.store.upsert(creation)
        return out

    def import_media_file(self, modality: str = "image") -> dict[str, Any]:
        """Import an image or video file into Archives as a new creation."""
        import uuid

        import webview

        from .creation_utils import build_media_creation
        from .media_store import mime_for_path, write_media_bytes
        from .modality import normalize_modality

        if self._window is None:
            return {"ok": False, "error": "No window"}
        mod = normalize_modality(modality, default="image")
        if mod not in {"image", "video"}:
            return {"ok": False, "error": "modality must be image or video"}

        if mod == "image":
            file_types = (
                "Image Files (*.png;*.jpg;*.jpeg;*.webp;*.gif;*.bmp)",
                "All Files (*.*)",
            )
        else:
            file_types = (
                "Video Files (*.mp4;*.webm;*.mov;*.mkv;*.avi)",
                "All Files (*.*)",
            )

        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types,
        )
        if not result:
            return {"ok": False, "cancelled": True}
        path = Path(result if isinstance(result, str) else result[0])
        if not path.is_file():
            return {"ok": False, "error": "File not found"}

        try:
            raw = path.read_bytes()
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        if not raw:
            return {"ok": False, "error": "Empty file"}

        mime = mime_for_path(path)
        if mod == "image" and not str(mime).startswith("image/"):
            mime = "image/png"
        if mod == "video" and not str(mime).startswith("video/"):
            mime = "video/mp4"

        new_id = f"doc_{uuid.uuid4().hex[:10]}"
        try:
            stored = write_media_bytes(
                new_id, raw, mime_type=mime, config=self.config
            )
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

        title = path.stem.strip() or ("Imported Image" if mod == "image" else "Imported Video")
        creation = build_media_creation(
            modality=mod,
            prompt=f"Imported from {path.name}",
            media_path=stored["mediaPath"],
            mime_type=stored["mimeType"],
            title=title,
            creation_id=new_id,
            model_info={"provider": "import", "repo_id": path.name, "modality": mod},
        )
        saved = self.store.upsert(creation)
        return {"ok": True, "creation": saved, "modality": mod}

    def duplicate_creation(self, creation_id: str) -> dict[str, Any]:
        """Clone a creation (and media file) so edits become a new Archive item."""
        import copy
        import uuid

        from .creation_utils import build_media_creation, build_text_creation_from_plain
        from .media_store import read_media_bytes, write_media_bytes

        creation_id = (creation_id or "").strip()
        source = next((c for c in self.store.load() if c.get("id") == creation_id), None)
        if not source:
            return {"ok": False, "error": "Creation not found"}

        mod = str(source.get("modality") or "text").lower()
        new_id = f"doc_{uuid.uuid4().hex[:10]}"
        title = str(source.get("title") or source.get("game") or "Untitled").strip()
        if not title.lower().endswith("(copy)"):
            title = f"{title} (copy)"

        if mod in {"image", "video"}:
            raw = read_media_bytes(source.get("mediaPath"), config=self.config)
            if not raw:
                return {"ok": False, "error": "Media file not found"}
            mime = source.get("mimeType") or (
                "video/mp4" if mod == "video" else "image/png"
            )
            stored = write_media_bytes(
                new_id, raw, mime_type=mime, config=self.config
            )
            creation = build_media_creation(
                modality=mod,
                prompt=str(source.get("prompt") or title),
                media_path=stored["mediaPath"],
                mime_type=stored["mimeType"],
                title=title,
                creation_id=new_id,
                model_info={"provider": "duplicate", "from": creation_id, "modality": mod},
            )
        else:
            body_parts: list[str] = []
            overview = (source.get("overview") or "").strip()
            if overview:
                body_parts.append(overview)
            for sec in source.get("sections") or []:
                if not isinstance(sec, dict):
                    continue
                st = (sec.get("title") or "").strip()
                sc = (sec.get("content") or "").strip()
                if st and sc:
                    body_parts.append(f"{st}\n{sc}")
                elif sc:
                    body_parts.append(sc)
                elif st:
                    body_parts.append(st)
            body = "\n\n".join(body_parts).strip() or "(empty)"
            creation = build_text_creation_from_plain(
                body,
                prompt=str(source.get("prompt") or title),
                title=title,
                model_info={"provider": "duplicate", "from": creation_id},
            )
            creation["id"] = new_id

        # Preserve useful metadata without sharing the same id
        for key in ("platform", "creationType", "theme", "meta", "accuracyNote"):
            if source.get(key) is not None and key not in creation:
                creation[key] = copy.deepcopy(source.get(key))

        saved = self.store.upsert(creation)
        return {"ok": True, "creation": saved}

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
