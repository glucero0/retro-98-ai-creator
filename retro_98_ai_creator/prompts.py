"""Prompt templates and JSON schema for document generation."""

from __future__ import annotations

import json
from typing import Any

JSON_SCHEMA_HINT = """
{
  "game": "<official canonical game title — correct spelling & conventional capitalization>",
  "platform": "<platform>",
  "creationType": "<creation type>",
  "notFound": false,
  "ambiguous": false,
  "meta": {
    "releaseYear": "Actual 4-digit release year",
    "developer": "Actual developer studio",
    "publisher": "Actual publisher",
    "designer": "Actual lead designer or key creators",
    "genre": "Actual game genre",
    "mediaFormat": "Actual physical or digital format (Cartridge / Floppy / CD-ROM / etc.)",
    "systemRequirements": "Actual target console specs or hardware requirements"
  },
  "theme": {
    "themeName": "Authentic Theme Name",
    "bgColor": "#hex",
    "cardBg": "#hex",
    "textColor": "#hex",
    "accentColor": "#hex",
    "headerBg": "#hex",
    "fontStyle": "workbench | dos-vga | serif-parchment | pixel | retro-sans",
    "boxArtStyle": "Description of palette and branding style"
  },
  "overview": "Comprehensive 2-3 sentence overview.",
  "sections": [
    {
      "title": "Section Title",
      "content": "Detailed text describing game rules, lore, or guide.",
      "keyValues": [
        { "label": "Button / Key", "value": "In-Game Action" }
      ]
    }
  ],
  "accuracyNote": "Brief note on verified facts and sources."
}
""".strip()

SEARCH_EXTRACT_SCHEMA_HINT = """
{
  "game": "<official canonical game title — correct spelling & conventional capitalization>",
  "platform": "<platform>",
  "creationType": "<creation type>",
  "notFound": false,
  "ambiguous": false,
  "meta": {
    "releaseYear": "Actual 4-digit release year",
    "developer": "Actual developer studio",
    "publisher": "Actual publisher",
    "designer": "Actual lead designer or key creators",
    "genre": "Actual game genre",
    "mediaFormat": "Actual physical or digital format (Cartridge / Floppy / CD-ROM / etc.)",
    "systemRequirements": "Actual target console specs or hardware requirements"
  },
  "theme": {
    "themeName": "Authentic Theme Name",
    "bgColor": "#hex",
    "cardBg": "#hex",
    "textColor": "#hex",
    "accentColor": "#hex",
    "headerBg": "#hex",
    "fontStyle": "workbench | dos-vga | serif-parchment | pixel | retro-sans",
    "boxArtStyle": "Description of palette and branding style"
  },
  "overview": "Comprehensive 2-3 sentence overview.",
  "sections": [
    {
      "title": "Section Title",
      "content": "Detailed text describing game rules, lore, or guide.",
      "keyValues": [
        { "label": "Button / Key", "value": "In-Game Action" }
      ]
    }
  ],
  "accuracyNote": "Brief note on verified facts and sources.",
  "sourceSnippets": [
    {
      "source": "<page title or URL from search>",
      "quote": "<exact verbatim text snippet from the search result that supports a claim>"
    }
  ]
}
""".strip()

NOT_FOUND_SCHEMA_HINT = """
{
  "game": "Game Not Found",
  "platform": "<platform>",
  "creationType": "<creation type>",
  "notFound": true,
  "ambiguous": false,
  "meta": {
    "releaseYear": "",
    "developer": "",
    "publisher": "",
    "designer": "",
    "genre": "",
    "mediaFormat": "",
    "systemRequirements": ""
  },
  "theme": {
    "themeName": "Game Not Found",
    "bgColor": "#808080",
    "cardBg": "#c0c0c0",
    "textColor": "#000000",
    "accentColor": "#800000",
    "headerBg": "#000080",
    "fontStyle": "retro-sans",
    "boxArtStyle": "N/A"
  },
  "overview": "No known video game matches the user input with high confidence.",
  "sections": [],
  "accuracyNote": "Rejected ambiguous or unrecognized game title — no document generated."
}
""".strip()

AMBIGUOUS_SCHEMA_HINT = """
{
  "game": "Ambiguous",
  "platform": "<platform>",
  "creationType": "<creation type>",
  "notFound": false,
  "ambiguous": true,
  "candidates": [
    {
      "game": "<official canonical title 1>",
      "year": "YYYY",
      "platform": "<primary / best-known platform for this title>",
      "note": "<short distinguishing phrase, e.g. original WWII FPS>"
    },
    {
      "game": "<official canonical title 2>",
      "year": "YYYY",
      "platform": "<platform>",
      "note": "<short distinguishing phrase>"
    }
  ],
  "overview": "Multiple matching titles — user must choose.",
  "sections": [],
  "accuracyNote": "Ambiguous query — listed candidate titles for user selection."
}
""".strip()


