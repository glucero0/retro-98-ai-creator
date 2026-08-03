"""Known franchise / base-name disambiguation for Search Results.

The LLM often returns notFound (or a single arbitrary title) for short franchise
queries like "call of duty". This catalog forces a multi-match Search Results
dialog when the user input is an ambiguous base name — without inventing a
match for true gibberish.
"""

from __future__ import annotations

import re
from typing import Any


def _norm(text: str) -> str:
    s = (text or "").casefold().strip()
    s = s.replace("&", " and ")
    s = re.sub(r"[^\w\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _c(game: str, year: str = "", platform: str = "", note: str = "") -> dict[str, str]:
    return {"game": game, "year": year, "platform": platform, "note": note}


# Keys are normalized franchise base names. Values are well-known official titles.
FRANCHISE_CANDIDATES: dict[str, list[dict[str, str]]] = {
    "call of duty": [
        _c("Call of Duty", "2003", "PC", "Original WWII FPS"),
        _c("Call of Duty 2", "2005", "PC / Xbox 360", "WWII sequel"),
        _c("Call of Duty 4: Modern Warfare", "2007", "Multi-platform", "Modern Warfare reboot"),
        _c("Call of Duty: World at War", "2008", "Multi-platform", "WWII Pacific / Eastern Front"),
        _c("Call of Duty: Modern Warfare 2", "2009", "Multi-platform", "Modern Warfare sequel"),
        _c("Call of Duty: Black Ops", "2010", "Multi-platform", "Cold War campaign"),
        _c("Call of Duty: Modern Warfare 3", "2011", "Multi-platform", "Modern Warfare trilogy finale"),
        _c("Call of Duty: Black Ops II", "2012", "Multi-platform", "Black Ops sequel"),
        _c("Call of Duty: Ghosts", "2013", "Multi-platform", "New IP within series"),
        _c("Call of Duty: Advanced Warfare", "2014", "Multi-platform", "Exosuit near-future"),
        _c("Call of Duty: Black Ops III", "2015", "Multi-platform", "Black Ops future war"),
        _c("Call of Duty: WWII", "2017", "Multi-platform", "Return to WWII"),
        _c("Call of Duty: Modern Warfare", "2019", "Multi-platform", "2019 Modern Warfare reboot"),
        _c("Call of Duty: Black Ops Cold War", "2020", "Multi-platform", "1980s Cold War"),
        _c("Call of Duty: Modern Warfare II", "2022", "Multi-platform", "2022 Modern Warfare sequel"),
    ],
    "final fantasy": [
        _c("Final Fantasy", "1987", "NES", "Original Famicom / NES RPG"),
        _c("Final Fantasy IV", "1991", "SNES", "Also known as FF II in early NA"),
        _c("Final Fantasy VI", "1994", "SNES", "Also known as FF III in early NA"),
        _c("Final Fantasy VII", "1997", "PlayStation", "Cloud / Midgar"),
        _c("Final Fantasy VIII", "1999", "PlayStation", "Squall / SeeD"),
        _c("Final Fantasy IX", "2000", "PlayStation", "Zidane / Gaia"),
        _c("Final Fantasy X", "2001", "PlayStation 2", "Tidus / Spira"),
        _c("Final Fantasy XII", "2006", "PlayStation 2", "Vaan / Ivalice"),
        _c("Final Fantasy XIII", "2009", "PlayStation 3 / Xbox 360", "Lightning / Cocoon"),
        _c("Final Fantasy XIV", "2010", "PC / consoles", "MMORPG (A Realm Reborn)"),
        _c("Final Fantasy XV", "2016", "PlayStation 4 / Xbox One", "Noctis road trip"),
        _c("Final Fantasy VII Remake", "2020", "PlayStation 4", "VII remake Part 1"),
    ],
    "resident evil": [
        _c("Resident Evil", "1996", "PlayStation", "Original mansion survival horror"),
        _c("Resident Evil 2", "1998", "PlayStation", "Raccoon City — Leon & Claire"),
        _c("Resident Evil 3: Nemesis", "1999", "PlayStation", "Jill vs Nemesis"),
        _c("Resident Evil 4", "2005", "GameCube", "Leon in rural Europe"),
        _c("Resident Evil 5", "2009", "PlayStation 3 / Xbox 360", "Chris in Africa"),
        _c("Resident Evil 6", "2012", "Multi-platform", "Ensemble action sequel"),
        _c("Resident Evil 7: Biohazard", "2017", "Multi-platform", "First-person Baker house"),
        _c("Resident Evil Village", "2021", "Multi-platform", "Ethan Winters sequel"),
        _c("Resident Evil 2 (Remake)", "2019", "Multi-platform", "2019 remake"),
        _c("Resident Evil 3 (Remake)", "2020", "Multi-platform", "2020 remake"),
        _c("Resident Evil 4 (Remake)", "2023", "Multi-platform", "2023 remake"),
    ],
    "halo": [
        _c("Halo: Combat Evolved", "2001", "Xbox", "Original Master Chief campaign"),
        _c("Halo 2", "2004", "Xbox", "Sequel / online multiplayer landmark"),
        _c("Halo 3", "2007", "Xbox 360", "Trilogy finale"),
        _c("Halo 3: ODST", "2009", "Xbox 360", "Orbital Drop Shock Troopers"),
        _c("Halo: Reach", "2010", "Xbox 360", "Fall of Reach prequel"),
        _c("Halo 4", "2012", "Xbox 360", "Reclaimer saga start"),
        _c("Halo 5: Guardians", "2015", "Xbox One", "Locke vs Chief"),
        _c("Halo Infinite", "2021", "Xbox / PC", "Open-world reboot"),
    ],
    "mario": [
        _c("Super Mario Bros.", "1985", "NES", "Original side-scroller"),
        _c("Super Mario Bros. 3", "1988", "NES", "Classic NES sequel"),
        _c("Super Mario World", "1990", "SNES", "Dinosaur Land"),
        _c("Super Mario 64", "1996", "Nintendo 64", "First 3D Mario"),
        _c("Super Mario Sunshine", "2002", "GameCube", "Isle Delfino"),
        _c("New Super Mario Bros.", "2006", "Nintendo DS", "2D revival"),
        _c("Super Mario Galaxy", "2007", "Wii", "Sphere platforming"),
        _c("New Super Mario Bros. Wii", "2009", "Wii", "Co-op 2D"),
        _c("Super Mario 3D World", "2013", "Wii U", "Cat suits / co-op 3D"),
        _c("Super Mario Odyssey", "2017", "Nintendo Switch", "Capture / kingdoms"),
        _c("Mario Kart 64", "1996", "Nintendo 64", "Kart racing"),
        _c("Mario Kart 8 / Deluxe", "2014", "Wii U / Switch", "Modern Mario Kart"),
    ],
    "zelda": [
        _c("The Legend of Zelda", "1986", "NES", "Original open adventure"),
        _c("The Legend of Zelda: A Link to the Past", "1991", "SNES", "Top-down classic"),
        _c("The Legend of Zelda: Ocarina of Time", "1998", "Nintendo 64", "3D landmark"),
        _c("The Legend of Zelda: Majora's Mask", "2000", "Nintendo 64", "Three-day cycle"),
        _c("The Legend of Zelda: The Wind Waker", "2002", "GameCube", "Cel-shaded ocean"),
        _c("The Legend of Zelda: Twilight Princess", "2006", "GameCube / Wii", "Wolf Link"),
        _c("The Legend of Zelda: Skyward Sword", "2011", "Wii", "Motion controls origin"),
        _c("The Legend of Zelda: Breath of the Wild", "2017", "Wii U / Switch", "Open-air reboot"),
        _c("The Legend of Zelda: Tears of the Kingdom", "2023", "Nintendo Switch", "BOTW sequel"),
    ],
    "doom": [
        _c("Doom", "1993", "MS-DOS", "Original id Software FPS"),
        _c("Doom II: Hell on Earth", "1994", "MS-DOS", "Super Shotgun sequel"),
        _c("Doom 3", "2004", "PC", "Horror reboot"),
        _c("Doom (2016)", "2016", "Multi-platform", "Modern reboot"),
        _c("Doom Eternal", "2020", "Multi-platform", "2016 sequel"),
        _c("Doom 64", "1997", "Nintendo 64", "Console-original campaign"),
    ],
    "elder scrolls": [
        _c("The Elder Scrolls III: Morrowind", "2002", "PC / Xbox", "Vvardenfell open world"),
        _c("The Elder Scrolls IV: Oblivion", "2006", "PC / Xbox 360 / PS3", "Cyrodiil"),
        _c("The Elder Scrolls V: Skyrim", "2011", "Multi-platform", "Dragonborn"),
        _c("The Elder Scrolls Online", "2014", "Multi-platform", "MMORPG"),
    ],
    "assassin s creed": [
        _c("Assassin's Creed", "2007", "Multi-platform", "Original Altaïr"),
        _c("Assassin's Creed II", "2009", "Multi-platform", "Ezio Auditore begins"),
        _c("Assassin's Creed: Brotherhood", "2010", "Multi-platform", "Ezio in Rome"),
        _c("Assassin's Creed: Revelations", "2011", "Multi-platform", "Ezio finale"),
        _c("Assassin's Creed III", "2012", "Multi-platform", "Connor / American Revolution"),
        _c("Assassin's Creed IV: Black Flag", "2013", "Multi-platform", "Pirate fantasy"),
        _c("Assassin's Creed Origins", "2017", "Multi-platform", "Ptolemaic Egypt"),
        _c("Assassin's Creed Odyssey", "2018", "Multi-platform", "Ancient Greece"),
        _c("Assassin's Creed Valhalla", "2020", "Multi-platform", "Viking England"),
    ],
    "grand theft auto": [
        _c("Grand Theft Auto III", "2001", "PlayStation 2", "3D Liberty City"),
        _c("Grand Theft Auto: Vice City", "2002", "PlayStation 2", "1980s Vice City"),
        _c("Grand Theft Auto: San Andreas", "2004", "PlayStation 2", "CJ / three cities"),
        _c("Grand Theft Auto IV", "2008", "PlayStation 3 / Xbox 360", "Niko Bellic"),
        _c("Grand Theft Auto V", "2013", "Multi-platform", "Franklin / Michael / Trevor"),
    ],
    "metal gear": [
        _c("Metal Gear Solid", "1998", "PlayStation", "Shadow Moses"),
        _c("Metal Gear Solid 2: Sons of Liberty", "2001", "PlayStation 2", "Big Shell"),
        _c("Metal Gear Solid 3: Snake Eater", "2004", "PlayStation 2", "1964 jungle"),
        _c("Metal Gear Solid 4: Guns of the Patriots", "2008", "PlayStation 3", "Old Snake"),
        _c("Metal Gear Solid V: The Phantom Pain", "2015", "Multi-platform", "Open-world MGSV"),
    ],
    "pokemon": [
        _c("Pokémon Red / Blue", "1996", "Game Boy", "Original Kanto"),
        _c("Pokémon Gold / Silver", "1999", "Game Boy Color", "Johto"),
        _c("Pokémon Ruby / Sapphire", "2002", "Game Boy Advance", "Hoenn"),
        _c("Pokémon Diamond / Pearl", "2006", "Nintendo DS", "Sinnoh"),
        _c("Pokémon Black / White", "2010", "Nintendo DS", "Unova"),
        _c("Pokémon X / Y", "2013", "Nintendo 3DS", "Kalos / 3D"),
        _c("Pokémon Sword / Shield", "2019", "Nintendo Switch", "Galar"),
        _c("Pokémon Legends: Arceus", "2022", "Nintendo Switch", "Open Hisui"),
    ],
    "sonic": [
        _c("Sonic the Hedgehog", "1991", "Sega Genesis", "Original Genesis platformer"),
        _c("Sonic the Hedgehog 2", "1992", "Sega Genesis", "Tails debut"),
        _c("Sonic the Hedgehog 3 & Knuckles", "1994", "Sega Genesis", "Lock-on epic"),
        _c("Sonic Adventure", "1998", "Dreamcast", "First major 3D Sonic"),
        _c("Sonic Adventure 2", "2001", "Dreamcast", "Hero / Dark stories"),
        _c("Sonic Generations", "2011", "Multi-platform", "Classic + Modern"),
        _c("Sonic Mania", "2017", "Multi-platform", "2D retro revival"),
        _c("Sonic Frontiers", "2022", "Multi-platform", "Open-zone"),
    ],
    "battlefield": [
        _c("Battlefield 1942", "2002", "PC", "Original large-scale WWII"),
        _c("Battlefield 2", "2005", "PC", "Modern modern warfare landmark"),
        _c("Battlefield 3", "2011", "Multi-platform", "Frostbite showcase"),
        _c("Battlefield 4", "2013", "Multi-platform", "Naval / levolution"),
        _c("Battlefield 1", "2016", "Multi-platform", "WWI setting"),
        _c("Battlefield V", "2018", "Multi-platform", "WWII return"),
        _c("Battlefield 2042", "2021", "Multi-platform", "Specialists near-future"),
    ],
    "mortal kombat": [
        _c("Mortal Kombat", "1992", "Arcade", "Original digitized fighter"),
        _c("Mortal Kombat II", "1993", "Arcade", "Classic sequel"),
        _c("Mortal Kombat 3", "1995", "Arcade", "Run button era"),
        _c("Mortal Kombat X", "2015", "Multi-platform", "Variant system"),
        _c("Mortal Kombat 11", "2019", "Multi-platform", "Kronika story"),
        _c("Mortal Kombat 1", "2023", "Multi-platform", "New Era reboot"),
    ],
    "street fighter": [
        _c("Street Fighter II", "1991", "Arcade", "World Warrior classic"),
        _c("Street Fighter Alpha 3", "1998", "Arcade", "Alpha series peak"),
        _c("Street Fighter III: 3rd Strike", "1999", "Arcade", "Parry bible"),
        _c("Street Fighter IV", "2008", "Arcade / consoles", "HD revival"),
        _c("Street Fighter V", "2016", "PlayStation 4 / PC", "V-System"),
        _c("Street Fighter 6", "2023", "Multi-platform", "Drive Rush era"),
    ],
    "tekken": [
        _c("Tekken 3", "1997", "Arcade / PlayStation", "Classic 3D fighter"),
        _c("Tekken 5", "2004", "Arcade / PlayStation 2", "Devil Within era"),
        _c("Tekken 7", "2015", "Arcade / Multi-platform", "Mishima finale"),
        _c("Tekken 8", "2024", "Multi-platform", "Heat system"),
    ],
    "need for speed": [
        _c("Need for Speed: Underground", "2003", "Multi-platform", "Tuner culture"),
        _c("Need for Speed: Underground 2", "2004", "Multi-platform", "Open city tuning"),
        _c("Need for Speed: Most Wanted", "2005", "Multi-platform", "Blacklist pursuit"),
        _c("Need for Speed: Carbon", "2006", "Multi-platform", "Crew / canyons"),
        _c("Need for Speed: Hot Pursuit", "2010", "Multi-platform", "Cops vs racers reboot"),
        _c("Need for Speed: Heat", "2019", "Multi-platform", "Day/night Palm City"),
    ],
    "far cry": [
        _c("Far Cry", "2004", "PC", "Original tropical FPS"),
        _c("Far Cry 2", "2008", "Multi-platform", "African civil war"),
        _c("Far Cry 3", "2012", "Multi-platform", "Rook Islands / Vaas"),
        _c("Far Cry 4", "2014", "Multi-platform", "Kyrat / Pagan Min"),
        _c("Far Cry 5", "2018", "Multi-platform", "Hope County cult"),
        _c("Far Cry 6", "2021", "Multi-platform", "Yara / Anton Castillo"),
    ],
    "witcher": [
        _c("The Witcher", "2007", "PC", "Original CDPR RPG"),
        _c("The Witcher 2: Assassins of Kings", "2011", "PC / Xbox 360", "Choice-heavy sequel"),
        _c("The Witcher 3: Wild Hunt", "2015", "Multi-platform", "Open-world peak"),
    ],
    "dark souls": [
        _c("Dark Souls", "2011", "PlayStation 3 / Xbox 360", "Original Lordran"),
        _c("Dark Souls II", "2014", "Multi-platform", "Drangleic"),
        _c("Dark Souls III", "2016", "Multi-platform", "Trilogy finale"),
        _c("Dark Souls: Remastered", "2018", "Multi-platform", "Remaster of the original"),
    ],
}

# Alias empty lists → point at canonical key entries
_ALIASES = {
    "the legend of zelda": "zelda",
    "the elder scrolls": "elder scrolls",
    "assassins creed": "assassin s creed",
    "metal gear solid": "metal gear",
    "sonic the hedgehog": "sonic",
    "gta": "grand theft auto",
    "nfs": "need for speed",
    "the witcher": "witcher",
}


def _candidates_for_key(key: str) -> list[dict[str, str]]:
    key = _ALIASES.get(key, key)
    return list(FRANCHISE_CANDIDATES.get(key) or [])


def _unique_title_match(query: str, candidates: list[dict[str, str]]) -> dict[str, str] | None:
    """If query uniquely identifies one candidate title, return it."""
    q = _norm(query)
    if not q:
        return None
    exact = [c for c in candidates if _norm(c["game"]) == q]
    if len(exact) == 1:
        base = _norm(exact[0]["game"])
        # Still ambiguous when longer subtitled entries extend this title
        # e.g. "Call of Duty: Black Ops" vs "… Black Ops II"
        extensions = [
            c
            for c in candidates
            if _norm(c["game"]) != base and _norm(c["game"]).startswith(base + " ")
        ]
        if not extensions:
            return exact[0]
        return None
    # Strong containment: query matches exactly one title and no extensions
    hits = [c for c in candidates if q == _norm(c["game"]) or q in _norm(c["game"])]
    if len(hits) == 1:
        return hits[0]
    return None


def _filter_candidates(query: str, candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    """Narrow list when the user typed extra words beyond the franchise base."""
    q = _norm(query)
    # Strip the longest matching franchise prefix from the query to get residual tokens
    residual = q
    for key in sorted(FRANCHISE_CANDIDATES.keys(), key=len, reverse=True):
        canon = _ALIASES.get(key, key)
        if q == key or q.startswith(key + " "):
            residual = q[len(key) :].strip()
            break
        if key in _ALIASES and (q == canon or q.startswith(canon + " ")):
            residual = q[len(canon) :].strip()
            break
    if not residual:
        return list(candidates)
    tokens = [t for t in residual.split() if t not in {"the", "a", "an", "of", "and"}]
    if not tokens:
        return list(candidates)
    filtered = []
    for c in candidates:
        name = _norm(c["game"])
        if all(t in name for t in tokens):
            filtered.append(c)
    return filtered if len(filtered) >= 2 else list(candidates)


def find_franchise_key(user_game: str) -> str | None:
    """Return franchise catalog key if the query is that franchise (base or subtitled)."""
    q = _norm(user_game)
    if not q:
        return None
    # Prefer longest key match (e.g. "metal gear solid" before "metal gear")
    keys = sorted(
        set(list(FRANCHISE_CANDIDATES.keys()) + list(_ALIASES.keys())),
        key=len,
        reverse=True,
    )
    for key in keys:
        canon = _ALIASES.get(key, key)
        if q == key or q == canon:
            return canon
        if q.startswith(key + " ") or q.startswith(canon + " "):
            return canon
        # Also allow "cod"-style short aliases already in map
    return None


def resolve_franchise_ambiguity(user_game: str) -> list[dict[str, str]] | None:
    """If the query should show Search Results, return >=2 candidates; else None.

    Returns None when:
    - query is not a known franchise, or
    - query uniquely identifies one catalog title (user already specific enough).
    """
    key = find_franchise_key(user_game)
    if not key:
        return None
    candidates = _candidates_for_key(key)
    if len(candidates) < 2:
        return None
    unique = _unique_title_match(user_game, candidates)
    if unique:
        return None
    narrowed = _filter_candidates(user_game, candidates)
    if len(narrowed) >= 2:
        return narrowed
    return candidates


def maybe_raise_franchise_ambiguous(user_game: str) -> None:
    """Raise AmbiguousGameError when catalog says the query needs Search Results."""
    candidates = resolve_franchise_ambiguity(user_game)
    if candidates and len(candidates) >= 2:
        # Local import avoids cycles with creation_utils
        from .creation_utils import AmbiguousGameError

        raise AmbiguousGameError(user_game, candidates)
