"""Built-in Gemini function-calling tools (local file read/write and PowerShell)."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MiB
MAX_POWERSHELL_OUTPUT_BYTES = 2 * 1024 * 1024
POWERSHELL_TIMEOUT_SEC = 120
MAX_TOOL_ITERATIONS = 16

# Catalog: fixed aliases declared to Gemini when the user attaches them in Creator.
TOOL_CATALOG: list[dict[str, str]] = [
    {
        "alias": "read_json",
        "display_name": "Read JSON",
        "summary": "Read and parse a JSON file at an absolute path",
    },
    {
        "alias": "write_json",
        "display_name": "Write JSON",
        "summary": "Write JSON data to a file at an absolute path (overwrites)",
    },
    {
        "alias": "read_text",
        "display_name": "Read text",
        "summary": "Read a text file at an absolute path",
    },
    {
        "alias": "write_text",
        "display_name": "Write text",
        "summary": "Write text to a file at an absolute path (overwrites)",
    },
    {
        "alias": "execute_powershell",
        "display_name": "Execute PowerShell",
        "summary": "Run a .ps1 script at an absolute path; returns stdout, stderr, and exit code",
    },
]

_ALIAS_SET = {t["alias"] for t in TOOL_CATALOG}


def list_tool_catalog() -> list[dict[str, str]]:
    """Return a copy of the built-in tool catalog for UI / bootstrap."""
    return [dict(t) for t in TOOL_CATALOG]


def normalize_tool_aliases(aliases: list[str] | None) -> list[str]:
    """Dedupe and keep only known catalog aliases (stable catalog order)."""
    if not aliases:
        return []
    wanted = {str(a).strip() for a in aliases if str(a).strip()}
    return [t["alias"] for t in TOOL_CATALOG if t["alias"] in wanted]


def _require_absolute_path(path_str: str) -> Path:
    raw = (path_str or "").strip()
    if not raw:
        raise ValueError("path is required")
    p = Path(raw)
    if not p.is_absolute():
        raise ValueError(f"path must be absolute (got {raw!r})")
    # Reject empty / odd drive-relative forms after resolve where possible
    try:
        resolved = p.resolve(strict=False)
    except OSError as exc:
        raise ValueError(f"invalid path: {exc}") from exc
    if not resolved.is_absolute():
        raise ValueError(f"path must be absolute (got {raw!r})")
    return resolved


def _read_bytes_limited(path: Path) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(f"file not found: {path}")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValueError(
            f"file too large ({size} bytes); max is {MAX_FILE_BYTES} bytes"
        )
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(
            f"file too large ({len(data)} bytes); max is {MAX_FILE_BYTES} bytes"
        )
    return data


def _write_bytes(path: Path, data: bytes) -> None:
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(
            f"content too large ({len(data)} bytes); max is {MAX_FILE_BYTES} bytes"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _decode_output(raw: bytes) -> str:
    if not raw:
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _truncate_output(text: str, *, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    trimmed = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return trimmed + "\n…[output truncated]"


def _execute_powershell_script(
    script_path: Path,
    arguments: list[str] | None = None,
) -> dict[str, Any]:
    if sys.platform != "win32":
        return {
            "ok": False,
            "error": "execute_powershell is only available on Windows",
        }
    if script_path.suffix.lower() != ".ps1":
        return {
            "ok": False,
            "error": f"script must be a .ps1 file (got {script_path.name!r})",
        }
    if not script_path.is_file():
        return {"ok": False, "error": f"script not found: {script_path}"}

    args = [str(a) for a in (arguments or []) if str(a).strip()]
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        *args,
    ]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            timeout=POWERSHELL_TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "path": str(script_path),
            "error": f"script timed out after {POWERSHELL_TIMEOUT_SEC} seconds",
        }
    except OSError as exc:
        return {"ok": False, "error": f"failed to start PowerShell: {exc}"}

    stdout = _truncate_output(
        _decode_output(completed.stdout or b""),
        max_bytes=MAX_POWERSHELL_OUTPUT_BYTES,
    )
    stderr = _truncate_output(
        _decode_output(completed.stderr or b""),
        max_bytes=MAX_POWERSHELL_OUTPUT_BYTES,
    )
    exit_code = int(completed.returncode)
    result: dict[str, Any] = {
        "ok": exit_code == 0,
        "path": str(script_path),
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }
    if exit_code != 0:
        result["error"] = f"script exited with code {exit_code}"
    return result


def execute_tool(name: str, args: dict[str, Any] | None) -> dict[str, Any]:
    """Run a built-in tool; always returns a JSON-serializable result dict."""
    alias = (name or "").strip()
    params = dict(args or {})
    try:
        if alias not in _ALIAS_SET:
            return {"ok": False, "error": f"unknown tool: {alias!r}"}
        if alias == "read_json":
            path = _require_absolute_path(str(params.get("path") or ""))
            raw = _read_bytes_limited(path)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                return {"ok": False, "error": f"file is not valid UTF-8: {exc}"}
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                return {"ok": False, "error": f"invalid JSON: {exc}"}
            return {"ok": True, "path": str(path), "data": data}
        if alias == "write_json":
            path = _require_absolute_path(str(params.get("path") or ""))
            if "data" not in params:
                return {"ok": False, "error": "data is required"}
            try:
                encoded = json.dumps(
                    params["data"], ensure_ascii=False, indent=2
                ).encode("utf-8")
            except (TypeError, ValueError) as exc:
                return {"ok": False, "error": f"data is not JSON-serializable: {exc}"}
            _write_bytes(path, encoded)
            return {"ok": True, "path": str(path), "bytes_written": len(encoded)}
        if alias == "read_text":
            path = _require_absolute_path(str(params.get("path") or ""))
            raw = _read_bytes_limited(path)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                return {"ok": False, "error": f"file is not valid UTF-8: {exc}"}
            return {"ok": True, "path": str(path), "text": text}
        if alias == "write_text":
            path = _require_absolute_path(str(params.get("path") or ""))
            if "text" not in params:
                return {"ok": False, "error": "text is required"}
            text = params.get("text")
            if not isinstance(text, str):
                text = str(text)
            encoded = text.encode("utf-8")
            _write_bytes(path, encoded)
            return {"ok": True, "path": str(path), "bytes_written": len(encoded)}
        if alias == "execute_powershell":
            path = _require_absolute_path(str(params.get("path") or ""))
            raw_args = params.get("arguments")
            arguments: list[str] = []
            if raw_args is not None:
                if not isinstance(raw_args, list):
                    return {"ok": False, "error": "arguments must be an array of strings"}
                arguments = [str(a) for a in raw_args]
            return _execute_powershell_script(path, arguments)
        return {"ok": False, "error": f"unhandled tool: {alias!r}"}
    except Exception as exc:  # noqa: BLE001
        logger.info("Tool %s failed: %s", alias, exc)
        return {"ok": False, "error": str(exc)}


def function_declarations_for(aliases: list[str] | None) -> list[Any]:
    """Build google.genai FunctionDeclaration objects for the given aliases."""
    from google.genai import types

    selected = normalize_tool_aliases(aliases)
    decls: list[Any] = []
    for alias in selected:
        if alias == "read_json":
            decls.append(
                types.FunctionDeclaration(
                    name="read_json",
                    description=(
                        "Read a JSON file from an absolute filesystem path and "
                        "return the parsed data."
                    ),
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to a JSON file",
                            }
                        },
                        "required": ["path"],
                    },
                )
            )
        elif alias == "write_json":
            decls.append(
                types.FunctionDeclaration(
                    name="write_json",
                    description=(
                        "Write JSON-serializable data to an absolute filesystem "
                        "path (creates parent directories; overwrites existing files)."
                    ),
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path for the output JSON file",
                            },
                            "data": {
                                "description": "JSON-serializable value to write",
                            },
                        },
                        "required": ["path", "data"],
                    },
                )
            )
        elif alias == "read_text":
            decls.append(
                types.FunctionDeclaration(
                    name="read_text",
                    description=(
                        "Read a UTF-8 text file from an absolute filesystem path."
                    ),
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to a text file",
                            }
                        },
                        "required": ["path"],
                    },
                )
            )
        elif alias == "write_text":
            decls.append(
                types.FunctionDeclaration(
                    name="write_text",
                    description=(
                        "Write UTF-8 text to an absolute filesystem path "
                        "(creates parent directories; overwrites existing files)."
                    ),
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path for the output text file",
                            },
                            "text": {
                                "type": "string",
                                "description": "Text content to write",
                            },
                        },
                        "required": ["path", "text"],
                    },
                )
            )
        elif alias == "execute_powershell":
            decls.append(
                types.FunctionDeclaration(
                    name="execute_powershell",
                    description=(
                        "Run a PowerShell script (.ps1) at an absolute filesystem path. "
                        "Returns stdout, stderr, and exit_code in the tool response — "
                        "use stdout with write_text when saving script output to a file."
                    ),
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to a .ps1 script file",
                            },
                            "arguments": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional arguments passed to the script",
                            },
                        },
                        "required": ["path"],
                    },
                )
            )
    return decls


def tools_config_for(
    aliases: list[str] | None,
    *,
    with_search: bool = False,
) -> list[Any] | None:
    """Return GenerateContentConfig.tools list, or None if nothing to enable."""
    from google.genai import types

    tools: list[Any] = []
    if with_search:
        tools.append(types.Tool(google_search=types.GoogleSearch()))
    decls = function_declarations_for(aliases)
    if decls:
        tools.append(types.Tool(function_declarations=decls))
    return tools or None


def extract_function_calls(response: Any) -> list[tuple[str, dict[str, Any]]]:
    """Return [(name, args), ...] from a generate_content response."""
    calls: list[tuple[str, dict[str, Any]]] = []
    try:
        cands = getattr(response, "candidates", None) or []
        if not cands:
            return calls
        content = getattr(cands[0], "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            fc = getattr(part, "function_call", None)
            if not fc:
                continue
            name = getattr(fc, "name", None) or ""
            raw_args = getattr(fc, "args", None)
            if raw_args is None:
                args: dict[str, Any] = {}
            elif isinstance(raw_args, dict):
                args = dict(raw_args)
            else:
                # protobuf MapComposite / similar
                try:
                    args = dict(raw_args)
                except Exception:  # noqa: BLE001
                    args = {}
            if name:
                calls.append((str(name), args))
    except Exception:  # noqa: BLE001
        logger.debug("Could not parse function_call parts", exc_info=True)
    return calls


def response_text(response: Any) -> str:
    """Best-effort plain text from a generate_content response."""
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    try:
        cands = getattr(response, "candidates", None) or []
        if not cands:
            return ""
        parts = getattr(getattr(cands[0], "content", None), "parts", None) or []
        chunks: list[str] = []
        for part in parts:
            t = getattr(part, "text", None)
            if isinstance(t, str) and t:
                chunks.append(t)
        return "".join(chunks).strip()
    except Exception:  # noqa: BLE001
        return ""
