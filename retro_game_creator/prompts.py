"""Prompt templates and JSON schema for document generation."""

from __future__ import annotations

JSON_SCHEMA_HINT = """
{
  "game": "<official canonical game title — correct spelling & conventional capitalization>",
  "platform": "<platform>",
  "creationType": "<creation type>",
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


def build_prompt(
    game: str,
    platform: str,
    creation_type: str,
    system_extra: str = "",
    *,
    with_web_search: bool = False,
) -> str:
    """Build the user prompt for Gemini or local instruct models."""
    extra = f"\n\nADDITIONAL USER INSTRUCTIONS:\n{system_extra.strip()}" if system_extra.strip() else ""

    accuracy_step = (
        f'1. Search the live web to identify the game the user means by "{game}" on "{platform}", '
        f"then verify the actual real-world historical game credits."
        if with_web_search
        else f'1. From your knowledge of video game history, identify the game the user means by "{game}" on "{platform}", '
        f"then verify the actual real-world historical game credits."
    )

    return f"""You are a retro gaming historian, archivist, and documentation master.
The user is asking for an authentic reference creation for the following game and platform:

USER GAME INPUT: "{game}"
PLATFORM: "{platform}"
DESIRED CREATION: "{creation_type}"

CRITICAL INSTRUCTIONS FOR ACCURACY & ERA AESTHETICS:
{accuracy_step}
2. The JSON "game" field MUST be the generally accepted official title as used on the internet
   (Wikipedia / MobyGames / publisher materials) — correct spelling and conventional capitalization.
   Do NOT echo the user's typos, odd spacing, or random capitalization.
   Examples: "doom" → "Doom"; "final fantacy 7" → "Final Fantasy VII"; "halo ce" → "Halo: Combat Evolved";
   "monkey island" → "The Secret of Monkey Island"; "oregon trail" → "The Oregon Trail".
3. You MUST output the ACTUAL real-world developer studio, publisher, key designers, release year, genre, media format, and hardware specs for that canonical game on "{platform}".
4. NEVER output placeholder credit strings like "Bethesda Game Studios / Studio", "Xbox Game Studios / Publisher", "Development Team", or "Commodore Amiga High Performance Mode" unless that studio genuinely made the game on that platform.
Provide exact credits, e.g.:
- If game is "The Oregon Trail" on "Apple II": developer="MECC", publisher="MECC", designer="Don Rawitsch, Bill Heinemann, Paul Dillenberger", releaseYear="1985", mediaFormat="5.25\\" Floppy Disk", systemRequirements="Apple II / IIe (MOS 6502 @ 1MHz, 64KB RAM)"
- If game is "Super Mario 64" on "N64": developer="Nintendo EAD", publisher="Nintendo", designer="Shigeru Miyamoto, Yoshiaki Koizumi", releaseYear="1996", mediaFormat="8MB N64 ROM Cartridge", systemRequirements="Nintendo 64 (NEC VR4300 @ 93.75MHz, 4MB Rambus RDRAM)"
- If game is "Final Fantasy VII" on "PS1": developer="Square", publisher="Square / Sony", designer="Yoshinori Kitase, Hironobu Sakaguchi, Tetsuya Nomura", releaseYear="1997", mediaFormat="3 x CD-ROM Discs", systemRequirements="PlayStation (MIPS R3000A @ 33.86MHz, 2MB RAM, 1MB VRAM)"
- If game is "Halo: Combat Evolved" on "Original Xbox": developer="Bungie", publisher="Microsoft Game Studios", designer="Jason Jones, Marcus Lehto", releaseYear="2001", mediaFormat="Xbox DVD-ROM", systemRequirements="Original Xbox (Intel Pentium III 733MHz, 64MB RAM, Nvidia NV2A)"

5. Produce a complete, detailed document corresponding to "{creation_type}". Include full paragraphs, real control keybindings, actual gameplay tips, plot lore, and magazine review style commentary when appropriate.
6. You MUST return ONLY a single, raw, valid JSON object conforming strictly to the schema below. Do NOT wrap in markdown fences. Do NOT add conversational intro text.

JSON SCHEMA:
{JSON_SCHEMA_HINT}

Set platform="{platform}", creationType="{creation_type}".
Set "game" to the official canonical title (not the raw user input if it was misspelled or oddly capitalized).
Respond with valid JSON only.{extra}"""


SYSTEM_MESSAGE = (
    "You are a precise retro gaming documentation generator. "
    "Always respond with a single valid JSON object and nothing else."
)