def _platform_hardware_block(
    platform: str,
    platform_hardware: dict[str, Any] | None = None,
) -> str:
    """Serialize the selected platforms.json entry for inclusion in the prompt."""
    from .presets import platform_for

    entry = platform_hardware if platform_hardware is not None else platform_for(platform)
    if not entry:
        return ""
    payload = json.dumps(entry, indent=2, ensure_ascii=False)
    return (
        "\nPLATFORM HARDWARE (authoritative catalog for this selection — "
        "use these exact controller and button labels; do not mix other platforms):\n"
        f"{payload}"
    )


def build_tools_research_prompt(
    prompt: str,
    *,
    system_extra: str = "",
) -> str:
    """Search-only research brief used before the file-tool loop."""
    user = (prompt or "").strip()
    extra = (
        f"\n\nADDITIONAL USER INSTRUCTIONS:\n{system_extra.strip()}"
        if system_extra.strip()
        else ""
    )
    return (
        "You are a research assistant with Google Search grounding enabled.\n"
        "This pass is RESEARCH ONLY — do not write files and do not simulate later filter steps.\n"
        "\n"
        "How to search:\n"
        "- Infer the core lookup from the user task (game, platform, what data is needed).\n"
        "- Run multiple distinct searches when useful (official/manual, major guides, FAQs, "
        "secondary corroboration).\n"
        "- Prefer pages that publish a FULL control/binding table over short forum stubs.\n"
        "- If Url Context / page fetch is available, open the best candidate pages and extract "
        "complete tables from them.\n"
        "\n"
        "What to collect:\n"
        "- As many high-quality sources as Search can find for the ORIGINAL subject "
        "(e.g. original 2014 Watch Dogs on PlayStation 4 DualShock), not a minimal set.\n"
        "- For each useful source: full https URL, site name, game title, publisher, platform, "
        "and the COMPLETE binding list when the page has one (every face button, bumper, "
        "trigger, stick, D-pad direction, Options/Share/Touchpad, etc.).\n"
        "- Clearly label wrong-game, wrong-platform, or incomplete sources if you mention them; "
        "do not invent filler rows just to create filter fodder.\n"
        "- Do not invent facts, bindings, or URLs — only report what Search (and fetched pages) show.\n"
        "\n"
        "Ignore later pipeline steps in the user task (filtering sequels, removing incomplete "
        "rows, writing intermediate files) except as clues about what 'good' data looks like.\n"
        "If Search returns little that is complete, say so explicitly and still list every "
        "partial source with URL.\n"
        f"{extra}\n\n"
        f"USER TASK:\n{user}\n"
    )


def build_general_text_prompt(
    prompt: str,
    *,
    system_extra: str = "",
    tool_aliases: list[str] | None = None,
    with_search: bool = False,
    research_context: str = "",
) -> str:
    """Freeform studio text prompt (not game-manual JSON)."""
    user = (prompt or "").strip()
    extra = (
        f"\n\nADDITIONAL USER INSTRUCTIONS:\n{system_extra.strip()}"
        if system_extra.strip()
        else ""
    )
    tools = [a for a in (tool_aliases or []) if str(a).strip()]
    tools_block = ""
    if tools:
        names = ", ".join(tools)
        tools_block = (
            "\n\nAVAILABLE TOOLS:\n"
            f"You may call these tools by name when the user prompt requires them: {names}.\n"
            "Use absolute filesystem paths from the user prompt as tool arguments.\n"
            "Call tools as needed (for example read_json then write_json), then give a brief "
            "final text summary of what you did.\n"
        )
        if with_search and not (research_context or "").strip():
            tools_block += (
                "Google Search grounding is enabled. When the user asks you to search the "
                "internet or cite sources, use Search to find real pages, prefer primary/"
                "reputable sources, and include full source URLs in any JSON you write.\n"
                "Do not invent website names or bindings — ground them in Search results.\n"
            )
    research = (research_context or "").strip()
    research_block = ""
    if research:
        research_block = (
            "\n\nWEB RESEARCH FINDINGS (from Google Search — authoritative for this run):\n"
            f"{research}\n\n"
            "Base any write_json / write_text content on these findings. "
            "Do not invent URLs, bindings, or sources that are not supported above. "
            "If the findings are insufficient for a step, write what you can and note gaps "
            "in your final summary.\n"
        )
    return (
        "You are a general-purpose AI writing assistant.\n"
        "Respond directly to the user's prompt with high-quality text.\n"
        "You may use Markdown headings and lists when helpful.\n"
        "Do NOT wrap the entire answer in a JSON object unless the user explicitly asks for JSON.\n"
        f"{extra}{tools_block}{research_block}\n\n"
        f"USER PROMPT:\n{user}\n"
    )


