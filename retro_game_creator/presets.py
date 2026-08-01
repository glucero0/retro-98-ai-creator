"""Platform catalogs, creation types, popular presets, and seed archives."""

from __future__ import annotations

POPULAR_GAME_PRESETS: list[dict[str, str]] = [
    {
        "game": "Defender of the Crown",
        "platform": "Commodore Amiga",
        "suggestedCreation": "Quick Reference Card",
        "eraDescription": "Cinematic 1986 Masterpiece by Cinemaware with iconic Paula 4-channel audio & Amiga Workbench graphics.",
    },
    {
        "game": "The Oregon Trail",
        "platform": "Apple II / IIe",
        "suggestedCreation": "Player Manual & Strategy Guide",
        "eraDescription": "1985 MECC educational survival pioneer with iconic green-phosphor graphics & dysentery lore.",
    },
    {
        "game": "Manic Miner",
        "platform": "Timex Sinclair / ZX Spectrum",
        "suggestedCreation": "Quick Reference Card",
        "eraDescription": "1983 Matthew Smith platforming legend with 8-color attribute clash & in-game music.",
    },
    {
        "game": "Pitfall!",
        "platform": "Atari 2600",
        "suggestedCreation": "Secret Codes & Cheatsheet",
        "eraDescription": "1982 Activision classic with 255 jungle screens and woodgrain console aesthetics.",
    },
    {
        "game": "The Secret of Monkey Island",
        "platform": "MS-DOS (VGA)",
        "suggestedCreation": "Player Manual & Strategy Guide",
        "eraDescription": "1990 LucasArts SCUMM classic with 256-color VGA art and iMUSE dynamic soundtrack.",
    },
    {
        "game": "Doom",
        "platform": "MS-DOS",
        "suggestedCreation": "Secret Codes & Cheatsheet",
        "eraDescription": "1993 id Software landmark FPS featuring sound card setup, IDKFA codes & shareware history.",
    },
    {
        "game": "Halo: Combat Evolved",
        "platform": "Original Xbox",
        "suggestedCreation": "Quick Reference Card",
        "eraDescription": "2001 Bungie launch masterpiece featuring Xbox Matrix Green Dashboard styling & LAN party setup.",
    },
    {
        "game": "Halo 3",
        "platform": "Xbox 360",
        "suggestedCreation": "Player Manual & Strategy Guide",
        "eraDescription": "2007 Xbox 360 flagship with Blade UI aesthetics, Forge mode guide, and Skull cheat locations.",
    },
    {
        "game": "Wii Sports",
        "platform": "Nintendo Wii",
        "suggestedCreation": "Quick Reference Card",
        "eraDescription": "2006 motion-control phenomenon featuring Wii Menu Cyan aesthetics & Wiimote safety guide.",
    },
    {
        "game": "Final Fantasy VII",
        "platform": "Sony PlayStation (PS1)",
        "suggestedCreation": "Plot & Lore Summary",
        "eraDescription": "1997 Square RPG phenomenon with 3D FMVs, Materia guide, and PS1 Memory Card management.",
    },
    {
        "game": "Chrono Trigger",
        "platform": "Super Nintendo (SNES)",
        "suggestedCreation": "Plot & Lore Summary",
        "eraDescription": "1995 Square RPG with 16-bit Mode 7 graphics, Yasunori Mitsuda soundtrack, and 13 distinct endings.",
    },
    {
        "game": "Sonic the Hedgehog 2",
        "platform": "Sega Genesis / Mega Drive",
        "suggestedCreation": "Secret Codes & Cheatsheet",
        "eraDescription": "1992 Sega mascot platformer featuring Super Sonic level select code & 16-bit sound test.",
    },
]

PLATFORM_OPTIONS: list[str] = [
    "Apple II / IIe",
    "Timex Sinclair 1000 / ZX Spectrum",
    "Commodore 64 (C64)",
    "Commodore Amiga 500 / 1200",
    "Atari 2600 / 5200 / 7800",
    "Atari ST / TT",
    "Amstrad CPC",
    "BBC Micro / Acorn Electron",
    "Vectrex",
    "MS-DOS (VGA/EGA/CGA)",
    "FM Towns / PC-98",
    "Nintendo Entertainment System (NES)",
    "Super Nintendo (SNES)",
    "Nintendo 64 (N64)",
    "Game Boy / Game Boy Color / Game Boy Advance",
    "Sega Genesis / Mega Drive",
    "Sega Saturn",
    "Sega Dreamcast",
    "TurboGrafx-16 / PC Engine",
    "Neo Geo MVS / AES",
    "Sony PlayStation (PS1)",
    "Sony PlayStation 2 (PS2)",
    "Sony PlayStation 3 (PS3)",
    "Sony PlayStation 4 (PS4)",
    "Sony PlayStation 5 (PS5)",
    "PlayStation Portable (PSP) / PS Vita",
    "Original Xbox",
    "Xbox 360",
    "Xbox One",
    "Xbox Series X | S",
    "Nintendo GameCube",
    "Nintendo Wii / Wii U",
    "Nintendo Switch",
    "Windows PC / Steam Deck",
    "Arcade (Coin-Op Cabinet)",
]

