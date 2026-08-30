"""Tests for Gemini built-in file tools and function-call helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import subprocess

from retro_98_ai_creator.config import DEFAULTS
from retro_98_ai_creator.gemini_tools import (
    MAX_FILE_BYTES,
    execute_tool,
    extract_function_calls,
    function_declarations_for,
    list_tool_catalog,
    normalize_tool_aliases,
    response_text,
    tools_config_for,
)
from retro_98_ai_creator.prompts import build_general_text_prompt, local_clock_context


def test_use_tools_default_is_false():
    assert DEFAULTS["gemini"]["use_tools"] is False


def test_catalog_aliases():
    aliases = [t["alias"] for t in list_tool_catalog()]
    assert aliases == [
        "read_json",
        "write_json",
        "read_text",
        "write_text",
        "execute_powershell",
        "search_gmail",
        "search_drive",
        "create_drive_file",
        "read_google_doc",
        "create_google_doc",
        "edit_google_doc",
        "list_calendar_events",
        "create_calendar_event",
        "edit_calendar_event",
        "list_tasks",
        "create_task",
        "edit_task",
        "browse_web",
    ]


def test_normalize_tool_aliases_filters_and_orders():
    assert normalize_tool_aliases(["write_text", "nope", "read_json", "read_json"]) == [
        "read_json",
        "write_text",
    ]
    assert normalize_tool_aliases(None) == []


def test_execute_read_write_json(tmp_path: Path):
    src = tmp_path / "in.json"
    dest = tmp_path / "out.json"
    src.write_text(json.dumps({"a": 1, "date": "1999-01-01"}), encoding="utf-8")

    read = execute_tool("read_json", {"path": str(src.resolve())})
    assert read["ok"] is True
    assert read["data"]["a"] == 1

    write = execute_tool(
        "write_json",
        {"path": str(dest.resolve()), "data": {"a": 1, "filtered": True}},
    )
    assert write["ok"] is True
    assert json.loads(dest.read_text(encoding="utf-8"))["filtered"] is True


def test_execute_read_write_text(tmp_path: Path):
    src = tmp_path / "in.txt"
    dest = tmp_path / "nested" / "out.txt"
    src.write_text("hello tools", encoding="utf-8")

    read = execute_tool("read_text", {"path": str(src.resolve())})
    assert read["ok"] is True
    assert read["text"] == "hello tools"

    write = execute_tool(
        "write_text", {"path": str(dest.resolve()), "text": "written"}
    )
    assert write["ok"] is True
    assert dest.read_text(encoding="utf-8") == "written"


def test_execute_rejects_relative_path():
    result = execute_tool("read_text", {"path": "relative.txt"})
    assert result["ok"] is False
    assert "absolute" in result["error"].lower()


def test_execute_missing_file(tmp_path: Path):
    missing = tmp_path / "nope.json"
    result = execute_tool("read_json", {"path": str(missing.resolve())})
    assert result["ok"] is False
    assert "not found" in result["error"].lower()


def test_execute_invalid_json(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = execute_tool("read_json", {"path": str(bad.resolve())})
    assert result["ok"] is False
    assert "json" in result["error"].lower()


def test_execute_oversized_file(tmp_path: Path):
    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    result = execute_tool("read_text", {"path": str(big.resolve())})
    assert result["ok"] is False
    assert "too large" in result["error"].lower()


def test_unknown_tool():
    result = execute_tool("launch_missiles", {"path": "C:/x"})
    assert result["ok"] is False
    assert "unknown" in result["error"].lower()


def test_execute_search_gmail_delegates():
    with patch(
        "retro_98_ai_creator.gmail_client.search_gmail",
        return_value={"ok": True, "query": "is:unread", "count": 0, "messages": []},
    ) as mock_search:
        result = execute_tool("search_gmail", {"query": "is:unread"})
    mock_search.assert_called_once_with(
        "is:unread",
        max_results=None,
        include_body=False,
    )
    assert result["ok"] is True


def test_execute_search_drive_delegates():
    with patch(
        "retro_98_ai_creator.drive_client.search_drive",
        return_value={"ok": True, "query": "name contains 'x'", "count": 0, "files": []},
    ) as mock_search:
        result = execute_tool("search_drive", {"query": "name contains 'x'"})
    mock_search.assert_called_once_with(
        "name contains 'x'",
        max_results=None,
        mime_type=None,
    )
    assert result["ok"] is True


def test_execute_create_google_doc_delegates():
    with patch(
        "retro_98_ai_creator.docs_client.create_google_doc",
        return_value={"ok": True, "document_id": "d1", "title": "Notes"},
    ) as mock_create:
        result = execute_tool(
            "create_google_doc", {"title": "Notes", "text": "hello"}
        )
    mock_create.assert_called_once_with("Notes", text="hello")
    assert result["ok"] is True


def test_execute_list_calendar_events_delegates():
    with patch(
        "retro_98_ai_creator.calendar_client.list_calendar_events",
        return_value={"ok": True, "count": 0, "events": []},
    ) as mock_list:
        result = execute_tool(
            "list_calendar_events",
            {"time_min": "2026-08-30T00:00:00Z", "max_results": 5},
        )
    mock_list.assert_called_once_with(
        time_min="2026-08-30T00:00:00Z",
        time_max=None,
        max_results=5,
        calendar_id=None,
        query=None,
    )
    assert result["ok"] is True


def test_execute_create_task_delegates():
    with patch(
        "retro_98_ai_creator.tasks_client.create_task",
        return_value={"ok": True, "id": "t1", "title": "Buy milk"},
    ) as mock_create:
        result = execute_tool(
            "create_task",
            {"title": "Buy milk", "due": "2026-08-30T00:00:00.000Z"},
        )
    mock_create.assert_called_once_with(
        "Buy milk",
        notes=None,
        due="2026-08-30T00:00:00.000Z",
        tasklist_id=None,
    )
    assert result["ok"] is True


def test_execute_browse_web_delegates():
    with patch(
        "retro_98_ai_creator.web_browse.browse_web",
        return_value={"ok": True, "url": "https://example.com/", "text": "Hello", "links": []},
    ) as mock_browse:
        result = execute_tool(
            "browse_web",
            {"url": "https://example.com/", "include_links": True, "max_chars": 1000},
        )
    mock_browse.assert_called_once_with(
        "https://example.com/",
        include_links=True,
        max_chars=1000,
    )
    assert result["ok"] is True


def test_execute_powershell_returns_stdout(tmp_path: Path):
    script = tmp_path / "getdir.ps1"
    script.write_text("Write-Output 'line-one'", encoding="utf-8")
    fake = subprocess.CompletedProcess(
        args=["powershell.exe"],
        returncode=0,
        stdout=b"line-one\r\n",
        stderr=b"",
    )
    with (
        patch("retro_98_ai_creator.gemini_tools.sys.platform", "win32"),
        patch("retro_98_ai_creator.gemini_tools.subprocess.run", return_value=fake),
    ):
        result = execute_tool(
            "execute_powershell",
            {"path": str(script.resolve())},
        )
    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert "line-one" in result["stdout"]
    assert result["stderr"] == ""


def test_execute_powershell_nonzero_exit_still_returns_output(tmp_path: Path):
    script = tmp_path / "fail.ps1"
    script.write_text("Write-Error 'oops'", encoding="utf-8")
    fake = subprocess.CompletedProcess(
        args=["powershell.exe"],
        returncode=1,
        stdout=b"",
        stderr=b"oops\r\n",
    )
    with (
        patch("retro_98_ai_creator.gemini_tools.sys.platform", "win32"),
        patch("retro_98_ai_creator.gemini_tools.subprocess.run", return_value=fake),
    ):
        result = execute_tool(
            "execute_powershell",
            {"path": str(script.resolve())},
        )
    assert result["ok"] is False
    assert result["exit_code"] == 1
    assert "oops" in result["stderr"]


def test_execute_powershell_requires_ps1_extension(tmp_path: Path):
    script = tmp_path / "getdir.bat"
    script.write_text("@echo off", encoding="utf-8")
    with patch("retro_98_ai_creator.gemini_tools.sys.platform", "win32"):
        result = execute_tool("execute_powershell", {"path": str(script.resolve())})
    assert result["ok"] is False
    assert ".ps1" in result["error"]


def test_function_declarations_build():
    decls = function_declarations_for(["read_json", "write_json"])
    assert len(decls) == 2
    assert decls[0].name == "read_json"
    assert decls[1].name == "write_json"


def test_extract_function_calls_and_text():
    response = SimpleNamespace(
        text=None,
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            function_call=SimpleNamespace(
                                name="read_json",
                                args={"path": r"C:\data\a.json"},
                            ),
                            text=None,
                        )
                    ]
                )
            )
        ],
    )
    calls = extract_function_calls(response)
    assert calls == [("read_json", {"path": r"C:\data\a.json"})]
    assert response_text(response) == ""

    text_response = SimpleNamespace(
        text="  All done.  ",
        candidates=[],
    )
    assert response_text(text_response) == "All done."


def test_build_general_text_prompt_includes_tools():
    prompt = build_general_text_prompt(
        "Use read_json on c:\\a.json",
        tool_aliases=["read_json", "write_json"],
    )
    assert "AVAILABLE TOOLS" in prompt
    assert "read_json" in prompt
    assert "write_json" in prompt
    assert "Google Search grounding is enabled" not in prompt


def test_build_general_text_prompt_mentions_search_when_enabled():
    prompt = build_general_text_prompt(
        "Search then write_json",
        tool_aliases=["write_json"],
        with_search=True,
    )
    assert "Google Search grounding is enabled" in prompt
    assert "full source URLs" in prompt


def test_tools_config_includes_search_when_requested():
    tools = tools_config_for(["read_json"], with_search=True)
    assert tools is not None
    assert len(tools) == 2
    assert getattr(tools[0], "google_search", None) is not None
    assert tools[1].function_declarations
    assert tools[1].function_declarations[0].name == "read_json"


def test_build_general_text_prompt_includes_research_context():
    prompt = build_general_text_prompt(
        "Write step1.json",
        tool_aliases=["write_json"],
        research_context="Found https://example.com/bindings with full PS4 map.",
    )
    assert "WEB RESEARCH FINDINGS" in prompt
    assert "https://example.com/bindings" in prompt
    assert "Do not invent URLs" in prompt


_FROZEN_NOW = datetime(
    2026, 8, 30, 7, 58, 0, tzinfo=timezone(timedelta(hours=-6), "MDT")
)


def test_local_clock_frozen_upcoming_wednesday():
    text = local_clock_context(
        _FROZEN_NOW, include_calendar=True, include_tasks=True
    )
    assert "Sunday 2026-08-30" in text
    assert "Wednesday 2026-09-02" in text
    assert "2026-08-30T07:58:00-06:00" in text
    assert "2026-09-02T09:45:00-06:00" in text
    assert "UTC-06:00" in text
    assert "discarded" not in text.lower()
    assert "midnight UTC" not in text


def test_calendar_tools_inject_local_clock():
    user = (
        'create_calendar_event add a meeting named "fire jim jim" '
        "on this coming Wednesday at 9:45am"
    )
    prompt = build_general_text_prompt(
        user,
        tool_aliases=["create_calendar_event"],
        now=_FROZEN_NOW,
    )
    assert "LOCAL CLOCK" in prompt
    assert "RFC3339" in prompt
    assert "Wednesday 2026-09-02" in prompt
    assert "not Z" in prompt
    assert user in prompt
    assert "Tasks:" not in prompt.split("USER PROMPT:")[0]


def test_task_tools_inject_local_clock():
    user = "create a task due this coming Wednesday"
    prompt = build_general_text_prompt(
        user,
        tool_aliases=["create_task"],
        now=_FROZEN_NOW,
    )
    header = prompt.split("USER PROMPT:")[0]
    assert "LOCAL CLOCK" in prompt
    assert "Wednesday 2026-09-02" in prompt
    assert "09:45:00-06:00" in prompt
    assert "not Z" in prompt
    assert "00:00:00.000Z" not in prompt
    assert "discarded" not in header.lower()
    assert "midnight UTC" not in header
    assert user in prompt
    assert "Calendar:" not in header


def test_list_tasks_injects_local_clock():
    prompt = build_general_text_prompt(
        "list my tasks due tomorrow",
        tool_aliases=["list_tasks"],
        now=_FROZEN_NOW,
    )
    assert "LOCAL CLOCK" in prompt
    assert "Wednesday 2026-09-02" in prompt


def test_gmail_tools_inject_local_clock():
    user = "search mail from yesterday"
    prompt = build_general_text_prompt(
        user,
        tool_aliases=["search_gmail"],
        now=_FROZEN_NOW,
    )
    header = prompt.split("USER PROMPT:")[0]
    assert "LOCAL CLOCK" in prompt
    assert "after:" in prompt
    assert "newer_than:" in prompt
    assert "after:2026/08/29" in prompt
    assert "Wednesday 2026-09-02" in prompt
    assert user in prompt
    assert "Calendar:" not in header
    assert "Tasks:" not in header
    assert "Drive:" not in header
    assert "Docs:" not in header


def test_drive_tools_inject_local_clock():
    prompt = build_general_text_prompt(
        "find files I edited this week",
        tool_aliases=["search_drive"],
        now=_FROZEN_NOW,
    )
    header = prompt.split("USER PROMPT:")[0]
    assert "LOCAL CLOCK" in prompt
    assert "Drive:" in header
    assert "modifiedTime" in prompt
    assert "createdTime" in prompt
    assert "Wednesday 2026-09-02" in prompt
    assert "Calendar:" not in header
    assert "Gmail:" not in header


def test_docs_tools_inject_local_clock():
    prompt = build_general_text_prompt(
        "create today's notes",
        tool_aliases=["create_google_doc"],
        now=_FROZEN_NOW,
    )
    header = prompt.split("USER PROMPT:")[0]
    assert "LOCAL CLOCK" in prompt
    assert "Docs:" in header
    assert "Wednesday 2026-09-02" in prompt
    assert "Calendar:" not in header
    assert "Gmail:" not in header


def test_non_scheduling_tools_do_not_inject_clock():
    prompt = build_general_text_prompt(
        "read the file",
        tool_aliases=["read_json", "write_json"],
        now=_FROZEN_NOW,
    )
    assert "LOCAL CLOCK" not in prompt
    assert "Wednesday 2026-09-02" not in prompt


def test_function_declarations_include_local_clock():
    decls = function_declarations_for(
        ["create_calendar_event", "create_task"],
        now=_FROZEN_NOW,
    )
    assert len(decls) == 2
    for decl in decls:
        assert "LOCAL CLOCK" in decl.description
        assert "Wednesday 2026-09-02" in decl.description
    gmail_decls = function_declarations_for(["search_gmail"], now=_FROZEN_NOW)
    assert "LOCAL CLOCK" in gmail_decls[0].description
    assert "Wednesday 2026-09-02" in gmail_decls[0].description
    json_decls = function_declarations_for(["read_json"], now=_FROZEN_NOW)
    assert "LOCAL CLOCK" not in json_decls[0].description
    task_decls = function_declarations_for(
        ["create_task", "edit_task"], now=_FROZEN_NOW
    )
    for decl in task_decls:
        schema = json.dumps(decl.parameters_json_schema)
        blob = f"{decl.description}\n{schema}"
        assert "discarded" not in blob.lower()
        assert "midnight UTC" not in blob
        assert "00:00:00.000Z" not in blob
        assert "calendar date" not in blob.lower()
        assert "due date/time" in blob.lower() or "due date and time" in blob.lower()
        assert "not Z" in blob


def test_tool_loop_mock(tmp_path: Path):
    """Mock generate_content: function_call then final text."""
    from retro_98_ai_creator import gemini_provider as gp

    src = tmp_path / "step1.json"
    src.write_text(json.dumps({"items": [{"date": "1990-01-01"}]}), encoding="utf-8")

    fc_part = SimpleNamespace(
        function_call=SimpleNamespace(
            name="read_json",
            args={"path": str(src.resolve())},
        ),
        text=None,
    )
    model_content = SimpleNamespace(role="model", parts=[fc_part])
    first = SimpleNamespace(
        text=None,
        candidates=[SimpleNamespace(content=model_content)],
    )
    second = SimpleNamespace(
        text="Loaded JSON and ready.",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Loaded JSON and ready.")]
                )
            )
        ],
    )

    client = MagicMock()
    client.models.generate_content.side_effect = [first, second]

    with (
        patch.object(gp, "resolve_api_key", return_value="fake-key"),
        patch("google.genai.Client", return_value=client),
    ):
        result = gp._generate_text_with_gemini(
            "Prompt",
            "General",
            "Custom",
            gemini_cfg={
                "api_key": "fake-key",
                "use_tools": True,
                "google_search": False,
                "temperature": 0.0,
            },
            prompt_text=f"Use read_json on {src.resolve()}",
            model_name="gemini-2.5-flash",
            tool_aliases=["read_json", "write_json"],
        )

    assert result["modality"] == "text"
    assert result["sections"][0]["content"] == "Loaded JSON and ready."
    assert (result.get("_model") or {}).get("use_tools") is True
    assert (result.get("_model") or {}).get("tools") == ["read_json", "write_json"]
    assert client.models.generate_content.call_count == 2


def test_tool_loop_runs_when_aliases_sent_even_if_config_use_tools_false(tmp_path: Path):
    """Studio Enable Tools override sends aliases without Control Panel use_tools."""
    from retro_98_ai_creator import gemini_provider as gp

    src = tmp_path / "step1.json"
    src.write_text(json.dumps({"ok": True}), encoding="utf-8")

    fc_part = SimpleNamespace(
        function_call=SimpleNamespace(
            name="read_json",
            args={"path": str(src.resolve())},
        ),
        text=None,
    )
    first = SimpleNamespace(
        text=None,
        candidates=[SimpleNamespace(content=SimpleNamespace(role="model", parts=[fc_part]))],
    )
    second = SimpleNamespace(
        text="Done.",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Done.")]
                )
            )
        ],
    )
    client = MagicMock()
    client.models.generate_content.side_effect = [first, second]

    with (
        patch.object(gp, "resolve_api_key", return_value="fake-key"),
        patch("google.genai.Client", return_value=client),
    ):
        result = gp._generate_text_with_gemini(
            "Prompt",
            "General",
            "Custom",
            gemini_cfg={
                "api_key": "fake-key",
                "use_tools": False,
                "google_search": False,
                "temperature": 0.0,
            },
            prompt_text=f"Use read_json on {src.resolve()}",
            model_name="gemini-2.5-flash",
            tool_aliases=["read_json"],
        )

    assert (result.get("_model") or {}).get("use_tools") is True
    assert (result.get("_model") or {}).get("tools") == ["read_json"]
    assert client.models.generate_content.call_count == 2


def test_tools_with_search_uses_search_query_for_research():
    """Dedicated Search field text drives the research pass, not Tool Use."""
    from retro_98_ai_creator import gemini_provider as gp

    research = SimpleNamespace(
        text="Research brief",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Research brief")]
                ),
                grounding_metadata=None,
            )
        ],
    )
    final = SimpleNamespace(
        text="Done.",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Done.")]
                ),
                grounding_metadata=None,
            )
        ],
    )

    client = MagicMock()
    contents_seen: list[Any] = []

    def _side_effect(**kwargs):
        contents_seen.append(kwargs.get("contents"))
        if len(contents_seen) == 1:
            return research
        return final

    client.models.generate_content.side_effect = _side_effect

    with (
        patch.object(gp, "resolve_api_key", return_value="fake-key"),
        patch("google.genai.Client", return_value=client),
    ):
        gp._generate_text_with_gemini(
            "Prompt",
            "General",
            "Custom",
            gemini_cfg={
                "api_key": "fake-key",
                "use_tools": True,
                "google_search": True,
                "temperature": 0.0,
            },
            prompt_text="use write_json to save c:\\out\\result.json",
            model_name="gemini-pro-latest",
            tool_aliases=["write_json"],
            search_query="Watch Dogs PS4 DualShock bindings complete table",
        )

    research_contents = contents_seen[0]
    research_text = (
        research_contents
        if isinstance(research_contents, str)
        else str(research_contents)
    )
    assert "Watch Dogs PS4 DualShock bindings complete table" in research_text
    # Tool-loop prompt should still be the Tool Use text
    tool_contents = contents_seen[1]
    first_user = tool_contents[0]
    user_text = first_user.parts[0].text
    assert "use write_json to save" in user_text


def test_tools_with_search_skips_research_when_search_query_empty():
    """Blank Search skips the research pass; only the tool loop runs."""
    from retro_98_ai_creator import gemini_provider as gp

    final = SimpleNamespace(
        text="Done.",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Done.")]
                ),
                grounding_metadata=None,
            )
        ],
    )

    client = MagicMock()
    client.models.generate_content.return_value = final

    with (
        patch.object(gp, "resolve_api_key", return_value="fake-key"),
        patch("google.genai.Client", return_value=client),
    ):
        gp._generate_text_with_gemini(
            "Prompt",
            "General",
            "Custom",
            gemini_cfg={
                "api_key": "fake-key",
                "use_tools": True,
                "google_search": True,
                "temperature": 0.0,
            },
            prompt_text="use write_json to save c:\\out\\result.json",
            model_name="gemini-pro-latest",
            tool_aliases=["write_json"],
            search_query="",
        )

    assert client.models.generate_content.call_count == 1


def test_tools_with_search_runs_research_first():
    """Search+tools: dedicated Google Search research pass, then file-tool loop."""
    from retro_98_ai_creator import gemini_provider as gp

    research = SimpleNamespace(
        text="Research brief with https://ign.com/watch-dogs-ps4-controls",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            function_call=None,
                            text="Research brief with https://ign.com/watch-dogs-ps4-controls",
                        )
                    ]
                ),
                grounding_metadata=SimpleNamespace(
                    grounding_chunks=[
                        SimpleNamespace(
                            web=SimpleNamespace(
                                title="IGN",
                                uri="https://ign.com/watch-dogs-ps4-controls",
                            )
                        )
                    ],
                    search_entry_point=None,
                    web_search_queries=["watch dogs ps4 controls"],
                ),
            )
        ],
    )
    final = SimpleNamespace(
        text="Wrote step1.json from research.",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            function_call=None,
                            text="Wrote step1.json from research.",
                        )
                    ]
                ),
                grounding_metadata=None,
            )
        ],
    )

    client = MagicMock()
    configs: list[Any] = []

    def _side_effect(**kwargs):
        configs.append(kwargs.get("config"))
        # First call = research (search only); later = tools
        if len(configs) == 1:
            return research
        return final

    client.models.generate_content.side_effect = _side_effect

    with (
        patch.object(gp, "resolve_api_key", return_value="fake-key"),
        patch("google.genai.Client", return_value=client),
    ):
        result = gp._generate_text_with_gemini(
            "Prompt",
            "General",
            "Custom",
            gemini_cfg={
                "api_key": "fake-key",
                "use_tools": True,
                "google_search": True,
                "temperature": 0.0,
            },
            prompt_text="use write_json to save research to c:\\out\\step1.json",
            model_name="gemini-pro-latest",
            tool_aliases=["write_json"],
            search_query="Watch Dogs PS4 bindings complete table",
        )

    assert client.models.generate_content.call_count >= 2
    research_cfg = configs[0]
    tools_cfg = configs[1]
    assert research_cfg.tools is not None
    assert len(research_cfg.tools) == 2
    assert getattr(research_cfg.tools[0], "google_search", None) is not None
    assert getattr(research_cfg.tools[1], "url_context", None) is not None
    # Tool loop should be file tools only (no Google Search combo).
    assert tools_cfg.tools is not None
    assert getattr(tools_cfg.tools[0], "google_search", None) is None
    assert tools_cfg.tools[0].function_declarations[0].name == "write_json"
    assert (result.get("_model") or {}).get("google_search") is True
    assert (result.get("_model") or {}).get("search_first") is True
    assert result.get("groundingSources")
    assert result["groundingSources"][0]["url"] == "https://ign.com/watch-dogs-ps4-controls"
    assert "CITED SOURCES FROM GOOGLE SEARCH" in (result.get("researchBrief") or "")
    # Research brief must be injected into the tool-loop user prompt
    tool_contents = client.models.generate_content.call_args_list[1].kwargs["contents"]
    first_user = tool_contents[0]
    user_text = first_user.parts[0].text
    assert "WEB RESEARCH FINDINGS" in user_text
    assert "https://ign.com/watch-dogs-ps4-controls" in user_text


def test_tools_research_prompt_targets_complete_sources():
    from retro_98_ai_creator.prompts import build_tools_research_prompt

    text = build_tools_research_prompt(
        "step1 search then step2 filter sequels then write files"
    )
    assert "RESEARCH ONLY" in text
    assert "FULL control/binding table" in text
    assert "Ignore later pipeline steps" in text
    assert "multiple distinct searches" in text.lower() or "Run multiple distinct searches" in text