def _shared_prompt_parts(
    game: str,
    platform: str,
    creation_type: str,
    *,
    system_extra: str = "",
    creation_description: str = "",
    platform_hardware: dict[str, Any] | None = None,
) -> dict[str, str]:
    description = (creation_description or "").strip()
    hardware_block = _platform_hardware_block(platform, platform_hardware)
    return {
        "extra": (
            f"\n\nADDITIONAL USER INSTRUCTIONS:\n{system_extra.strip()}"
            if system_extra.strip()
            else ""
        ),
        "description_block": (
            f'\nCREATION DESCRIPTION: "{description}"' if description else ""
        ),
        "hardware_block": hardware_block,
        "hardware_instruction": (
            " Use ONLY the controller/button names from PLATFORM HARDWARE when documenting "
            "controls or keybindings (e.g. PlayStation Cross/Square — never Xbox A/B on a PS platform)."
            if hardware_block
            else ""
        ),
        "description_instruction": (
            " Follow the CREATION DESCRIPTION closely for scope, tone, and section priorities."
            if description
            else ""
        ),
        "header": (
            "You are a retro gaming historian, archivist, and documentation master.\n"
            "The user is asking for an authentic reference creation for the following "
            "game and platform:\n\n"
            f'USER GAME INPUT: "{game}"\n'
            f'PLATFORM: "{platform}"\n'
            f'DESIRED CREATION: "{creation_type}"'
        ),
    }


def build_prompt(
    game: str,
    platform: str,
    creation_type: str,
    system_extra: str = "",
    *,
    creation_description: str = "",
    with_web_search: bool = False,
    exact_title: bool = False,
    platform_hardware: dict[str, Any] | None = None,
) -> str:
    """Build the user prompt for Gemini or local instruct models."""
    parts = _shared_prompt_parts(
        game,
        platform,
        creation_type,
        system_extra=system_extra,
        creation_description=creation_description,
        platform_hardware=platform_hardware,
    )

    if exact_title:
        accuracy_step = (
            f'1. The user already selected the exact title "{game}" on "{platform}" from a '
            f"search-results list. Treat this as a confirmed unique match. Do NOT return "
            f"ambiguous or notFound — generate the full document for this specific title."
        )
    elif with_web_search:
        accuracy_step = (
            f'1. Search the live web for matches for the game titled "{game}" on "{platform}". '
            f"Prefer official titles from Wikipedia / MobyGames / publisher materials. "
            f"When researching controls, match terminology to the PLATFORM HARDWARE catalog."
        )
    else:
        accuracy_step = (
            f'1. From your knowledge of video game history, decide whether "{game}" on '
            f'"{platform}" uniquely identifies a real game (allowing only clear '
            f"spelling/capitalization fixes of a known title)."
        )

    if exact_title:
        return f"""{parts["header"]}{parts["description_block"]}{parts["hardware_block"]}

CRITICAL INSTRUCTIONS FOR ACCURACY — CONFIRMED TITLE:
{accuracy_step}
2. You may apply only clear capitalization / conventional title formatting.
3. Do NOT invent a match from gibberish. If somehow this confirmed title is unknown, use Not Found.
4. Do NOT return the Ambiguous schema — the title is already chosen.
5. When generating: output the ACTUAL real-world developer, publisher, designers,
   release year, genre, media format, and hardware specs for that canonical game on "{platform}".
6. NEVER output placeholder credit strings like "Bethesda Game Studios / Studio",
   "Xbox Game Studios / Publisher", "Development Team", or "Commodore Amiga High Performance Mode"
   unless that studio genuinely made the game on that platform.
7. Produce a complete, detailed document corresponding to "{creation_type}".{parts["description_instruction"]}{parts["hardware_instruction"]}
8. You MUST return ONLY a single, raw, valid JSON object. Do NOT wrap in markdown fences.
   Do NOT add conversational intro text.

JSON SCHEMA (use this — notFound=false, ambiguous=false):
{JSON_SCHEMA_HINT}

Set platform="{platform}", creationType="{creation_type}".
Set "game" to the official canonical title for the selected game.
Respond with valid JSON only.{parts["extra"]}"""

    return f"""{parts["header"]}{parts["description_block"]}{parts["hardware_block"]}

CRITICAL INSTRUCTIONS FOR ACCURACY — NO GUESSING:
{accuracy_step}
2. You may fix ONLY clear typos / capitalization / conventional abbreviations of a known title.
   Allowed examples: "doom" → "Doom"; "final fantacy 7" → "Final Fantasy VII";
   "halo ce" → "Halo: Combat Evolved"; "monkey island" → "The Secret of Monkey Island".
3. Do NOT invent a match from gibberish, nonsense phrases, or loose phonetic similarity.
   If the input is not a recognizable game with high confidence, you MUST NOT pick a "closest"
   title (e.g. nonsense containing "hex" must NOT become "Hexen"). Use Not Found instead.
4. DISAMBIGUATION (required when multiple titles fit) — CHECK THIS BEFORE NOT FOUND:
   - Franchise / base names such as "call of duty", "final fantasy", "halo", "mario",
     "zelda", "resident evil", "pokemon", "sonic", "metal gear", "assassin's creed",
     "grand theft auto", "battlefield", "doom", "witcher", "dark souls" are AMBIGUOUS.
     Return the Ambiguous JSON with many official titles (include the original when it
     exists). Never answer Not Found for a well-known franchise base name.
   - If the input uniquely identifies one game with high confidence, use the Found schema.
5. Only if the input is gibberish / unrecognized (not a known franchise or title), return
   Game Not Found (notFound=true). Do not invent credits, lore, or sections.
6. When the game IS uniquely identified: output the ACTUAL real-world developer, publisher,
   designers, release year, genre, media format, and hardware specs for that canonical game
   on "{platform}".
7. NEVER output placeholder credit strings like "Bethesda Game Studios / Studio",
   "Xbox Game Studios / Publisher", "Development Team", or "Commodore Amiga High Performance Mode"
   unless that studio genuinely made the game on that platform.
8. When uniquely found: produce a complete, detailed document corresponding to "{creation_type}".{parts["description_instruction"]}{parts["hardware_instruction"]}
9. You MUST return ONLY a single, raw, valid JSON object. Do NOT wrap in markdown fences.
   Do NOT add conversational intro text.

JSON SCHEMA (unique game found — notFound=false, ambiguous=false):
{JSON_SCHEMA_HINT}

JSON SCHEMA (ambiguous — multiple matches; use this instead of guessing):
{AMBIGUOUS_SCHEMA_HINT}

JSON SCHEMA (game NOT found — use this instead):
{NOT_FOUND_SCHEMA_HINT}

Set platform="{platform}", creationType="{creation_type}".
If uniquely found, set "game" to the official canonical title.
If ambiguous, set ambiguous=true and fill candidates with official titles.
If not found, set game="Game Not Found" and notFound=true.
Respond with valid JSON only.{parts["extra"]}"""