CREATION_TYPES: list[dict[str, str]] = [
    {
        "id": "Quick Reference Card",
        "label": "Quick Reference Card & Keybindings",
        "desc": "Keybindings, joystick controls, quick start steps, disk swap instructions, and sound setup.",
    },
    {
        "id": "Player Manual & Strategy Guide",
        "label": "Player Manual & Strategy Guide",
        "desc": "Lore background, game mechanics, character stats, interface guide, and beginner walkthrough.",
    },
    {
        "id": "Review Aggregation & Retrospective",
        "label": "Review Aggregation & Retrospective",
        "desc": "1980s/90s magazine reviews, ratings, pros/cons, and modern retrospective.",
    },
    {
        "id": "Plot & Lore Summary",
        "label": "Plot & Lore Summary",
        "desc": "Opening cinematic lore, act-by-act narrative breakdown, key character profiles, and endings explained.",
    },
    {
        "id": "Secret Codes & Cheatsheet",
        "label": "Secret Codes, Cheats & Passwords",
        "desc": "Invincibility codes, level passwords, developer easter eggs, debug keys, and POKE codes.",
    },
    {
        "id": "Boss & Enemy Compendium",
        "label": "Boss & Enemy Compendium",
        "desc": "Enemy stats, attack patterns, weakness tables, boss fight strategies, and loot tables.",
    },
    {
        "id": "Soundtrack, Trivia & Historical Companion",
        "label": "Soundtrack, Trivia & Historical Companion",
        "desc": "Sound chip hardware feats, composer info, box art design history, and regional port differences.",
    },
]

