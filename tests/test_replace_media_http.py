"""HTTP replace-creation-media endpoint (large payloads bypass pywebview bridge)."""

from __future__ import annotations

import base64
import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import retro_98_ai_creator.app as app_mod


class _FakeApi:
    def replace_creation_media(self, creation_id, base64_data, mime_type="image/png"):
        assert creation_id == "c1"
        assert "data:image/png;base64," in base64_data
        assert mime_type == "image/png"
        return {"ok": True, "creation": {"id": "c1", "modality": "image"}}

    def save_binary_file_dialog(self, default_name, base64_data):
        assert default_name.endswith(".png")
        assert "data:image/png;base64," in base64_data or base64_data
        return {"ok": True, "path": "C:/tmp/out.png"}


def test_replace_creation_media_http_post(tmp_path):
    app_mod._api_bridge = _FakeApi()
    app_mod._AppRequestHandler.ui_root = tmp_path
    app_mod._AppRequestHandler.media_root = tmp_path
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")

    server = ThreadingHTTPServer(("127.0.0.1", 0), app_mod._AppRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        png = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("ascii")
        body = json.dumps(
            {
                "creationId": "c1",
                "dataUrl": f"data:image/png;base64,{png}",
                "mimeType": "image/png",
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request(
            "POST",
            "/api/replace-creation-media",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        assert resp.status == 200
        data = json.loads(raw.decode("utf-8"))
        assert data["ok"] is True
        assert data["creation"]["id"] == "c1"
    finally:
        server.shutdown()
        app_mod._api_bridge = None


def test_save_media_file_http_post(tmp_path):
    app_mod._api_bridge = _FakeApi()
    app_mod._AppRequestHandler.ui_root = tmp_path
    app_mod._AppRequestHandler.media_root = tmp_path
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")

    server = ThreadingHTTPServer(("127.0.0.1", 0), app_mod._AppRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        png = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("ascii")
        body = json.dumps(
            {
                "defaultName": "shot.png",
                "dataUrl": f"data:image/png;base64,{png}",
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request(
            "POST",
            "/api/save-media-file",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        assert resp.status == 200
        data = json.loads(raw.decode("utf-8"))
        assert data["ok"] is True
        assert data["path"].endswith("out.png")
    finally:
        server.shutdown()
        app_mod._api_bridge = None
