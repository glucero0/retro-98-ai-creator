"""Prompt templates and JSON schema for document generation."""

from __future__ import annotations

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


def build_prompt(
    game: str,
    platform: str,
    creation_type: str,
    system_extra: str = "",
    *,
    creation_description: str = "",
    with_web_search: bool = False,
    exact_title: bool = False,
) -> str:
    """Build the user prompt for Gemini or local instruct models."""
    extra = f"\n\nADDITIONAL USER INSTRUCTIONS:\n{system_extra.strip()}" if system_extra.strip() else ""
    description = (creation_description or "").strip()
    description_block = (
        f'\nCREATION DESCRIPTION: "{description}"'
        if description
        else ""
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
            f"Prefer official titles from Wikipedia / MobyGames / publisher materials."
        )
    else:
        accuracy_step = (
            f'1. From your knowledge of video game history, decide whether "{game}" on '
            f'"{platform}" uniquely identifies a real game (allowing only clear '
            f"spelling/capitalization fixes of a known title)."
        )

    description_instruction = (
        f" Follow the CREATION DESCRIPTION closely for scope, tone, and section priorities."
        if description
        else ""
    )

    if exact_title:
        return f"""You are a retro gaming historian, archivist, and documentation master.
The user is asking for an authentic reference creation for the following game and platform:

USER GAME INPUT: "{game}"
PLATFORM: "{platform}"
DESIRED CREATION: "{creation_type}"{description_block}

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
7. Produce a complete, detailed document corresponding to "{creation_type}".{description_instruction}
8. You MUST return ONLY a single, raw, valid JSON object. Do NOT wrap in markdown fences.
   Do NOT add conversational intro text.

JSON SCHEMA (use this — notFound=false, ambiguous=false):
{JSON_SCHEMA_HINT}

Set platform="{platform}", creationType="{creation_type}".
Set "game" to the official canonical title for the selected game.
Respond with valid JSON only.{extra}"""

    return f"""You are a retro gaming historian, archivist, and documentation master.
The user is asking for an authentic reference creation for the following game and platform:

USER GAME INPUT: "{game}"
PLATFORM: "{platform}"
DESIRED CREATION: "{creation_type}"{description_block}

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
8. When uniquely found: produce a complete, detailed document corresponding to "{creation_type}".{description_instruction}
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
Respond with valid JSON only.{extra}"""


SYSTEM_MESSAGE = (
    "You are a precise retro gaming documentation generator. "
    "Never guess a game title from ambiguous or nonsense input. "
    "If multiple real titles match the query (franchise / base name / ambiguity), "
    "return ambiguous=true with a candidates list of official titles. "
    "If the game cannot be identified with high confidence, return notFound=true "
    'with game="Game Not Found". '
    "Always respond with a single valid JSON object and nothing else."
)