def build_search_extract_prompt(
    game: str,
    platform: str,
    creation_type: str,
    system_extra: str = "",
    *,
    creation_description: str = "",
    exact_title: bool = False,
    platform_hardware: dict[str, Any] | None = None,
) -> str:
    """Pass 1: web search + extract candidate document with supporting snippets."""
    parts = _shared_prompt_parts(
        game,
        platform,
        creation_type,
        system_extra=system_extra,
        creation_description=creation_description,
        platform_hardware=platform_hardware,
    )

    if exact_title:
        identity_rules = f"""CRITICAL INSTRUCTIONS — CONFIRMED TITLE (PASS 1: SEARCH & EXTRACT):
1. The user already selected the exact title "{game}" on "{platform}". Treat this as a
   confirmed unique match. Do NOT return ambiguous or notFound.
2. Search the live web for official manuals, control settings menus, verified wiki tables,
   publisher docs, and primary sources for this title on "{platform}".
3. You may apply only clear capitalization / conventional title formatting."""
    else:
        identity_rules = f"""CRITICAL INSTRUCTIONS — PASS 1: SEARCH & EXTRACT:
1. Search the live web for matches for the game titled "{game}" on "{platform}".
   Prefer official titles from Wikipedia / MobyGames / publisher materials / manuals.
2. You may fix ONLY clear typos / capitalization / conventional abbreviations of a known title.
3. Do NOT invent a match from gibberish. If unrecognized, return Not Found.
4. DISAMBIGUATION: franchise / base names with multiple titles → Ambiguous schema
   (do not invent a full document or sourceSnippets for ambiguous queries).
5. Only if gibberish / unrecognized → Game Not Found (notFound=true)."""

    return f"""{parts["header"]}{parts["description_block"]}{parts["hardware_block"]}

{identity_rules}

PASS 1 EXTRACTION RULES (when a unique game is identified):
A. Produce a complete candidate "{creation_type}" document grounded in what you found.{parts["description_instruction"]}{parts["hardware_instruction"]}
B. Include sourceSnippets: an array of exact verbatim quotes copied from the search results
   that support key claims (especially every control / keybinding / cheat / fact you list).
   Each snippet must have "source" (title or URL) and "quote" (exact text, not paraphrased).
C. Prefer quoting over summarizing. If you cannot find a supporting quote for a claim,
   omit that claim from the candidate rather than inventing one — Pass 2 will strip guesses.
D. For controls/keybindings: map ONLY button→action pairs that appear explicitly in a quote.
   Use PLATFORM HARDWARE labels. Do not fill gaps with genre conventions.
E. You MUST return ONLY a single, raw, valid JSON object. No markdown fences.

JSON SCHEMA (unique game found — include sourceSnippets):
{SEARCH_EXTRACT_SCHEMA_HINT}

JSON SCHEMA (ambiguous — multiple matches):
{AMBIGUOUS_SCHEMA_HINT}

JSON SCHEMA (game NOT found):
{NOT_FOUND_SCHEMA_HINT}

Set platform="{platform}", creationType="{creation_type}".
Respond with valid JSON only.{parts["extra"]}"""


