/* Shared catalogs — mirrors retro_game_creator/presets.py so the UI works
   even before (or without) the Python bridge answering get_bootstrap. */
window.RGC_CATALOG = {
  platforms: [
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
  ],
  creationTypes: [
    {
      id: "Quick Reference Card",
      label: "Quick Reference Card & Keybindings",
      desc: "Keybindings, joystick controls, quick start steps, disk swap instructions, and sound setup.",
    },
    {
      id: "Player Manual & Strategy Guide",
      label: "Player Manual & Strategy Guide",
      desc: "Lore background, game mechanics, character stats, interface guide, and beginner walkthrough.",
    },
    {
      id: "Review Aggregation & Retrospective",
      label: "Review Aggregation & Retrospective",
      desc: "1980s/90s magazine reviews, ratings, pros/cons, and modern retrospective.",
    },
    {
      id: "Plot & Lore Summary",
      label: "Plot & Lore Summary",
      desc: "Opening cinematic lore, act-by-act narrative breakdown, key character profiles, and endings explained.",
    },
    {
      id: "Secret Codes & Cheatsheet",
      label: "Secret Codes, Cheats & Passwords",
      desc: "Invincibility codes, level passwords, developer easter eggs, debug keys, and POKE codes.",
    },
    {
      id: "Boss & Enemy Compendium",
      label: "Boss & Enemy Compendium",
      desc: "Enemy stats, attack patterns, weakness tables, boss fight strategies, and loot tables.",
    },
    {
      id: "Soundtrack, Trivia & Historical Companion",
      label: "Soundtrack, Trivia & Historical Companion",
      desc: "Sound chip hardware feats, composer info, box art design history, and regional port differences.",
    },
  ],
  presets: [
    {
      game: "Defender of the Crown",
      platform: "Commodore Amiga",
      suggestedCreation: "Quick Reference Card",
      eraDescription:
        "Cinematic 1986 Masterpiece by Cinemaware with iconic Paula 4-channel audio & Amiga Workbench graphics.",
    },
    {
      game: "The Oregon Trail",
      platform: "Apple II / IIe",
      suggestedCreation: "Player Manual & Strategy Guide",
      eraDescription:
        "1985 MECC educational survival pioneer with iconic green-phosphor graphics & dysentery lore.",
    },
    {
      game: "Manic Miner",
      platform: "Timex Sinclair / ZX Spectrum",
      suggestedCreation: "Quick Reference Card",
      eraDescription:
        "1983 Matthew Smith platforming legend with 8-color attribute clash & in-game music.",
    },
    {
      game: "Pitfall!",
      platform: "Atari 2600",
      suggestedCreation: "Secret Codes & Cheatsheet",
      eraDescription:
        "1982 Activision classic with 255 jungle screens and woodgrain console aesthetics.",
    },
    {
      game: "The Secret of Monkey Island",
      platform: "MS-DOS (VGA)",
      suggestedCreation: "Player Manual & Strategy Guide",
      eraDescription:
        "1990 LucasArts SCUMM classic with 256-color VGA art and iMUSE dynamic soundtrack.",
    },
    {
      game: "Doom",
      platform: "MS-DOS",
      suggestedCreation: "Secret Codes & Cheatsheet",
      eraDescription:
        "1993 id Software landmark FPS featuring sound card setup, IDKFA codes & shareware history.",
    },
    {
      game: "Halo: Combat Evolved",
      platform: "Original Xbox",
      suggestedCreation: "Quick Reference Card",
      eraDescription:
        "2001 Bungie launch masterpiece featuring Xbox Matrix Green Dashboard styling & LAN party setup.",
    },
    {
      game: "Halo 3",
      platform: "Xbox 360",
      suggestedCreation: "Player Manual & Strategy Guide",
      eraDescription:
        "2007 Xbox 360 flagship with Blade UI aesthetics, Forge mode guide, and Skull cheat locations.",
    },
    {
      game: "Wii Sports",
      platform: "Nintendo Wii",
      suggestedCreation: "Quick Reference Card",
      eraDescription:
        "2006 motion-control phenomenon featuring Wii Menu Cyan aesthetics & Wiimote safety guide.",
    },
    {
      game: "Final Fantasy VII",
      platform: "Sony PlayStation (PS1)",
      suggestedCreation: "Plot & Lore Summary",
      eraDescription:
        "1997 Square RPG phenomenon with 3D FMVs, Materia guide, and PS1 Memory Card management.",
    },
    {
      game: "Chrono Trigger",
      platform: "Super Nintendo (SNES)",
      suggestedCreation: "Plot & Lore Summary",
      eraDescription:
        "1995 Square RPG with 16-bit Mode 7 graphics, Yasunori Mitsuda soundtrack, and 13 distinct endings.",
    },
    {
      game: "Sonic the Hedgehog 2",
      platform: "Sega Genesis / Mega Drive",
      suggestedCreation: "Secret Codes & Cheatsheet",
      eraDescription:
        "1992 Sega mascot platformer featuring Super Sonic level select code & 16-bit sound test.",
    },
  ],
};
