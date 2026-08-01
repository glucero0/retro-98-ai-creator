"""Application entry — pywebview + 98.css desktop UI."""

from __future__ import annotations

import logging
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .api import Api
from .config import PROJECT_ROOT, load_config, save_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).resolve().parent / "ui"


def _load_dotenv() -> None:
    """Load .env / .env.local if present (GEMINI_API_KEY, etc.)."""
    for name in (".env.local", ".env"):
        path = PROJECT_ROOT / name
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
        except OSError:
            pass


class _UIRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        logger.debug("ui-http: " + format, *args)


def _start_ui_server() -> tuple[ThreadingHTTPServer, str]:
    """Serve the 98.css UI over localhost (more reliable than file:// in WebView2)."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _UIRequestHandler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{port}/index.html"


def main() -> int:
    _load_dotenv()
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

    server, url = _start_ui_server()
    api = Api()
    width = max(900, int(ui_cfg.get("window_width") or 1280))
    height = max(600, int(ui_cfg.get("window_height") or 800))
    window = webview.create_window(
        title=ui_cfg.get("title") or "Game Base Ref Creator 98",
        url=url,
        js_api=api,
        width=width,
        height=height,
        min_size=(900, 600),
        background_color="#008080",
    )
    api.set_window(window)

    def _persist_window_size() -> bool:
        """Write current outer window size into project config.yaml."""
        try:
            w = int(getattr(window, "width", 0) or 0)
            h = int(getattr(window, "height", 0) or 0)
            if w < 100 or h < 100:
                return True
            w = max(900, w)
            h = max(600, h)
            api.config = save_config(
                {"ui": {"window_width": w, "window_height": h}},
                existing=api.config,
            )
            logger.info("Saved window size %sx%s", w, h)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to persist window size")
        return True  # allow the window to close

    window.events.closing += _persist_window_size

    provider = (cfg.get("backend") or {}).get("provider") or "gemini"
    logger.info("Starting Game Base Ref Creator 98")
    logger.info("UI: %s", url)
    logger.info("Window: %sx%s", width, height)
    logger.info("Backend: %s", provider)
    if provider == "gemini":
        logger.info("Gemini model: %s", (cfg.get("gemini") or {}).get("model"))
    else:
        logger.info("HF model: %s", (cfg.get("model") or {}).get("repo_id"))
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