def build_verification_prompt(
    game: str,
    platform: str,
    creation_type: str,
    *,
    candidate_document: dict[str, Any],
    source_snippets: list[dict[str, str]],
    creation_description: str = "",
    platform_hardware: dict[str, Any] | None = None,
    system_extra: str = "",
) -> str:
    """Pass 2: verify candidate against raw snippets at temperature 0."""
    parts = _shared_prompt_parts(
        game,
        platform,
        creation_type,
        system_extra=system_extra,
        creation_description=creation_description,
        platform_hardware=platform_hardware,
    )
    # Avoid re-sending huge nested copies inside the candidate for the verify step
    candidate = dict(candidate_document)
    snippets = list(source_snippets or [])
    if not snippets and isinstance(candidate.get("sourceSnippets"), list):
        snippets = [
            {"source": str(s.get("source") or ""), "quote": str(s.get("quote") or "")}
            for s in candidate["sourceSnippets"]
            if isinstance(s, dict)
        ]
    candidate_json = json.dumps(candidate, indent=2, ensure_ascii=False)
    snippets_json = json.dumps(snippets, indent=2, ensure_ascii=False)

    return f"""{parts["header"]}{parts["description_block"]}{parts["hardware_block"]}

CRITICAL INSTRUCTIONS — PASS 2: VERIFICATION (temperature 0 — no guessing):
Review this {creation_type} against these raw search snippets. Remove or mark "Unverified"
for any information that is not 100% explicitly proven by the text snippets. Strip out any
assumed information.

RULES:
1. Keep a claim, keyValue, or detail ONLY when a raw snippet quote explicitly supports it.
2. If a control binding / fact appears in the candidate but is not proven by any quote,
   either remove it or set its value to "Unverified" (prefer "Unverified" for keyValues
   so gaps stay visible).
3. Do NOT add new facts from memory or genre conventions. Do NOT invent new snippets.
4. Preserve the document structure (meta/theme/sections/overview) but scrub unsupported
   content. Meta fields with no snippet support should be emptied or marked Unverified.
5. Keep sourceSnippets in the output (copy from the input list).
6. Update accuracyNote to state that Pass 2 verification ran against the provided snippets.
7. Use PLATFORM HARDWARE button labels only; never mix other platforms.{parts["hardware_instruction"]}
8. Return ONLY a single raw JSON object matching the Found schema (notFound=false,
   ambiguous=false). No markdown fences.

CANDIDATE DOCUMENT (Pass 1 output):
{candidate_json}

RAW SEARCH SNIPPETS:
{snippets_json}

JSON SCHEMA (verified document):
{SEARCH_EXTRACT_SCHEMA_HINT}

Set platform="{platform}", creationType="{creation_type}".
Respond with valid JSON only.{parts["extra"]}"""


SYSTEM_MESSAGE = (
    "You are a precise retro gaming documentation generator. "
    "Never guess a game title from ambiguous or nonsense input. "
    "If multiple real titles match the query (franchise / base name / ambiguity), "
    "return ambiguous=true with a candidates list of official titles. "
    "If the game cannot be identified with high confidence, return notFound=true "
    'with game="Game Not Found". '
    "When PLATFORM HARDWARE is provided, use those exact controller and button labels "
    "for controls documentation — never mix terminology from other platforms. "
    "When verifying against sourceSnippets, never keep unsupported claims. "
    "Always respond with a single valid JSON object and nothing else."
)
