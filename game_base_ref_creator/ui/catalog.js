/* Shared catalogs — mirrors game_base_ref_creator/data/creation_types.json
   (and presets.py platforms/presets) so the UI works even before (or without)
   the Python bridge answering get_bootstrap. */
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
      description:
        "Produce a compact quick-reference card focused on getting the player into the game fast. Cover default keyboard and joystick/controller bindings, pause/quit/save/load keys, disk or media swap steps when relevant, sound and video setup quirks for the platform, boot/launch tips, and a short 'first five minutes' checklist. Prefer tables of key→action pairs and concise bullet steps over long narrative.",
    },
    {
      id: "Player Manual & Strategy Guide",
      label: "Player Manual & Strategy Guide",
      description:
        "Produce a player manual and beginner-to-intermediate strategy guide. Include setting/lore background, core game mechanics, interface and HUD explanation, character or unit stats when applicable, resource and progression systems, recommended early strategies, and a short walkthrough of the opening hours. Write in clear manual prose with labeled sections a player could follow while playing.",
    },
    {
      id: "Review Aggregation & Retrospective",
      label: "Review Aggregation & Retrospective",
      description:
        "Produce a review aggregation and retrospective in the style of period magazine coverage plus modern hindsight. Summarize contemporary 1980s–2000s critical reception (scores, praise, complaints), quote or paraphrase typical review angles of the era, list pros and cons, note commercial impact or controversy, and close with a modern retrospective on how the game holds up and why it still matters.",
    },
    {
      id: "Plot & Lore Summary",
      label: "Plot & Lore Summary",
      description:
        "Produce a plot and lore summary with clear spoiler structure. Cover premise and opening setup, act-by-act or chapter narrative beats, key character profiles and relationships, world/setting lore, major twists, and endings (including notable alternate endings when they exist). Prefer accurate story documentation over gameplay tips; mark heavy spoiler sections clearly in section titles.",
    },
    {
      id: "Secret Codes & Cheatsheet",
      label: "Secret Codes, Cheats & Passwords",
      description:
        "Produce a cheats, codes, and passwords reference. Document invincibility and weapon/item cheats, level-select or stage passwords, debug keys, developer rooms, easter eggs, and era-specific tricks (POKE codes, Game Genie / Action Replay style notes when historically relevant). For each entry give the exact code/input method, platform caveats, and what it does. Prefer verified lists over rumor.",
    },
    {
      id: "Boss & Enemy Compendium",
      label: "Boss & Enemy Compendium",
      description:
        "Produce a boss and enemy compendium useful during combat. Catalog regular enemies and bosses with attack patterns, tells, weaknesses/resistances, recommended tactics, and rewards or loot when applicable. Use consistent stat-style key/value rows where helpful and dedicate sections to major boss fights with phase-by-phase strategy.",
    },
    {
      id: "Soundtrack, Trivia & Historical Companion",
      label: "Soundtrack, Trivia & Historical Companion",
      description:
        "Produce a soundtrack, trivia, and historical companion. Cover audio hardware and sound-chip feats for the platform, composers and notable tracks, development anecdotes, box-art and packaging history, regional port differences, censorship or localization changes, and lasting cultural impact. Favor documented trivia and production history over gameplay walkthrough content.",
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
