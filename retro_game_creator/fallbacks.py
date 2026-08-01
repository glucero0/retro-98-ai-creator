"""Emergency metadata when the model fails to return parseable JSON."""

from __future__ import annotations


def get_dynamic_fallback_meta(game: str, platform: str) -> dict[str, str]:
    g = game.lower()
    p = platform.lower()

    dev = f"{game} Development Studio"
    pub = f"{platform} Game Publisher"
    designer = f"{game} Design Team"
    year = "199X"
    genre = "Action / Adventure"
    media = "Game Media / Cartridge / Disc"
    sys = f"{platform} Standard Hardware"

    if "starfield" in g:
        dev, pub, designer = "Bethesda Game Studios", "Xbox Game Studios", "Todd Howard"
        year, genre = "2023", "Sci-Fi Action RPG"
        media = "Digital / Xbox Game Pass / Optical Disc"
        sys = "Xbox Series X|S / PC (8-Core Zen 2 CPU, 16GB RAM, SSD)"
    elif "defender of the crown" in g:
        dev, pub, designer = "Cinemaware", "Cinemaware / Mindscape", "Kellyn Beck"
        year, genre = "1986", "Turn-Based Strategy & Action"
        media = '3.5" Amiga Floppy Disk'
        sys = "Amiga 500 / 1000 (Motorola 68000 @ 7.09MHz, 512KB RAM)"
    elif "doom" in g:
        dev, pub, designer = "id Software", "id Software / GT Interactive", "John Carmack, John Romero, Tom Hall"
        year, genre = "1993", "First-Person Shooter"
        media = '3.5" MS-DOS Floppies / Shareware'
        sys = "386DX 33MHz, 4MB RAM, VGA Graphics, Sound Blaster"
    elif "mario" in g:
        dev, pub, designer = "Nintendo EAD", "Nintendo", "Shigeru Miyamoto"
        year = "1990" if "snes" in p else "1985"
        genre = "Side-Scrolling Platformer"
        media = "Nintendo ROM Cartridge"
        sys = "SNES (Ricoh 5A22 CPU, 128KB RAM)" if "snes" in p else "NES (Ricoh 2A03 8-bit CPU, 2KB RAM)"
    elif "halo" in g:
        dev, pub = "Bungie", "Microsoft Game Studios"
        designer = "Jason Jones / Marcus Lehto"
        year = "2007" if "halo 3" in g else "2001"
        genre = "First-Person Shooter"
        media = "Xbox 360 DVD-ROM" if "360" in p else "Xbox DVD-ROM"
        sys = "Xbox 360 (Xenon 3.2GHz, 512MB RAM)" if "360" in p else "Original Xbox (Pentium III 733MHz, 64MB RAM)"
    elif "zelda" in g:
        dev, pub, designer = "Nintendo EPD", "Nintendo", "Shigeru Miyamoto / Eiji Aonuma"
        year, genre = "1986-2023", "Action-Adventure"
        media = "Nintendo Switch Game Card" if "switch" in p else "Nintendo ROM Cartridge"
        sys = f"{platform} Console Architecture"
    elif "elden ring" in g:
        dev, pub, designer = "FromSoftware", "Bandai Namco Entertainment", "Hidetaka Miyazaki"
        year, genre = "2022", "Action RPG"
        media = "Ultra HD Blu-ray / Digital"
        sys = "PS5 / Xbox Series X / PC"
    elif "oregon trail" in g:
        dev, pub, designer = "MECC", "MECC", "Don Rawitsch, Bill Heinemann, Paul Dillenberger"
        year, genre = "1985", "Educational Strategy / Survival"
        media = '5.25" Floppy Disk'
        sys = "Apple II / IIe (MOS 6502 @ 1MHz, 64KB RAM)"
    elif "manic miner" in g:
        dev, pub, designer = "Bug-Byte / Software Projects", "Software Projects", "Matthew Smith"
        year, genre = "1983", "Platformer"
        media = "Cassette Tape / Sinclair Floppy"
        sys = "Timex Sinclair 2068 / ZX Spectrum (Z80 @ 3.5MHz, 48KB RAM)"
    elif "pitfall" in g:
        dev, pub, designer = "Activision", "Activision", "David Crane"
        year, genre = "1982", "Platformer"
        media = "Atari 2600 ROM Cartridge"
        sys = "Atari 2600 (MOS 6507 @ 1.19MHz, 128 Bytes RAM)"
    elif "sonic" in g:
        dev, pub, designer = "Sonic Team / Sega", "Sega", "Yuji Naka / Hirokazu Yasuhara"
        year, genre = "1991", "Platformer"
        media = "Sega Genesis ROM Cartridge"
        sys = "Sega Genesis (Motorola 68000 @ 7.6MHz, Z80 Audio, YM2612)"
    elif "monkey island" in g:
        dev, pub, designer = "LucasArts", "LucasArts", "Ron Gilbert, Tim Schafer, Dave Grossman"
        year, genre = "1990", "Point-and-Click Graphic Adventure"
        media = '3.5" MS-DOS Floppy Disks'
        sys = "IBM PC / AT (286 12MHz, 640KB RAM, 256-Color VGA)"
    else:
        if "apple" in p:
            dev, pub, designer = "Apple II Software Developer", "Apple II Publisher", "Original Programmer"
            year, media = "1984", '5.25" Apple Floppy Disk'
            sys = "Apple IIe (MOS 6502 @ 1.023 MHz, 64KB RAM)"
        elif "sinclair" in p or "spectrum" in p:
            dev, pub, designer = "ZX Spectrum Studio", "Sinclair Research / Mastertronic", "Spectrum Programmer"
            year, media = "1983", "Cassette Tape"
            sys = "ZX Spectrum / Timex Sinclair (Z80 @ 3.5 MHz, 48KB RAM)"
        elif "amiga" in p:
            dev, pub, designer = "Amiga Software House", "Amiga Software Publisher", "Amiga Development Team"
            year, media = "1988", '3.5" Double Density Floppy Disk'
            sys = "Amiga 500 (Motorola 68000 @ 7.09 MHz, Paula Audio, OCS)"
        elif "commodore 64" in p or "c64" in p:
            dev, pub, designer = "C64 Software Team", "Commodore / Epyx", "C64 Programmer"
            year, media = "1985", '5.25" Commodore Floppy / Cassette'
            sys = "Commodore 64 (MOS 6510 @ 1.023 MHz, SID 6581 Sound)"
        elif "dos" in p or "pc" in p:
            dev, pub, designer = "PC Game Studio", "PC Software Publisher", "DOS Lead Designer"
            year, media = "1992", '3.5" Floppy Disk / CD-ROM'
            sys = "386 / 486 PC, VGA Graphics, Sound Blaster 16"
        elif "xbox" in p:
            is_360 = "360" in p
            dev = "Xbox 360 Game Studio" if is_360 else "Xbox Game Studio"
            pub, designer = "Microsoft / Xbox Game Studios", "Xbox Development Team"
            year = "2007" if is_360 else "2002"
            media = "DVD-ROM" if is_360 else "Xbox DVD-ROM"
            sys = "Xbox 360 Console" if is_360 else "Original Xbox Console"
        elif "playstation" in p or p.startswith("ps") or " ps" in f" {p}":
            dev, pub, designer = "PlayStation Development Studio", "Sony Interactive Entertainment", "PlayStation Design Team"
            year = "2021" if "5" in p else "2003" if "2" in p else "1998"
            media = "Ultra HD Blu-ray / Digital" if "5" in p else "CD-ROM / DVD-ROM"
            sys = f"{platform} Architecture"
        elif any(x in p for x in ("nintendo", "snes", "nes", "wii", "switch")):
            dev, pub, designer = "Nintendo Development Studio", "Nintendo", "Nintendo Design Team"
            year = "2020" if "switch" in p else "2007" if "wii" in p else "1992" if "snes" in p else "1987"
            media = (
                "Switch Game Card"
                if "switch" in p
                else "Wii Optical Disc"
                if "wii" in p
                else "Nintendo ROM Cartridge"
            )
            sys = f"{platform} System Hardware"

    return {
        "developer": dev,
        "publisher": pub,
        "designer": designer,
        "releaseYear": year,
        "genre": genre,
        "mediaFormat": media,
        "systemRequirements": sys,
    }


