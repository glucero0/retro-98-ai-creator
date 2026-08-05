"""Application entry — pywebview + 98.css desktop UI."""

from __future__ import annotations

import json
import logging
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .api import Api
from .config import PROJECT_ROOT, load_config, save_config
from .media_store import media_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).resolve().parent / "ui"

# Shared with the localhost HTTP handler for large media uploads (avoids pywebview
# JS↔Python bridge size limits that blank the WebView on big data URLs).
_api_bridge: Api | None = None


class _AppRequestHandler(SimpleHTTPRequestHandler):
    """Serve the 98.css UI and project media/ over the same localhost origin."""

    ui_root: Path = UI_DIR
    media_root: Path = PROJECT_ROOT / "media"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.ui_root), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        logger.debug("ui-http: " + format, *args)

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path).path
        parsed = unquote(parsed)
        if parsed.startswith("/media/") or parsed == "/media":
            root = self.media_root.resolve()
            rel = parsed[len("/media") :].lstrip("/")
            if not rel or ".." in Path(rel).parts:
                return str(root / ".__denied__")
            candidate = (root / rel).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                return str(root / ".__denied__")
            return str(candidate)

        # Default: files under ui/
        root = self.ui_root.resolve()
        rel = parsed.lstrip("/")
        if not rel or rel.endswith("/"):
            rel = f"{rel}index.html".lstrip("/")
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return str(root / ".__denied__")
        return str(candidate)

    def end_headers(self) -> None:
        # Allow the WebView to cache/seek media from this origin.
        if urlparse(self.path).path.startswith("/media/"):
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "private, max-age=60")
        super().end_headers()

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in ("/api/replace-creation-media", "/api/save-media-file"):
            self.send_error(404, "Not Found")
            return
        if _api_bridge is None:
            self._send_json(503, {"ok": False, "error": "API not ready"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 80 * 1024 * 1024:
            self._send_json(400, {"ok": False, "error": "Invalid payload size"})
            return
        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object")
            if path == "/api/save-media-file":
                result = _api_bridge.save_binary_file_dialog(
                    str(data.get("defaultName") or "image.png"),
                    str(data.get("dataUrl") or data.get("base64") or ""),
                )
                status = 200 if result.get("ok") or result.get("cancelled") else 400
                self._send_json(status, result)
                return
            result = _api_bridge.replace_creation_media(
                str(data.get("creationId") or ""),
                str(data.get("dataUrl") or data.get("base64") or ""),
                str(data.get("mimeType") or "image/png"),
            )
            self._send_json(200 if result.get("ok") else 400, result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("media HTTP POST failed")
            self._send_json(500, {"ok": False, "error": str(exc)})


def _start_ui_server(
    media_root: Path | None = None,
) -> tuple[ThreadingHTTPServer, str, str]:
    """Serve UI + media over localhost. Returns (server, index_url, origin)."""
    media_root = (media_root or media_dir()).resolve()
    media_root.mkdir(parents=True, exist_ok=True)
    _AppRequestHandler.ui_root = UI_DIR
    _AppRequestHandler.media_root = media_root
    server = ThreadingHTTPServer(("127.0.0.1", 0), _AppRequestHandler)
    port = server.server_address[1]
    origin = f"http://127.0.0.1:{port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"{origin}/index.html", origin


def main() -> int:
    try:
        import webview
    except ImportError:
        print(
            "pywebview is required. Install with: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    cfg = load_config()
    ui_cfg = cfg.get("ui") or {}
    index = UI_DIR / "index.html"
    if not index.exists():
        print(f"UI not found at {index}", file=sys.stderr)
        return 1

    media_root = media_dir(cfg)
    server, url, origin = _start_ui_server(media_root)
    global _api_bridge
    api = Api()
    _api_bridge = api
    api.set_ui_origin(origin)
    width = max(900, int(ui_cfg.get("window_width") or 1280))
    height = max(600, int(ui_cfg.get("window_height") or 800))
    window = webview.create_window(
        title=ui_cfg.get("title") or "Retro 98 AI Creator",
        url=url,
        js_api=api,
        width=width,
        height=height,
        min_size=(900, 600),
        background_color="#008080",
    )
    api.set_window(window)

    last_size: tuple[int, int] = (width, height)
    size_persisted = False

    def _read_window_size() -> tuple[int, int] | None:
        """Best-effort outer size; returns None once the native window is gone."""
        try:
            gui = getattr(window, "gui", None)
            uid = getattr(window, "uid", None)
            if gui is not None and uid is not None and hasattr(gui, "get_size"):
                size = gui.get_size(uid)
                if not size or len(size) != 2:
                    return None
                w, h = int(size[0]), int(size[1])
            else:
                w = int(getattr(window, "width", 0) or 0)
                h = int(getattr(window, "height", 0) or 0)
            if w < 100 or h < 100:
                return None
            return w, h
        except (TypeError, ValueError, AttributeError, RuntimeError, OSError):
            return None

    def _remember_size() -> None:
        nonlocal last_size
        size = _read_window_size()
        if size:
            last_size = size

    def _persist_window_size() -> bool:
        """Write last-known outer window size into project config.yaml."""
        nonlocal last_size, size_persisted
        if size_persisted:
            return True
        try:
            _remember_size()
            w = max(900, last_size[0])
            h = max(600, last_size[1])
            api.config = save_config(
                {"ui": {"window_width": w, "window_height": h}},
                existing=api.config,
            )
            size_persisted = True
            logger.info("Saved window size %sx%s", w, h)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to persist window size")
        return True  # allow the window to close

    window.events.closing += _persist_window_size
    # Cache size while the GUI is alive — closing/finally may run after teardown
    if hasattr(window.events, "resized"):
        window.events.resized += _remember_size

    provider = (cfg.get("backend") or {}).get("provider") or "gemini"
    logger.info("Starting Retro 98 AI Creator")
    logger.info("UI: %s", url)
    logger.info("Media HTTP: %s/media/", origin)
    logger.info("Window: %sx%s", width, height)
    logger.info("Backend: %s", provider)
    if provider == "gemini":
        logger.info("Gemini text model: %s", (cfg.get("gemini") or {}).get("text_model"))
    elif provider == "openrouter":
        logger.info(
            "OpenRouter text model: %s",
            (cfg.get("openrouter") or {}).get("text_model"),
        )
    else:
        hf = cfg.get("huggingface") or {}
        logger.info(
            "HF models: text=%s image=%s video=%s",
            hf.get("text_model") or hf.get("repo_id"),
            hf.get("image_model"),
            hf.get("video_model"),
        )
    try:
        webview.start(debug=bool(ui_cfg.get("debug")))
    finally:
        # Fallback if closing event did not fire (abnormal shutdown)
        try:
            _persist_window_size()
        except Exception:  # noqa: BLE001
            pass
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