INITIAL_PRESET_CREATIONS: list[dict] = [
    {
        "id": "preset-defender-amiga",
        "game": "Defender of the Crown",
        "platform": "Commodore Amiga",
        "creationType": "Quick Reference Card",
        "createdAt": "2026-07-24T05:00:00.000Z",
        "meta": {
            "releaseYear": "1986",
            "developer": "Cinemaware",
            "publisher": "Cinemaware / Mindscape",
            "designer": "Kellyn Beck (Art: Jim Sachs)",
            "genre": "Turn-Based Strategy & Action",
            "mediaFormat": '2 x 3.5" Double Density Amiga Floppies',
            "systemRequirements": "Amiga 500 / 1000, 512 KB RAM, Kickstart 1.2, OCS Paula Chip",
        },
        "theme": {
            "themeName": "Amiga Workbench 1.3 Blue & Topaz",
            "bgColor": "#0055aa",
            "cardBg": "#ffffff",
            "textColor": "#000000",
            "accentColor": "#ffaa00",
            "headerBg": "#0055aa",
            "fontStyle": "workbench",
            "boxArtStyle": "Rich medieval tapestry gold framing over deep cobalt blue background",
        },
        "overview": (
            "Official 1986 Cinemaware Quick Reference Command Card for Defender of the Crown "
            "on the Commodore Amiga 500/1000. Features disk swap instructions, tournament controls, "
            "castle siege catapult physics, and raiding keybindings."
        ),
        "sections": [
            {
                "title": "System Boot & Disk Loading Procedure",
                "content": (
                    '1. Insert Disk 1 (Boot Disk) into floppy drive DF0: and power on your Amiga.\n'
                    "2. When the Workbench hand appears or the Cinemaware splash screen initializes, "
                    "do not interrupt disk drive activity.\n"
                    '3. Keep Disk 2 ready. When prompted "Insert Disk 2 into DF0:", eject Disk 1 and insert Disk 2.'
                ),
                "keyValues": [
                    {"label": "Boot Drive", "value": "DF0: (Floppy)"},
                    {"label": "Audio Hardware", "value": "Paula 4-Channel Stereo PCM"},
                    {"label": "Graphics Mode", "value": "32-Color 320x200 LORES / HAM"},
                ],
            },
            {
                "title": "Jousting Tournament Controls",
                "content": "During the Joust, aim your lance at your opponent's shield while matching horse speed.",
                "keyValues": [
                    {"label": "Joystick Port", "value": "Port 2"},
                    {"label": "Joystick UP", "value": "Raise Lance Angle"},
                    {"label": "Joystick DOWN", "value": "Lower Lance Angle"},
                    {"label": "FIRE Button", "value": "Lock Lance Position on Impact"},
                ],
            },
            {
                "title": "Siege Catapult Physics Commands",
                "content": "Adjust trebuchet winch tension to breach castle walls before launching payloads.",
                "keyValues": [
                    {"label": "FIRE Button Hold", "value": "Increase Catapult Tension"},
                    {"label": "FIRE Button Release", "value": "Launch Payload"},
                    {"label": "Greek Fire Toggle", "value": "Press [F1] Key"},
                    {"label": "Boulder Payload", "value": "Press [F3] Key"},
                ],
            },
        ],
        "groundingSources": [
            {"title": "Cinemaware Archives - Defender of the Crown", "url": "https://www.cinemaware.com/defender"},
            {"title": "Amiga Hall of Light - Defender of the Crown", "url": "https://hol.abime.net/304"},
        ],
        "accuracyNote": "Verified against original 1986 Cinemaware Amiga manual and disk sector documentation.",
    },
    {
        "id": "preset-doom-dos",
        "game": "Doom",
        "platform": "MS-DOS",
        "creationType": "Secret Codes & Cheatsheet",
        "createdAt": "2026-07-24T05:10:00.000Z",
        "meta": {
            "releaseYear": "1993",
            "developer": "id Software",
            "publisher": "id Software / GT Interactive",
            "designer": "John Carmack, John Romero, Tom Hall, Adrian Carmack",
            "genre": "First-Person Shooter",
            "mediaFormat": '4 x 3.5" High Density MS-DOS Floppies / Shareware',
            "systemRequirements": "386DX 33MHz, 4MB RAM, VGA Graphics, Sound Blaster / Roland Sound",
        },
        "theme": {
            "themeName": "MS-DOS Cyber VGA Cyber-Green & Blood Red",
            "bgColor": "#001100",
            "cardBg": "#0a1a0a",
            "textColor": "#00ff66",
            "accentColor": "#ff2200",
            "headerBg": "#002200",
            "fontStyle": "dos-vga",
            "boxArtStyle": "Dark cyber-demon art with toxic green DOS terminal text and red warning accents",
        },
        "overview": (
            "Complete verified 1993 id Software Command Reference & Cheat Codes for Doom on MS-DOS. "
            "Includes command line parameters, Sound Blaster IRQ setup, and secret level access codes."
        ),
        "sections": [
            {
                "title": "In-Game Cheat Codes (Type directly during gameplay)",
                "content": "Type the letter sequence at any point during active gameplay. No console needed.",
                "keyValues": [
                    {"label": "IDKFA", "value": "Full Ammo, All Weapons, All Keycards"},
                    {"label": "IDDQD", "value": "Degreelessness Mode (Invulnerability)"},
                    {"label": "IDCLIP / IDSPISPOPD", "value": "No-Clip Mode (Walk through walls)"},
                    {"label": "IDCLEVxy", "value": "Warp to Episode x, Level y (e.g. IDCLEV19)"},
                    {"label": "IDBEHOLDs", "value": "Gain Berserk powerup"},
                    {"label": "IDMYPOS", "value": "Display exact coordinate grid & compass bearing"},
                ],
            },
            {
                "title": "MS-DOS Command Line Launch Switches",
                "content": "Launch DOOM.EXE from C:\\DOOM> with custom command line parameters.",
                "keyValues": [
                    {"label": "DOOM.EXE -file <wad>", "value": "Load custom PWAD mod file"},
                    {"label": "DOOM.EXE -warp <e> <l>", "value": "Boot directly into Episode and Map"},
                    {"label": "DOOM.EXE -nosound", "value": "Disable sound driver"},
                    {"label": "DOOM.EXE -respawn", "value": "Monsters respawn after death"},
                    {"label": "DOOM.EXE -fast", "value": "Monsters move and attack twice as fast"},
                ],
            },
        ],
        "groundingSources": [
            {"title": "Doom Wiki - Cheat codes", "url": "https://doomwiki.org/wiki/Cheat_codes"},
        ],
        "accuracyNote": "Cross-checked against id Software DOOM v1.1-1.9 release documentation.",
    },
]