def build_emergency_creation(game: str, platform: str, creation_type: str) -> dict:
    meta = get_dynamic_fallback_meta(game, platform)
    return {
        "game": game,
        "platform": platform,
        "creationType": creation_type,
        "meta": meta,
        "theme": {
            "themeName": f"{game} Reference Document",
            "bgColor": "#101820",
            "cardBg": "#1e2a38",
            "textColor": "#f0f4f8",
            "accentColor": "#f2a900",
            "headerBg": "#0a0f14",
            "fontStyle": "retro-sans",
            "boxArtStyle": "Authentic era palette for target hardware",
        },
        "overview": (
            f"Reference document for {game} on {platform} ({creation_type}). "
            "The language model did not return parseable JSON; this emergency "
            "fallback uses known historical credits where available."
        ),
        "sections": [
            {
                "title": "Credits & System Specs",
                "content": (
                    f"{game} was developed by {meta['developer']} and published by "
                    f"{meta['publisher']}. Re-run generation after the model finishes "
                    "downloading, or try a different instruct model in Control Panel."
                ),
                "keyValues": [
                    {"label": "Release Year", "value": meta["releaseYear"]},
                    {"label": "Designer", "value": meta["designer"]},
                    {"label": "Genre", "value": meta["genre"]},
                    {"label": "Media", "value": meta["mediaFormat"]},
                    {"label": "Hardware", "value": meta["systemRequirements"]},
                ],
            },
            {
                "title": "Generation Tip",
                "content": (
                    "Phi-3.5-mini and other small models occasionally wrap JSON in "
                    "markdown or truncate mid-object. Raise max_new_tokens, lower "
                    "temperature, or switch to Qwen2.5-3B-Instruct in Control Panel."
                ),
                "keyValues": [],
            },
        ],
        "accuracyNote": "Emergency fallback — verify credits against original manuals / MobyGames.",
    }
