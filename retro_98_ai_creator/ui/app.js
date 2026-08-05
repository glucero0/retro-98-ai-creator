/* global pywebview, RGC_CATALOG */

(function () {
  "use strict";

  const state = {
    creations: [],
    active: null,
    focused: "form",
    open: { form: true, viewer: false, library: false, control: false, "image-edit": false, "video-edit": false },
    minimized: { form: false, viewer: false, library: false, control: false, "image-edit": false, "video-edit": false },
    generating: false,
    modelLoading: false,
    preloadJobId: null,
    soundEnabled: true,
    crtEnabled: false,
    uiScale: 1,
    uiFont: "inter",
    config: null,
    viewerTab: "doc",
    speechPlaying: false,
    controlTab: "ai",
    archiveSort: { key: "created", dir: "desc" },
    presets: [],
    creationTypes: [],
    suggestedHfModels: null,
    suggestedOpenRouterModels: null,
    studioBasis: null, // { creationId, modality, fileUrl, mimeType, title }
    appTheme: "light",
    customTheme: {
      desktopColor: "#008080",
      windowColor: "#c0c0c0",
      titleColor: "#000080",
      textColor: "#222222",
      font: "sans",
    },
  };

  /**
   * App chrome fonts. "retro-pixel" is local (98.css). Others are open-source
   * faces loaded from Bunny Fonts (Google Fonts mirror) on demand.
   */
  const UI_FONTS = {
    "retro-pixel": {
      label: "Retro Pixel (Win98)",
      stack: '"Pixelated MS Sans Serif", "MS Sans Serif", Tahoma, sans-serif',
      google: null,
      pixel: true,
    },
    inter: {
      label: "Inter",
      stack: 'Inter, "Segoe UI", Tahoma, sans-serif',
      google: "Inter:400,700",
    },
    roboto: {
      label: "Roboto",
      stack: 'Roboto, "Segoe UI", Tahoma, sans-serif',
      google: "Roboto:400,700",
    },
    "open-sans": {
      label: "Open Sans",
      stack: '"Open Sans", "Segoe UI", Tahoma, sans-serif',
      google: "Open+Sans:400,700",
    },
    lato: {
      label: "Lato",
      stack: 'Lato, "Segoe UI", Tahoma, sans-serif',
      google: "Lato:400,700",
    },
    montserrat: {
      label: "Montserrat",
      stack: 'Montserrat, "Segoe UI", Tahoma, sans-serif',
      google: "Montserrat:400,700",
    },
    "source-sans-3": {
      label: "Source Sans 3",
      stack: '"Source Sans 3", "Segoe UI", Tahoma, sans-serif',
      google: "Source+Sans+3:400,700",
    },
    nunito: {
      label: "Nunito",
      stack: 'Nunito, "Segoe UI", Tahoma, sans-serif',
      google: "Nunito:400,700",
    },
    poppins: {
      label: "Poppins",
      stack: 'Poppins, "Segoe UI", Tahoma, sans-serif',
      google: "Poppins:400,700",
    },
    raleway: {
      label: "Raleway",
      stack: 'Raleway, "Segoe UI", Tahoma, sans-serif',
      google: "Raleway:400,700",
    },
    ubuntu: {
      label: "Ubuntu",
      stack: 'Ubuntu, "Segoe UI", Tahoma, sans-serif',
      google: "Ubuntu:400,700",
    },
    "noto-sans": {
      label: "Noto Sans",
      stack: '"Noto Sans", "Segoe UI", Tahoma, sans-serif',
      google: "Noto+Sans:400,700",
    },
    "work-sans": {
      label: "Work Sans",
      stack: '"Work Sans", "Segoe UI", Tahoma, sans-serif',
      google: "Work+Sans:400,700",
    },
    "ibm-plex-sans": {
      label: "IBM Plex Sans",
      stack: '"IBM Plex Sans", "Segoe UI", Tahoma, sans-serif',
      google: "IBM+Plex+Sans:400,700",
    },
    "pt-sans": {
      label: "PT Sans",
      stack: '"PT Sans", "Segoe UI", Tahoma, sans-serif',
      google: "PT+Sans:400,700",
    },
    "fira-sans": {
      label: "Fira Sans",
      stack: '"Fira Sans", "Segoe UI", Tahoma, sans-serif',
      google: "Fira+Sans:400,700",
    },
    rubik: {
      label: "Rubik",
      stack: 'Rubik, "Segoe UI", Tahoma, sans-serif',
      google: "Rubik:400,700",
    },
    "dm-sans": {
      label: "DM Sans",
      stack: '"DM Sans", "Segoe UI", Tahoma, sans-serif',
      google: "DM+Sans:400,700",
    },
    "libre-franklin": {
      label: "Libre Franklin",
      stack: '"Libre Franklin", "Segoe UI", Tahoma, sans-serif',
      google: "Libre+Franklin:400,700",
    },
    merriweather: {
      label: "Merriweather",
      stack: 'Merriweather, Georgia, "Times New Roman", serif',
      google: "Merriweather:400,700",
    },
    "source-serif-4": {
      label: "Source Serif 4",
      stack: '"Source Serif 4", Georgia, "Times New Roman", serif',
      google: "Source+Serif+4:400,700",
    },
  };

  // Legacy stacks for Viewer document themes (not app chrome)
  const UI_FONT_STACKS = {
    sans: UI_FONTS["retro-pixel"].stack,
    serif: 'Georgia, "Times New Roman", Times, serif',
    mono: '"Courier New", Courier, monospace',
  };

  const FONT_STACKS = {
    mono: '"Courier New", Courier, monospace',
    serif: 'Georgia, "Times New Roman", serif',
    sans: UI_FONTS["retro-pixel"].stack,
  };

  const _loadedUiFontLinks = Object.create(null);

  function resolveUiFontKey(font) {
    const raw = String(font || "").trim().toLowerCase();
    if (UI_FONTS[raw]) return raw;
    // Legacy custom_theme.font values
    if (raw === "serif") return "merriweather";
    if (raw === "mono") return "ibm-plex-sans";
    if (raw === "sans") return "retro-pixel";
    return "inter";
  }

  function ensureUiFontLoaded(fontKey) {
    const key = resolveUiFontKey(fontKey);
    const meta = UI_FONTS[key];
    if (!meta || !meta.google || _loadedUiFontLinks[key]) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.bunny.net/css?family=" + meta.google + "&display=swap";
    link.dataset.uiFont = key;
    document.head.appendChild(link);
    _loadedUiFontLinks[key] = link;
  }

  function applyUiFont(fontKey) {
    const key = resolveUiFontKey(fontKey);
    const meta = UI_FONTS[key] || UI_FONTS.inter;
    state.uiFont = key;
    ensureUiFontLoaded(key);
    document.documentElement.style.setProperty("--ui-font", meta.stack);
    document.documentElement.setAttribute("data-ui-font", key);
    if ($("#ui-font")) $("#ui-font").value = key;
  }

  function fillUiFontSelect() {
    const sel = $("#ui-font");
    if (!sel) return;
    const prev = resolveUiFontKey(sel.value || state.uiFont || "inter");
    sel.innerHTML = "";
    Object.keys(UI_FONTS).forEach((key) => {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = UI_FONTS[key].label;
      opt.style.fontFamily = UI_FONTS[key].stack;
      sel.appendChild(opt);
    });
    sel.value = prev;
  }

  function fontStackFromStyle(fontStyle) {
    const s = (fontStyle || "").toLowerCase();
    if (s === "dos-vga" || s === "workbench" || s === "pixel" || s === "mono") {
      return FONT_STACKS.mono;
    }
    if (s === "serif-parchment" || s === "serif") return FONT_STACKS.serif;
    return FONT_STACKS.sans;
  }

  /** Palette overrides ported from retro_web_app CreationViewerWindow */
  const THEMES = {
    "apple2-green": {
      themeName: "Apple II Phosphor Green",
      bgColor: "#000000",
      cardBg: "#021802",
      textColor: "#00ff33",
      accentColor: "#00aa22",
      headerBg: "#012001",
      fontStyle: "dos-vga",
    },
    "apple2-amber": {
      themeName: "Apple II Phosphor Amber",
      bgColor: "#000000",
      cardBg: "#1a1000",
      textColor: "#ffb000",
      accentColor: "#cc8800",
      headerBg: "#2a1800",
      fontStyle: "dos-vga",
    },
    "sinclair-spectrum": {
      themeName: "Timex Sinclair / ZX Spectrum",
      bgColor: "#000000",
      cardBg: "#ffffff",
      textColor: "#000000",
      accentColor: "#d00000",
      headerBg: "#1a1a1a",
      fontStyle: "dos-vga",
    },
    c64: {
      themeName: "Commodore 64 Blue & Cyan",
      bgColor: "#352879",
      cardBg: "#403285",
      textColor: "#a297e0",
      accentColor: "#6c5eb5",
      headerBg: "#352879",
      fontStyle: "dos-vga",
    },
    workbench: {
      themeName: "Commodore Amiga Workbench 1.3",
      bgColor: "#0055aa",
      cardBg: "#ffffff",
      textColor: "#000000",
      accentColor: "#ffaa00",
      headerBg: "#0055aa",
      fontStyle: "workbench",
    },
    atari2600: {
      themeName: "Atari 2600 Woodgrain & Sunset",
      bgColor: "#2d1606",
      cardBg: "#3d2210",
      textColor: "#f8b800",
      accentColor: "#d05800",
      headerBg: "#1f0d02",
      fontStyle: "dos-vga",
    },
    "atari-st": {
      themeName: "Atari ST TOS Desktop",
      bgColor: "#008080",
      cardBg: "#ffffff",
      textColor: "#000000",
      accentColor: "#00a8a8",
      headerBg: "#005555",
      fontStyle: "dos-vga",
    },
    "amstrad-cpc": {
      themeName: "Amstrad CPC Color Palette",
      bgColor: "#000080",
      cardBg: "#0000a0",
      textColor: "#ffff00",
      accentColor: "#00ffff",
      headerBg: "#000060",
      fontStyle: "dos-vga",
    },
    "bbc-micro": {
      themeName: "BBC Micro / Acorn Palette",
      bgColor: "#600000",
      cardBg: "#1a0000",
      textColor: "#ffff00",
      accentColor: "#ff3333",
      headerBg: "#400000",
      fontStyle: "dos-vga",
    },
    vectrex: {
      themeName: "Vectrex Vector Monitor",
      bgColor: "#000000",
      cardBg: "#030c1a",
      textColor: "#00ffff",
      accentColor: "#0088ff",
      headerBg: "#001a33",
      fontStyle: "dos-vga",
    },
    gameboy: {
      themeName: "Game Boy Monochromatic Green",
      bgColor: "#0f380f",
      cardBg: "#306230",
      textColor: "#9bbc0f",
      accentColor: "#8bac0f",
      headerBg: "#0f380f",
      fontStyle: "pixel",
    },
    "dos-vga": {
      themeName: "MS-DOS Cyber VGA",
      bgColor: "#000000",
      cardBg: "#051505",
      textColor: "#00ff66",
      accentColor: "#008833",
      headerBg: "#003311",
      fontStyle: "dos-vga",
    },
    nes: {
      themeName: "NES Gray",
      bgColor: "#212121",
      cardBg: "#e0e0e0",
      textColor: "#111111",
      accentColor: "#e52521",
      headerBg: "#7c7c7c",
      fontStyle: "pixel",
    },
    "snes-parchment": {
      themeName: "SNES 16-Bit Parchment",
      bgColor: "#2b1b0e",
      cardBg: "#f4ebd0",
      textColor: "#2b1b0e",
      accentColor: "#8b0000",
      headerBg: "#8b0000",
      fontStyle: "serif-parchment",
    },
    "sega-genesis": {
      themeName: "Sega Genesis / Mega Drive Gold",
      bgColor: "#0a0a14",
      cardBg: "#181828",
      textColor: "#ffd700",
      accentColor: "#0060a8",
      headerBg: "#003060",
      fontStyle: "dos-vga",
    },
    dreamcast: {
      themeName: "Sega Dreamcast Orange & White",
      bgColor: "#ff6600",
      cardBg: "#ffffff",
      textColor: "#111827",
      accentColor: "#ff6600",
      headerBg: "#e65c00",
      fontStyle: "retro-sans",
    },
    "ps1-classic": {
      themeName: "PlayStation 1 Classic Gray",
      bgColor: "#7a818c",
      cardBg: "#1a2332",
      textColor: "#f3f4f6",
      accentColor: "#00439c",
      headerBg: "#0e1726",
      fontStyle: "retro-sans",
    },
    "ps2-darkness": {
      themeName: "PlayStation 2 Deep Space",
      bgColor: "#000511",
      cardBg: "#0a1228",
      textColor: "#e2e8f0",
      accentColor: "#0066cc",
      headerBg: "#001a40",
      fontStyle: "retro-sans",
    },
    "ps3-xmb": {
      themeName: "PlayStation 3 XMB Crimson Wave",
      bgColor: "#120008",
      cardBg: "#1f0a14",
      textColor: "#f3f4f6",
      accentColor: "#dc2626",
      headerBg: "#3b0712",
      fontStyle: "retro-sans",
    },
    "ps4-ps5": {
      themeName: "PlayStation 4 / PS5 Midnight Blue",
      bgColor: "#0a1128",
      cardBg: "#0f172a",
      textColor: "#f8fafc",
      accentColor: "#3b82f6",
      headerBg: "#1e3a8a",
      fontStyle: "retro-sans",
    },
    "xbox-original": {
      themeName: "Original Xbox Matrix Green",
      bgColor: "#031203",
      cardBg: "#0a220a",
      textColor: "#22ff33",
      accentColor: "#107c41",
      headerBg: "#003300",
      fontStyle: "dos-vga",
    },
    "xbox-360": {
      themeName: "Xbox 360 Blade UI Emerald",
      bgColor: "#dce3eb",
      cardBg: "#ffffff",
      textColor: "#0f172a",
      accentColor: "#107c41",
      headerBg: "#107c41",
      fontStyle: "retro-sans",
    },
    "xbox-series": {
      themeName: "Xbox Series X Dark Minimal",
      bgColor: "#0d1117",
      cardBg: "#161b22",
      textColor: "#f0f6fc",
      accentColor: "#107c41",
      headerBg: "#052e16",
      fontStyle: "retro-sans",
    },
    "wii-menu": {
      themeName: "Nintendo Wii Menu Cyan",
      bgColor: "#e8f4f8",
      cardBg: "#ffffff",
      textColor: "#0f172a",
      accentColor: "#00a4e4",
      headerBg: "#00a4e4",
      fontStyle: "retro-sans",
    },
    gamecube: {
      themeName: "Nintendo GameCube Indigo",
      bgColor: "#311042",
      cardBg: "#481e60",
      textColor: "#f3f4f6",
      accentColor: "#facc15",
      headerBg: "#240833",
      fontStyle: "retro-sans",
    },
    "switch-neon": {
      themeName: "Nintendo Switch Joy-Con Neon",
      bgColor: "#18181c",
      cardBg: "#24242c",
      textColor: "#ffffff",
      accentColor: "#ff3c28",
      headerBg: "#00c3e3",
      fontStyle: "retro-sans",
    },
    win98: {
      themeName: "Windows 98 Standard",
      bgColor: "#008080",
      cardBg: "#ffffff",
      textColor: "#000000",
      accentColor: "#000080",
      headerBg: "#000080",
      fontStyle: "retro-sans",
    },
  };

  // Back-compat aliases for older saved Viewer palette selections
  THEMES.amiga = THEMES.workbench;
  THEMES.dos = THEMES["dos-vga"];
  THEMES.xbox = THEMES["xbox-original"];

  /** App shell themes (Control Panel → Display). Separate from Viewer palettes above. */
  const APP_THEME_PRESETS = {
    light: {
      themeName: "Light Mode (Day)",
      bgColor: "#d8dee6",
      cardBg: "#f0f0f0",
      textColor: "#1a1a1a",
      accentColor: "#0b5cab",
      headerBg: "#0a5aab",
      fontStyle: "sans",
    },
    dark: {
      themeName: "Dark Mode (Night)",
      bgColor: "#12151a",
      cardBg: "#2a2f38",
      textColor: "#e8eaed",
      accentColor: "#5b9bd5",
      headerBg: "#1a3358",
      fontStyle: "sans",
    },
  };

  function resolveAppThemeKey(key) {
    const k = (key || "").trim().toLowerCase();
    if (k === "light" || k === "dark" || k === "custom") return k;
    // Migrate legacy console/app theme keys → closest preset
    if (
      k === "win98" ||
      k === "wii-menu" ||
      k === "xbox-360" ||
      k === "dreamcast" ||
      k === "nes" ||
      k === "sinclair-spectrum"
    ) {
      return "light";
    }
    if (k) return "dark";
    return "light";
  }

  function normalizeHexColor(value, fallback) {
    const raw = String(value || "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(raw)) return raw.toLowerCase();
    if (/^#[0-9a-fA-F]{3}$/.test(raw)) {
      return (
        "#" +
        raw[1] +
        raw[1] +
        raw[2] +
        raw[2] +
        raw[3] +
        raw[3]
      ).toLowerCase();
    }
    return fallback;
  }

  function resolveCustomFontKey(font) {
    const f = String(font || "sans").toLowerCase();
    if (f === "serif" || f === "mono") return f;
    return "sans";
  }

  function readCustomThemeFromControls() {
    return {
      desktopColor: normalizeHexColor(
        $("#custom-desktop-color") && $("#custom-desktop-color").value,
        state.customTheme.desktopColor
      ),
      windowColor: normalizeHexColor(
        $("#custom-window-color") && $("#custom-window-color").value,
        state.customTheme.windowColor
      ),
      titleColor: normalizeHexColor(
        $("#custom-title-color") && $("#custom-title-color").value,
        state.customTheme.titleColor
      ),
      textColor: normalizeHexColor(
        $("#custom-text-color") && $("#custom-text-color").value,
        state.customTheme.textColor
      ),
      // Legacy field; app chrome font is state.uiFont / #ui-font
      font: state.customTheme.font || "sans",
    };
  }

  function writeCustomThemeToControls(custom) {
    const c = custom || state.customTheme;
    if ($("#custom-desktop-color")) $("#custom-desktop-color").value = c.desktopColor;
    if ($("#custom-window-color")) $("#custom-window-color").value = c.windowColor;
    if ($("#custom-title-color")) $("#custom-title-color").value = c.titleColor;
    if ($("#custom-text-color")) $("#custom-text-color").value = c.textColor;
  }

  function syncCustomThemeControlsVisibility() {
    const panel = $("#app-theme-custom");
    if (!panel) return;
    const key =
      ($("#app-theme") && $("#app-theme").value) || state.appTheme || "light";
    panel.hidden = key !== "custom";
  }

  function getAppThemePalette(themeKey) {
    const key = resolveAppThemeKey(themeKey);
    if (key === "custom") {
      const c = state.customTheme;
      return {
        themeName: "Customize",
        bgColor: c.desktopColor,
        cardBg: c.windowColor,
        textColor: c.textColor,
        accentColor: c.titleColor,
        headerBg: c.titleColor,
        fontStyle: c.font,
      };
    }
    return APP_THEME_PRESETS[key] || APP_THEME_PRESETS.light;
  }

  function _hexToRgb(hex) {
    const h = String(hex || "").replace("#", "").trim();
    if (h.length === 3) {
      return {
        r: parseInt(h[0] + h[0], 16),
        g: parseInt(h[1] + h[1], 16),
        b: parseInt(h[2] + h[2], 16),
      };
    }
    if (h.length >= 6) {
      return {
        r: parseInt(h.slice(0, 2), 16),
        g: parseInt(h.slice(2, 4), 16),
        b: parseInt(h.slice(4, 6), 16),
      };
    }
    return { r: 0, g: 128, b: 128 };
  }

  function _mixHex(a, b, t) {
    const A = _hexToRgb(a);
    const B = _hexToRgb(b);
    const m = (x, y) => Math.round(x + (y - x) * t);
    const to = (n) => n.toString(16).padStart(2, "0");
    return "#" + to(m(A.r, B.r)) + to(m(A.g, B.g)) + to(m(A.b, B.b));
  }

  function _luminance(hex) {
    const { r, g, b } = _hexToRgb(hex);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  }

  /** Desktop is a solid theme color (no patterned wallpaper). */
  function applyAppTheme(themeKey) {
    const key = resolveAppThemeKey(themeKey);
    if (key === "custom") {
      state.customTheme = readCustomThemeFromControls();
    }
    const t = getAppThemePalette(key);
    state.appTheme = key;

    const root = document.documentElement;
    const mid = _mixHex(t.bgColor, "#ffffff", 0.12);
    const deep = _mixHex(t.bgColor, "#000000", 0.28);
    const lightDesktop = _luminance(t.bgColor) > 0.55;

    // Window surface: prefer cardBg; nudge pure white toward classic silver for chrome feel
    let windowBg = t.cardBg || "#c0c0c0";
    if (_normHex(windowBg) === "ffffff") {
      windowBg = _mixHex(windowBg, "#c0c0c0", 0.55);
    }
    const text = t.textColor || "#222222";
    const title = t.headerBg || t.accentColor || "#000080";
    const accent = t.accentColor || "#000080";
    const titleMid = _mixHex(title, accent, 0.4);
    const titleText = _luminance(title) > 0.55 ? "#111111" : "#ffffff";
    const titleInactive = _mixHex(title, "#808080", 0.55);
    const titleInactiveMid = _mixHex(titleInactive, "#ffffff", 0.18);
    const titleTextInactive =
      _luminance(titleInactive) > 0.55 ? "#333333" : "#d4d4d4";
    const lightWin = _luminance(windowBg) > 0.45;
    const buttonFace = lightWin
      ? _mixHex(windowBg, "#dfdfdf", 0.25)
      : _mixHex(windowBg, "#ffffff", 0.12);
    const buttonText = _luminance(buttonFace) > 0.5 ? "#222222" : "#f0f0f0";
    const darkButtons = _luminance(buttonFace) <= 0.5;
    const inputBg = lightWin
      ? _mixHex(windowBg, "#ffffff", 0.65)
      : _mixHex(windowBg, "#000000", 0.25);
    const inputText = _luminance(inputBg) > 0.5 ? "#111111" : text;
    const muted = _mixHex(text, windowBg, 0.42);
    const taskbar = lightWin
      ? _mixHex(windowBg, "#b0b0b0", 0.2)
      : _mixHex(windowBg, "#ffffff", 0.08);
    const accentText = _luminance(accent) > 0.55 ? "#111111" : "#ffffff";
    const highlight = lightWin
      ? _mixHex("#ffffd0", accent, 0.12)
      : _mixHex(windowBg, accent, 0.28);
    const borderLight = lightWin ? "#ffffff" : _mixHex(windowBg, "#ffffff", 0.38);
    const borderMid = lightWin ? "#dfdfdf" : _mixHex(windowBg, "#ffffff", 0.2);
    const borderDark = lightWin ? "#808080" : _mixHex(windowBg, "#000000", 0.35);
    const borderDarker = lightWin ? "#0a0a0a" : _mixHex(windowBg, "#000000", 0.7);

    root.style.setProperty("--desktop-bg", t.bgColor);
    root.style.setProperty("--desktop-bg-mid", mid);
    root.style.setProperty("--desktop-bg-deep", deep);
    root.style.setProperty("--desktop-wallpaper", "none");
    root.style.setProperty("--app-accent", accent);
    root.style.setProperty("--app-header", title);
    root.style.setProperty("--app-card", t.cardBg);
    root.style.setProperty("--app-text", text);
    root.style.setProperty("--icon-fg", lightDesktop ? "#111111" : "#ffffff");
    root.style.setProperty(
      "--icon-shadow",
      lightDesktop ? "rgba(255,255,255,0.7)" : "#000000"
    );
    root.style.setProperty("--icon-glyph-bg", buttonFace);

    root.style.setProperty("--ui-window", windowBg);
    root.style.setProperty("--ui-text", text);
    root.style.setProperty("--ui-muted", muted);
    root.style.setProperty("--ui-title", title);
    root.style.setProperty("--ui-title-mid", titleMid);
    root.style.setProperty("--ui-title-text", titleText);
    root.style.setProperty("--ui-title-inactive", titleInactive);
    root.style.setProperty("--ui-title-inactive-mid", titleInactiveMid);
    root.style.setProperty("--ui-title-text-inactive", titleTextInactive);
    root.style.setProperty("--ui-accent", accent);
    root.style.setProperty("--ui-accent-text", accentText);
    root.style.setProperty("--ui-button", buttonFace);
    root.style.setProperty("--ui-button-text", buttonText);
    root.style.setProperty("--ui-input", inputBg);
    root.style.setProperty("--ui-input-text", inputText);
    root.style.setProperty("--ui-taskbar", taskbar);
    root.style.setProperty("--ui-highlight", highlight);
    root.style.setProperty("--ui-border-light", borderLight);
    root.style.setProperty("--ui-border-mid", borderMid);
    root.style.setProperty("--ui-border-dark", borderDark);
    root.style.setProperty("--ui-border-darker", borderDarker);

    applyUiFont(state.uiFont || "inter");

    const desktop = $("#desktop");
    if (desktop) desktop.setAttribute("data-app-theme", key);
    document.documentElement.setAttribute("data-app-theme", key);
    document.documentElement.setAttribute(
      "data-ui-button-dark",
      darkButtons ? "1" : "0"
    );

    if ($("#app-theme") && [...$("#app-theme").options].some((o) => o.value === key)) {
      $("#app-theme").value = key;
    }
    syncCustomThemeControlsVisibility();
  }

  function _normHex(hex) {
    return String(hex || "")
      .replace("#", "")
      .trim()
      .toLowerCase();
  }

  let audioCtx = null;
  function beep(freq, dur, type) {
    if (!state.soundEnabled) return;
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.type = type || "square";
      o.frequency.value = freq;
      g.gain.value = 0.04;
      o.connect(g);
      g.connect(audioCtx.destination);
      o.start();
      o.stop(audioCtx.currentTime + (dur || 0.06));
    } catch (_) {
      /* ignore */
    }
  }

  function api() {
    return window.pywebview && window.pywebview.api;
  }

  function waitForApi(timeoutMs) {
    timeoutMs = timeoutMs || 8000;
    return new Promise((resolve) => {
      if (api()) return resolve(api());
      const onReady = () => resolve(api());
      window.addEventListener("pywebviewready", onReady, { once: true });
      setTimeout(() => {
        window.removeEventListener("pywebviewready", onReady);
        resolve(api());
      }, timeoutMs);
    });
  }

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function showToast(msg, durationMs) {
    const el = $("#error-toast");
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(showToast._t);
    const ms =
      typeof durationMs === "number"
        ? durationMs
        : String(msg || "").length > 120
          ? 12000
          : 5000;
    showToast._t = setTimeout(() => {
      el.hidden = true;
    }, ms);
  }

  function setProgress(msg) {
    const text = $("#gen-status-text");
    if (text) text.textContent = msg || "Ready";
  }

  // ── Busy / progress dialog ─────────────────────────────────────────
  const BUSY_HINTS = {
    generate:
      "Creating text, an image, or video from your prompt. You can cancel anytime.",
    preload:
      "Downloading / loading local text, image, and video models. Create is blocked until this finishes.",
    default:
      "Gemini usually finishes in seconds. Local models can take minutes.",
  };

  const busy = {
    visible: false,
    showTimer: null,
    elapsedTimer: null,
    startedAt: 0,
    title: "Please wait…",
    activity: null, // "generate" | "preload" | "other"
    cancellable: false,
    cancelling: false,
    jobId: null,
  };

  function setBusyHint(text) {
    const hintEl = $("#busy-hint");
    if (hintEl) hintEl.textContent = text || BUSY_HINTS.default;
  }

  function setBusyTitle(title) {
    if (!title) return;
    busy.title = title;
    const titleEl = $("#busy-title");
    if (titleEl && (busy.visible || busy.showTimer)) {
      titleEl.textContent = title;
    }
  }

  function showConfirm(title, message, opts) {
    opts = opts || {};
    return new Promise((resolve) => {
      const overlay = $("#confirm-overlay");
      const titleEl = $("#confirm-title");
      const msgEl = $("#confirm-message");
      const yesBtn = $("#confirm-yes");
      const noBtn = $("#confirm-no");
      if (!overlay || !yesBtn || !noBtn) {
        resolve(window.confirm(message || title));
        return;
      }
      const prevYes = yesBtn.textContent;
      const prevNo = noBtn.textContent;
      if (titleEl) titleEl.textContent = title || "Confirm";
      if (msgEl) msgEl.textContent = message || "";
      yesBtn.textContent = opts.yesLabel || "Yes";
      noBtn.textContent = opts.noLabel || "No";
      overlay.hidden = false;

      const finish = (value) => {
        overlay.hidden = true;
        yesBtn.textContent = prevYes;
        noBtn.textContent = prevNo;
        yesBtn.removeEventListener("click", onYes);
        noBtn.removeEventListener("click", onNo);
        resolve(value);
      };
      const onYes = () => finish(true);
      const onNo = () => finish(false);
      yesBtn.addEventListener("click", onYes);
      noBtn.addEventListener("click", onNo);
      (opts.focusNo ? noBtn : yesBtn).focus();
    });
  }

  /**
   * Search Results dialog for ambiguous game titles.
   * Resolves to the selected candidate object, or null if cancelled.
   */
  function showSearchResults(query, candidates) {
    return new Promise((resolve) => {
      const overlay = $("#search-results-overlay");
      const titleEl = $("#search-results-title");
      const msgEl = $("#search-results-message");
      const listEl = $("#search-results-list");
      const cancelBtn = $("#search-results-cancel");
      const items = Array.isArray(candidates) ? candidates : [];

      if (!overlay || !listEl || !cancelBtn) {
        resolve(null);
        return;
      }

      if (titleEl) titleEl.textContent = "Search Results";
      if (msgEl) {
        const q = (query || "").trim();
        msgEl.textContent = q
          ? `Multiple games match "${q}". Select the title you meant:`
          : "Multiple games match. Select the title you meant:";
      }

      const finish = (value) => {
        overlay.hidden = true;
        cancelBtn.removeEventListener("click", onCancel);
        listEl.innerHTML = "";
        resolve(value);
      };
      const onCancel = () => finish(null);

      listEl.innerHTML = "";
      items.forEach((c, idx) => {
        const li = document.createElement("li");
        li.setAttribute("role", "option");
        const btn = document.createElement("button");
        btn.type = "button";
        const name = (c && c.game) || "";
        const metaParts = [];
        if (c && c.year) metaParts.push(String(c.year));
        if (c && c.platform) metaParts.push(String(c.platform));
        if (c && c.note) metaParts.push(String(c.note));
        const titleSpan = document.createElement("span");
        titleSpan.className = "sr-title";
        titleSpan.textContent = name;
        btn.appendChild(titleSpan);
        if (metaParts.length) {
          const metaSpan = document.createElement("span");
          metaSpan.className = "sr-meta";
          metaSpan.textContent = metaParts.join(" · ");
          btn.appendChild(metaSpan);
        }
        btn.addEventListener("click", () => finish(c));
        if (idx === 0) btn.dataset.first = "1";
        li.appendChild(btn);
        listEl.appendChild(li);
      });

      overlay.hidden = false;
      cancelBtn.addEventListener("click", onCancel);
      const firstBtn = listEl.querySelector("button[data-first]") || cancelBtn;
      firstBtn.focus();
    });
  }

  function setCreateBlocked(blocked) {
    const btn = $("#btn-generate");
    if (!btn) return;
    if (blocked || state.generating || state.modelLoading) {
      btn.disabled = true;
    } else {
      btn.disabled = false;
    }
  }

  function finishModelDownload(ok, errMsg) {
    if (!state.modelLoading && !busy.visible) {
      // Already finished (guard against double completion from poll + bridge push)
      return;
    }
    state.modelLoading = false;
    state.preloadJobId = null;
    endBusy("Ready");
    setCreateBlocked(false);
    if (ok) {
      showToast("Local model ready");
      closeWindow("control");
      beep(880, 0.08, "triangle");
    } else {
      showToast(errMsg || "Model download / load failed");
      beep(200, 0.2, "sawtooth");
    }
  }

  async function startLocalModelDownload() {
    const a = api();
    if (!a) {
      showToast("Python bridge not ready.");
      return;
    }
    if (state.modelLoading) {
      showToast("A model download is already in progress…");
      return;
    }
    state.modelLoading = true;
    setCreateBlocked(true);
    beginBusy("Downloading models", "Starting Hugging Face downloads…", {
      delayMs: 0,
      activity: "preload",
      hint: BUSY_HINTS.preload,
    });

    let res;
    try {
      res = await a.preload_model();
    } catch (err) {
      finishModelDownload(false, String(err));
      return;
    }

    if (!res || !res.ok) {
      finishModelDownload(false, (res && res.error) || "Backend check failed");
      return;
    }

    if (res.job_id) {
      state.preloadJobId = res.job_id;
      await pollJob(res.job_id, "preload");
    } else {
      finishModelDownload(true);
    }
  }

  async function saveControlPanelSettings(opts) {
    opts = opts || {};
    const a = api();
    if (!a) {
      showToast("Python bridge not ready.");
      return;
    }
    if (!ensureApiKeyBeforeSave()) return;

    if (opts.applyDisplay) applyDisplaySettingsFromControls();

    const provider =
      ($("#backend-provider") && $("#backend-provider").value) || "gemini";
    const offerDownload = provider === "huggingface" && !!opts.offerDownload;
    const res = await a.save_settings(collectSettings(offerDownload));

    if (res.config) {
      state.config = res.config;
      try {
        const boot = await a.get_bootstrap();
        state.config = boot.config || res.config;
        fillControlPanel(boot);
      } catch (_) {
        fillControlPanel({
          config: res.config,
          suggestedModels: [],
          suggestedGeminiModels: [],
          suggestedOpenRouterModels: [],
          modelStatus: res.modelStatus,
        });
        updateApiKeyIndicators();
      }
      if ($("#gemini-key")) $("#gemini-key").value = "";
      if ($("#openrouter-key")) $("#openrouter-key").value = "";
    }

    // Always close Control Panel after a successful Save.
    closeWindow("control");
    showToast(res.message || "Saved");
    beep(750, 0.05);

    if (!offerDownload) return;

    const go = await showConfirm(
      "Download local models?",
      "Settings were saved.\n\n" +
        "Download and cache the Hugging Face text, image, and video models now?\n\n" +
        "Yes — start the downloads (Create stays blocked until they finish).\n" +
        "No — skip download for now (models load on first use)."
    );
    if (!go) {
      showToast("Saved — local models not downloaded yet.");
      return;
    }

    await startLocalModelDownload();
  }

  function formatElapsed(ms) {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return m + ":" + String(r).padStart(2, "0");
  }

  function updateBusyElapsed() {
    const el = $("#busy-elapsed");
    if (!el || !busy.startedAt) return;
    el.textContent = formatElapsed(Date.now() - busy.startedAt);
  }

  function setBusyCancelVisible(show) {
    const actions = $("#busy-actions");
    const btn = $("#busy-cancel");
    if (actions) actions.hidden = !show;
    if (btn) {
      btn.disabled = !!busy.cancelling;
      btn.textContent = busy.cancelling ? "Cancelling…" : "Cancel";
    }
  }

  function _showBusyNow(title, message, percent, hint) {
    const overlay = $("#busy-overlay");
    if (!overlay) return;
    $("#busy-title").textContent = title || "Please wait…";
    $("#busy-message").textContent = message || "Working…";
    if (hint) setBusyHint(hint);
    overlay.hidden = false;
    busy.visible = true;
    if (!busy.startedAt) busy.startedAt = Date.now();
    if (!busy.elapsedTimer) {
      updateBusyElapsed();
      busy.elapsedTimer = setInterval(updateBusyElapsed, 500);
    }
    setBusyPercent(percent);
    setBusyCancelVisible(!!busy.cancellable);
  }

  function setBusyPercent(percent) {
    const bar = $("#busy-bar");
    const indicator = $("#busy-indicator");
    const label = $("#busy-percent-label");
    if (!bar || !indicator) return;
    if (percent == null || Number.isNaN(Number(percent))) {
      indicator.classList.add("indeterminate");
      bar.style.width = "";
      bar.style.marginLeft = "";
      if (label) label.textContent = "";
    } else {
      const pct = Math.max(0, Math.min(100, Number(percent)));
      indicator.classList.remove("indeterminate");
      bar.style.marginLeft = "0";
      bar.style.width = pct + "%";
      if (label) label.textContent = Math.round(pct) + "%";
    }
  }

  /**
   * Show the busy dialog. Known long ops use delayMs=0.
   * Otherwise the dialog appears only if work is still going after delayMs
   * (default 1500ms) so short actions don't flash a modal.
   * opts.cancellable — show Cancel (generation jobs).
   * opts.activity — "generate" | "preload" | "other" (drives title/hint framing).
   * opts.hint — footer description for this activity.
   */
  function beginBusy(title, message, opts) {
    opts = opts || {};
    const delayMs = opts.delayMs != null ? opts.delayMs : 1500;
    busy.title = title || "Please wait…";
    busy.activity = opts.activity || "other";
    if ("cancellable" in opts) busy.cancellable = !!opts.cancellable;
    if ("jobId" in opts) busy.jobId = opts.jobId || null;
    if (!opts.cancellable) busy.cancelling = false;
    const hint =
      opts.hint != null
        ? opts.hint
        : busy.activity === "generate"
          ? BUSY_HINTS.generate
          : busy.activity === "preload"
            ? BUSY_HINTS.preload
            : null;
    clearTimeout(busy.showTimer);
    setProgress(message || title || "Working…");

    if (delayMs <= 0) {
      _showBusyNow(busy.title, message, opts.percent, hint);
      return;
    }

    // If already visible, just update
    if (busy.visible) {
      $("#busy-title").textContent = busy.title;
      $("#busy-message").textContent = message || "Working…";
      if (hint) setBusyHint(hint);
      if ("percent" in opts) setBusyPercent(opts.percent);
      setBusyCancelVisible(!!busy.cancellable);
      return;
    }

    busy.startedAt = Date.now();
    busy.showTimer = setTimeout(() => {
      _showBusyNow(busy.title, message, opts.percent, hint);
    }, delayMs);
  }

  function updateBusy(message, percent, title) {
    if (title) setBusyTitle(title);
    if (message) {
      setProgress(message);
      const msgEl = $("#busy-message");
      if (msgEl) msgEl.textContent = message;
    }
    if (percent !== undefined) setBusyPercent(percent);

    // If a deferred show is pending and we got real progress, show immediately
    if (!busy.visible && busy.showTimer && (message || percent != null || title)) {
      clearTimeout(busy.showTimer);
      busy.showTimer = null;
      _showBusyNow(busy.title, message || "Working…", percent);
    }
  }

  function endBusy(finalMessage) {
    clearTimeout(busy.showTimer);
    busy.showTimer = null;
    if (busy.elapsedTimer) {
      clearInterval(busy.elapsedTimer);
      busy.elapsedTimer = null;
    }
    busy.startedAt = 0;
    busy.visible = false;
    busy.activity = null;
    busy.cancellable = false;
    busy.cancelling = false;
    busy.jobId = null;
    setBusyCancelVisible(false);
    setBusyHint(BUSY_HINTS.default);
    const overlay = $("#busy-overlay");
    if (overlay) overlay.hidden = true;
    setProgress(finalMessage || "Ready");
  }

  function setStudioPlatform(platform) {
    // Platform select removed from Creation Studio; keep for API compatibility no-ops.
    void platform;
  }

  function getStudioPlatform() {
    return "";
  }

  function getStudioPrompt() {
    const field = $("#studio-prompt");
    return field ? field.value : "";
  }

  function setStudioPrompt(text) {
    const field = $("#studio-prompt");
    if (field) field.value = text || "";
  }

  function extractCreationTextBody(creation) {
    if (!creation) return "";
    const parts = [];
    const overview = (creation.overview || "").trim();
    if (overview) parts.push(overview);
    (creation.sections || []).forEach((sec) => {
      if (!sec || typeof sec !== "object") return;
      const st = (sec.title || "").trim();
      const sc = (sec.content || "").trim();
      if (st && sc) parts.push(st + "\n" + sc);
      else if (sc) parts.push(sc);
      else if (st) parts.push(st);
    });
    return parts.join("\n\n").trim();
  }

  function rememberImportedCreation(creation) {
    if (!creation || !creation.id) return;
    state.creations = [creation].concat(
      state.creations.filter((c) => c.id !== creation.id)
    );
    state.active = creation;
    renderArchives();
  }

  /**
   * Use an existing creation as the basis for new work of the same modality.
   * Text → Studio prompt. Image/video → Studio media-basis panel (not the editors).
   */
  async function useCreationAsBasis(creation) {
    if (!creation) {
      showToast("Open or select a creation first.");
      return;
    }
    const mod = creationModality(creation);
    const a = api();
    if (!a) {
      showToast("Python bridge required.");
      return;
    }

    if (mod === "text") {
      const prompt = (creation.prompt || "").trim();
      const body = extractCreationTextBody(creation);
      let seeded = "";
      if (prompt && body && body !== prompt) {
        seeded =
          prompt +
          "\n\nBased on this existing text, create an improved version:\n\n" +
          body;
      } else {
        seeded = prompt || body || creationTitle(creation);
      }
      clearStudioBasis();
      setStudioPrompt(seeded);
      openWindow("form");
      showToast("Text loaded into Studio as basis — edit the prompt, then CREATE.");
      beep(700, 0.04);
      return;
    }

    if (mod !== "image" && mod !== "video") {
      showToast("Unsupported creation type.");
      return;
    }

    const ok = await setStudioBasisFromCreation(creation);
    if (!ok) return;
    openWindow("form");
    showToast(
      (mod === "image" ? "Image" : "Video") +
        " loaded as Studio basis — describe the change, then CREATE."
    );
    beep(700, 0.04);
  }

  function clearStudioBasis() {
    state.studioBasis = null;
    renderStudioBasisPanel();
  }

  function renderStudioBasisPanel() {
    const win = $("#win-form");
    const panel = $("#studio-basis-panel");
    const preview = $("#studio-basis-preview");
    const label = $("#studio-basis-label");
    const layout = $("#studio-layout");
    const basis = state.studioBasis;
    if (!panel || !preview) return;

    if (!basis) {
      panel.hidden = true;
      if (win) {
        win.classList.remove("has-studio-basis");
        if (!win.style.width || parseInt(win.style.width, 10) >= 700) {
          win.style.width = "440px";
        }
      }
      if (layout) layout.classList.remove("has-basis");
      preview.innerHTML = '<p class="muted">No media loaded</p>';
      if (label) label.textContent = "";
      requestAnimationFrame(() => syncDesktopScrollExtent());
      return;
    }

    panel.hidden = false;
    if (layout) layout.classList.add("has-basis");
    if (win) {
      win.classList.add("has-studio-basis");
      const w = parseInt(win.style.width, 10);
      if (!Number.isFinite(w) || w < 720) win.style.width = "780px";
    }

    preview.innerHTML = "";
    if (basis.modality === "video") {
      const vid = document.createElement("video");
      vid.src = basis.fileUrl;
      vid.controls = true;
      vid.playsInline = true;
      preview.appendChild(vid);
    } else {
      const img = document.createElement("img");
      img.src = basis.fileUrl;
      img.alt = basis.title || "Basis image";
      preview.appendChild(img);
    }
    if (label) {
      label.textContent =
        (basis.modality === "video" ? "Video basis: " : "Image basis: ") +
        (basis.title || basis.creationId || "media");
    }
    requestAnimationFrame(() => syncDesktopScrollExtent());
  }

  async function setStudioBasisFromCreation(creation) {
    const a = api();
    if (!a || !creation) return false;
    const mod = creationModality(creation);
    if (mod !== "image" && mod !== "video") {
      showToast("Only image or video can be a media basis.");
      return false;
    }
    const payload = await a.get_media_payload(creation);
    const previewUrl =
      (payload && (payload.fileUrl || payload.dataUrl)) || "";
    if (!payload || !payload.ok || !previewUrl) {
      showToast((payload && payload.error) || "Could not load media for basis.");
      return false;
    }
    state.studioBasis = {
      creationId: creation.id,
      modality: mod,
      fileUrl: previewUrl,
      mimeType: payload.mimeType || creation.mimeType || "",
      title: creationTitle(creation),
      mediaPath: creation.mediaPath || "",
    };
    if (!(getStudioPrompt() || "").trim() && (creation.prompt || "").trim()) {
      setStudioPrompt(creation.prompt.trim());
    }
    renderStudioBasisPanel();
    return true;
  }

  async function studioLoadTextFile() {
    const a = api();
    if (!a) return;
    try {
      const res = await a.import_text_file(false);
      if (!res || res.cancelled) return;
      if (!res.ok) {
        showToast(res.error || "Import failed");
        return;
      }
      clearStudioBasis();
      setStudioPrompt(res.text || "");
      openWindow("form");
      showToast("Text loaded into Studio prompt — edit and CREATE when ready.");
      beep(700, 0.04);
    } catch (err) {
      showToast("Load failed: " + err);
    }
  }

  async function studioLoadMediaFile(modality) {
    const a = api();
    if (!a) return;
    beginBusy("Loading " + modality, "Reading file for Studio basis…", {
      delayMs: 0,
    });
    try {
      const res = await a.import_media_file(modality);
      if (!res || res.cancelled) return;
      if (!res.ok) {
        showToast(res.error || "Import failed");
        return;
      }
      rememberImportedCreation(res.creation);
      const ok = await setStudioBasisFromCreation(res.creation);
      if (!ok) return;
      openWindow("form");
      showToast(
        (modality === "image" ? "Image" : "Video") +
          " loaded as Studio basis — describe the change, then CREATE."
      );
      beep(900, 0.05);
    } catch (err) {
      showToast("Load failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  async function archivesImportText() {
    const a = api();
    if (!a) return;
    try {
      const res = await a.import_text_file(true);
      if (!res || res.cancelled) return;
      if (!res.ok) {
        showToast(res.error || "Import failed");
        return;
      }
      if (res.creation) {
        rememberImportedCreation(res.creation);
        renderDocument(res.creation);
        openWindow("viewer");
      }
      openWindow("library");
      showToast("Text imported into Archives");
      beep(900, 0.05);
    } catch (err) {
      showToast("Import failed: " + err);
    }
  }

  async function archivesImportMedia(modality) {
    const a = api();
    if (!a) return;
    const kind = modality === "video" ? "video" : "image";
    beginBusy("Importing " + kind, "Copying into Archives…", { delayMs: 0 });
    try {
      const res = await a.import_media_file(kind);
      if (!res || res.cancelled) return;
      if (!res.ok) {
        showToast(res.error || "Import failed");
        return;
      }
      if (res.creation) {
        rememberImportedCreation(res.creation);
        renderDocument(res.creation);
        openWindow("viewer");
      }
      openWindow("library");
      showToast(
        (kind === "image" ? "Image" : "Video") + " imported into Archives"
      );
      beep(900, 0.05);
    } catch (err) {
      showToast("Import failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  // ── Window manager ─────────────────────────────────────────────────
  function focusWindow(id) {
    state.focused = id;
    document.querySelectorAll(".app-window").forEach((w) => {
      const title = w.querySelector(".title-bar");
      if (w.dataset.window === id) {
        w.classList.add("focused");
        if (title) title.classList.remove("inactive");
      } else {
        w.classList.remove("focused");
        if (title) title.classList.add("inactive");
      }
    });
    renderTaskbar();
  }

  function openWindow(id) {
    state.open[id] = true;
    state.minimized[id] = false;
    const el = document.getElementById("win-" + id);
    if (el) {
      el.hidden = false;
      el.classList.remove("minimized");
    }
    focusWindow(id);
    beep(660, 0.04);
    // Let layout settle (esp. Control Panel height:auto) then extend scroll area
    requestAnimationFrame(() => syncDesktopScrollExtent());
    if (id === "control") {
      syncControlPanelWidth();
      refreshGeminiModelsForControlPanel();
    }
    if (id === "image-edit" && !imageEdit.creationId) {
      prepareEmptyImageEditor();
    }
    if (id === "video-edit" && !videoEdit.creationId) {
      prepareEmptyVideoEditor();
    }
  }

  let _geminiModelsRefreshSeq = 0;
  let _hfModelsRefreshSeq = 0;
  let _openrouterModelsRefreshSeq = 0;

  async function refreshGeminiModelsForControlPanel() {
    const a = api();
    const textSel = $("#gemini-text-model");
    const imageSel = $("#gemini-image-model");
    const videoSel = $("#gemini-video-model");
    if (!a || !textSel || !imageSel || !videoSel) return;

    const seq = ++_geminiModelsRefreshSeq;
    const prev = {
      text: textSel.value,
      image: imageSel.value,
      video: videoSel.value,
    };
    beginBusy(
      "Refreshing Gemini models",
      "Checking Google for models available to your API key…",
      {
        delayMs: 0,
        percent: 15,
        hint:
          "Each modality picker is filled with compatible models only. Requires a saved Gemini API key.",
      }
    );

    try {
      const res = await a.list_gemini_models();
      if (seq !== _geminiModelsRefreshSeq) return;
      const models = (res && res.models) || [];
      fillGeminiModalitySelect(textSel, prev.text, models, "text");
      fillGeminiModalitySelect(imageSel, prev.image, models, "image");
      fillGeminiModalitySelect(videoSel, prev.video, models, "video");
      if (res && res.ok) {
        updateBusy(
          "Loaded " +
            models.length +
            " Gemini model" +
            (models.length === 1 ? "" : "s") +
            " from Google.",
          100
        );
      } else {
        updateBusy(
          (res && res.error) ||
            "Could not refresh live models — showing the built-in fallback list.",
          100
        );
        if (res && res.error) showToast(res.error);
      }
      updateStudioBackendLabel({
        config: {
          backend: { provider: "gemini" },
          gemini: {
            text_model: textSel.value,
            image_model: imageSel.value,
            video_model: videoSel.value,
          },
        },
      });
    } catch (err) {
      if (seq !== _geminiModelsRefreshSeq) return;
      showToast("Model list refresh failed: " + err);
    } finally {
      if (seq === _geminiModelsRefreshSeq) {
        endBusy("Ready");
        requestAnimationFrame(() => syncDesktopScrollExtent());
      }
    }
  }

  async function refreshHfModelsForControlPanel() {
    const a = api();
    const textSel = $("#hf-text-model");
    const imageSel = $("#hf-image-model");
    const videoSel = $("#hf-video-model");
    if (!a || !textSel || !imageSel || !videoSel) return;

    const go = await showConfirm(
      "Refresh Hub models?",
      "This contacts Hugging Face and loads up to 20 popular models for each of Text, Image, and Video (ranked by downloads).\n\n" +
        "This usually takes about 5–15 seconds, depending on your connection.\n\n" +
        "OK — fetch the model lists now.\n" +
        "Cancel — keep the current lists.",
      { yesLabel: "OK", noLabel: "Cancel" }
    );
    if (!go) return;

    const seq = ++_hfModelsRefreshSeq;
    const prev = {
      text: textSel.value,
      image: imageSel.value,
      video: videoSel.value,
    };
    beginBusy(
      "Refreshing Hub models",
      "Asking Hugging Face for top text, image, and video models…",
      {
        delayMs: 0,
        percent: 15,
        hint: "Up to 20 models per modality, ranked by downloads. Usually 5–15 seconds.",
      }
    );

    try {
      const res = await a.list_hf_models();
      if (seq !== _hfModelsRefreshSeq) return;
      const models = (res && res.models) || [];
      state.suggestedHfModels = models;
      fillHfModalitySelect(textSel, prev.text, models, "text");
      fillHfModalitySelect(imageSel, prev.image, models, "image");
      fillHfModalitySelect(videoSel, prev.video, models, "video");
      if (res && res.ok) {
        const live = res.liveCount != null ? res.liveCount : models.length;
        updateBusy(
          "Loaded " +
            live +
            " Hub model" +
            (live === 1 ? "" : "s") +
            " (up to 20 per modality).",
          100
        );
        showToast("Hub model lists refreshed");
      } else {
        updateBusy(
          (res && res.error) ||
            "Could not refresh Hub models — showing the curated fallback list.",
          100
        );
        if (res && res.error) showToast(res.error);
      }
      updateStudioBackendLabel({
        config: {
          backend: { provider: "huggingface" },
          gemini: currentGeminiUiConfig(),
          openrouter: currentOpenRouterUiConfig(),
          huggingface: currentHfUiConfig(),
        },
      });
    } catch (err) {
      if (seq !== _hfModelsRefreshSeq) return;
      showToast("Hub model list refresh failed: " + err);
    } finally {
      if (seq === _hfModelsRefreshSeq) {
        endBusy("Ready");
        requestAnimationFrame(() => syncDesktopScrollExtent());
      }
    }
  }

  async function refreshOpenRouterModelsForControlPanel() {
    const a = api();
    const textSel = $("#openrouter-text-model");
    const imageSel = $("#openrouter-image-model");
    const videoSel = $("#openrouter-video-model");
    if (!a || !textSel || !imageSel || !videoSel) return;

    const go = await showConfirm(
      "Refresh OpenRouter models?",
      "This contacts OpenRouter and loads up to 20 popular models for each of Text, Image, and Video (ranked by popularity).\n\n" +
        "This usually takes about 5–15 seconds, depending on your connection.\n\n" +
        "OK — fetch the model lists now.\n" +
        "Cancel — keep the current lists.",
      { yesLabel: "OK", noLabel: "Cancel" }
    );
    if (!go) return;

    const seq = ++_openrouterModelsRefreshSeq;
    const prev = {
      text: textSel.value,
      image: imageSel.value,
      video: videoSel.value,
    };
    beginBusy(
      "Refreshing OpenRouter models",
      "Asking OpenRouter for top text, image, and video models…",
      {
        delayMs: 0,
        percent: 15,
        hint: "Up to 20 models per modality, ranked by popularity. Usually 5–15 seconds.",
      }
    );

    try {
      const res = await a.list_openrouter_models();
      if (seq !== _openrouterModelsRefreshSeq) return;
      const models = (res && res.models) || [];
      state.suggestedOpenRouterModels = models;
      fillOpenRouterModalitySelect(textSel, prev.text, models, "text");
      fillOpenRouterModalitySelect(imageSel, prev.image, models, "image");
      fillOpenRouterModalitySelect(videoSel, prev.video, models, "video");
      syncControlPanelWidth();
      requestAnimationFrame(() => syncDesktopScrollExtent());
      if (res && res.ok) {
        const live = res.liveCount != null ? res.liveCount : models.length;
        updateBusy(
          "Loaded " +
            live +
            " OpenRouter model" +
            (live === 1 ? "" : "s") +
            " (up to 20 per modality).",
          100
        );
        showToast("OpenRouter model lists refreshed");
      } else {
        updateBusy(
          (res && res.error) ||
            "Could not refresh OpenRouter models — showing the curated fallback list.",
          100
        );
        if (res && res.error) showToast(res.error);
      }
      updateStudioBackendLabel({
        config: {
          backend: { provider: "openrouter" },
          gemini: currentGeminiUiConfig(),
          openrouter: currentOpenRouterUiConfig(),
          huggingface: currentHfUiConfig(),
        },
      });
    } catch (err) {
      if (seq !== _openrouterModelsRefreshSeq) return;
      showToast("OpenRouter model list refresh failed: " + err);
    } finally {
      if (seq === _openrouterModelsRefreshSeq) {
        endBusy("Ready");
        requestAnimationFrame(() => syncDesktopScrollExtent());
      }
    }
  }

  function syncDesktopScrollExtent() {
    const desktop = $("#desktop");
    const layer = $("#windows-layer");
    if (!desktop || !layer) return;
    // With document zoom, layout sizes are already in zoomed CSS pixels.
    let maxBottom = window.innerHeight;
    document.querySelectorAll(".app-window").forEach((win) => {
      if (win.hidden || win.classList.contains("minimized")) return;
      const top = parseFloat(win.style.top);
      const y = Number.isFinite(top) ? top : win.offsetTop || 0;
      const h = win.offsetHeight || 0;
      maxBottom = Math.max(maxBottom, y + h + 24);
    });
    layer.style.minHeight = maxBottom + "px";
    desktop.style.minHeight = Math.max(window.innerHeight, maxBottom + 40) + "px";
  }

  async function cancelControlPanel() {
    // Discard unsaved Control Panel edits by restoring last saved config.
    const a = api();
    if (a) {
      try {
        const boot = await a.get_bootstrap();
        state.config = boot.config || state.config;
        fillControlPanel(boot);
      } catch (_) {
        if (state.config) {
          fillControlPanel({
            config: state.config,
            suggestedModels: [],
            suggestedGeminiModels: [],
            suggestedOpenRouterModels: [],
          });
        }
      }
    } else if (state.config) {
      fillControlPanel({
        config: state.config,
        suggestedModels: [],
        suggestedGeminiModels: [],
        suggestedOpenRouterModels: [],
      });
    }
    if ($("#gemini-key")) $("#gemini-key").value = "";
    if ($("#openrouter-key")) $("#openrouter-key").value = "";
    closeWindow("control");
  }

  async function confirmDiscardEditorEdits(kind) {
    const dirty = kind === "image" ? imageEdit.dirty : videoEdit.dirty;
    if (!dirty) return true;
    const label = kind === "image" ? "image" : "video";
    const winId = kind === "image" ? "image-edit" : "video-edit";
    const discard = await showConfirm(
      "Unsaved edits",
      "You have unsaved " +
        label +
        " edits. Closing will discard them.\n\nDiscard and close, or keep editing so you can save?",
      {
        yesLabel: "Discard",
        noLabel: "Keep Editing",
        focusNo: true,
      }
    );
    if (!discard) {
      if (state.open[winId]) focusWindow(winId);
      else openWindow(winId);
      return false;
    }
    return true;
  }

  async function requestCloseWindow(id) {
    if (id === "image-edit") {
      if (!(await confirmDiscardEditorEdits("image"))) return false;
    } else if (id === "video-edit") {
      if (!(await confirmDiscardEditorEdits("video"))) return false;
    }
    closeWindow(id);
    return true;
  }

  function closeWindow(id) {
    if (id === "viewer") stopSpeech();
    if (id === "image-edit") {
      imageEdit.sourceImg = null;
      imageEdit.creationId = null;
      imageEdit.crop = null;
      imageEdit.cropDrag = null;
      imageEdit.filters = null;
      imageEdit.rotation = 0;
      imageEdit.dirty = false;
      if (window.R98ImageEdit) {
        writeImageEditFiltersToUi(window.R98ImageEdit.DEFAULT_FILTERS);
        if ($("#edit-rotation")) $("#edit-rotation").value = 0;
        syncImageEditValueLabels();
      }
    }
    if (id === "video-edit") {
      videoEdit.dirty = false;
      resetVideoEditRuntime();
    }
    state.open[id] = false;
    state.minimized[id] = false;
    const el = document.getElementById("win-" + id);
    if (el) {
      el.hidden = true;
      el.classList.remove("minimized");
    }
    // Focus another already-open window — never open a closed one
    if (state.focused === id) {
      const preferred =
        (id === "image-edit" || id === "video-edit") &&
        state.open.viewer &&
        !state.minimized.viewer
          ? "viewer"
          : null;
      const next =
        preferred ||
        ["form", "viewer", "library", "control", "image-edit", "video-edit"].find(
          (wid) => wid !== id && state.open[wid] && !state.minimized[wid]
        );
      if (next) focusWindow(next);
      else state.focused = null;
    }
    renderTaskbar();
    beep(440, 0.04);
    syncDesktopScrollExtent();
  }

  function minimizeWindow(id) {
    state.minimized[id] = true;
    const el = document.getElementById("win-" + id);
    if (el) el.classList.add("minimized");
    renderTaskbar();
    beep(520, 0.03);
    syncDesktopScrollExtent();
  }

  function toggleStartMenu(force) {
    const menu = $("#start-menu");
    if (!menu) return;
    if (typeof force === "boolean") menu.hidden = !force;
    else menu.hidden = !menu.hidden;
  }

  // ── Drag windows by title bar ───────────────────────────────────────
  let dragState = null;

  function getDesktopBounds() {
    const layer = $("#windows-layer") || $("#desktop");
    const rect = layer.getBoundingClientRect();
    return {
      left: rect.left,
      top: rect.top,
      right: rect.right,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height,
    };
  }

  function clampWindowPosition(win, left, top) {
    const bounds = getDesktopBounds();
    const rect = win.getBoundingClientRect();
    const minVisible = 48;
    const maxLeft = bounds.width - minVisible;
    const maxTop = Math.max(0, bounds.height - minVisible);
    const minLeft = -(rect.width - minVisible);
    left = Math.min(Math.max(left, minLeft), maxLeft);
    top = Math.min(Math.max(top, 0), maxTop);
    return { left, top };
  }

  function enableWindowDragging() {
    document.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return;
      if (e.target.closest(".title-bar-controls")) return;
      const titleBar = e.target.closest(".app-window > .title-bar");
      if (!titleBar) return;
      const win = titleBar.parentElement;
      if (!win || !win.classList.contains("app-window")) return;

      const id = win.dataset.window;
      if (id) focusWindow(id);

      const rect = win.getBoundingClientRect();
      const layer = $("#windows-layer") || $("#desktop");
      const layerRect = layer.getBoundingClientRect();
      // Position is relative to windows-layer
      const startLeft = rect.left - layerRect.left;
      const startTop = rect.top - layerRect.top;

      dragState = {
        win,
        startX: e.clientX,
        startY: e.clientY,
        origLeft: startLeft,
        origTop: startTop,
      };
      win.classList.add("dragging");
      e.preventDefault();
    });

    document.addEventListener("mousemove", (e) => {
      if (!dragState) return;
      const dx = e.clientX - dragState.startX;
      const dy = e.clientY - dragState.startY;
      const next = clampWindowPosition(
        dragState.win,
        dragState.origLeft + dx,
        dragState.origTop + dy
      );
      dragState.win.style.left = next.left + "px";
      dragState.win.style.top = next.top + "px";
      dragState.win.style.right = "auto";
    });

    document.addEventListener("mouseup", () => {
      if (!dragState) return;
      dragState.win.classList.remove("dragging");
      dragState = null;
    });

    // Cancel drag if pointer leaves the window unexpectedly
    window.addEventListener("blur", () => {
      if (!dragState) return;
      dragState.win.classList.remove("dragging");
      dragState = null;
    });
  }

  // ── Resize windows from bottom-right grip ───────────────────────────
  let resizeState = null;

  function uiZoomFactor() {
    const fromStyle = Number(document.documentElement.style.zoom);
    if (Number.isFinite(fromStyle) && fromStyle > 0) return fromStyle;
    const fromState = Number(state.uiScale);
    return Number.isFinite(fromState) && fromState > 0 ? fromState : 1;
  }

  function enableWindowResizing() {
    document.querySelectorAll(".app-window").forEach((win) => {
      // Control Panel uses fixed tab widths + vertical scroll — no resize grip.
      if (win.id === "win-control") {
        win.querySelectorAll(".window-resize-handle").forEach((h) => h.remove());
        return;
      }
      if (win.querySelector(".window-resize-handle")) return;
      const handle = document.createElement("div");
      handle.className = "window-resize-handle";
      handle.title = "Resize";
      win.appendChild(handle);
    });

    document.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      const handle = e.target.closest(".window-resize-handle");
      if (!handle) return;
      const win = handle.closest(".app-window");
      if (!win || win.id === "win-control") return;
      const id = win.dataset.window;
      if (id) focusWindow(id);

      // Inline max-* fight explicit sizing and make the grip feel like it slips.
      win.style.maxHeight = "none";
      win.style.maxWidth = "none";

      const scale = uiZoomFactor();
      resizeState = {
        win,
        handle,
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        // offset* matches style width/height (CSS px); client deltas are zoomed
        origW: win.offsetWidth,
        origH: win.offsetHeight,
        origLeft: parseFloat(win.style.left) || win.offsetLeft || 0,
        origTop: parseFloat(win.style.top) || win.offsetTop || 0,
        scale,
      };
      win.classList.add("resizing");
      try {
        handle.setPointerCapture(e.pointerId);
      } catch (_) {
        /* ignore */
      }
      e.preventDefault();
      e.stopPropagation();
    });

    document.addEventListener("pointermove", (e) => {
      if (!resizeState || e.pointerId !== resizeState.pointerId) return;
      const layer = $("#windows-layer") || $("#desktop");
      const scale = resizeState.scale || 1;
      // clientWidth is in the same CSS-px space as offsetWidth under document zoom
      const deskW = layer ? layer.clientWidth : window.innerWidth;
      const deskH = layer ? layer.clientHeight : window.innerHeight;
      const minW = 320;
      const minH = 180;
      let nextW = resizeState.origW + (e.clientX - resizeState.startX) / scale;
      let nextH = resizeState.origH + (e.clientY - resizeState.startY) / scale;
      nextW = Math.max(minW, Math.min(nextW, deskW - resizeState.origLeft - 8));
      nextH = Math.max(minH, Math.min(nextH, deskH - resizeState.origTop - 8));
      resizeState.win.style.width = Math.round(nextW) + "px";
      resizeState.win.style.height = Math.round(nextH) + "px";
    });

    const endResize = (e) => {
      if (!resizeState) return;
      if (e && e.pointerId != null && e.pointerId !== resizeState.pointerId) return;
      try {
        if (resizeState.handle && resizeState.pointerId != null) {
          resizeState.handle.releasePointerCapture(resizeState.pointerId);
        }
      } catch (_) {
        /* ignore */
      }
      resizeState.win.classList.remove("resizing");
      resizeState = null;
      syncDesktopScrollExtent();
    };

    document.addEventListener("pointerup", endResize);
    document.addEventListener("pointercancel", endResize);

    window.addEventListener("blur", () => {
      if (!resizeState) return;
      resizeState.win.classList.remove("resizing");
      resizeState = null;
    });
  }

  function renderTaskbar() {
    const host = $("#taskbar-windows");
    if (!host) return;
    host.innerHTML = "";
    const titles = {
      form: "Creation Studio",
      viewer: state.active ? "Viewer — " + creationTitle(state.active) : "Viewer",
      library: "Archives",
      control: "Control Panel",
      "image-edit": "Image Edit",
      "video-edit": "Video Edit",
    };
    ["form", "viewer", "library", "control", "image-edit", "video-edit"].forEach((id) => {
      if (!state.open[id]) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "task-btn" + (state.focused === id && !state.minimized[id] ? " active" : "");
      btn.textContent = titles[id];
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (state.minimized[id]) {
          state.minimized[id] = false;
          const win = document.getElementById("win-" + id);
          if (win) win.classList.remove("minimized");
        }
        focusWindow(id);
        toggleStartMenu(false);
      });
      host.appendChild(btn);
    });
  }

  function tickClock() {
    const el = $("#taskbar-clock");
    if (!el) return;
    const d = new Date();
    el.textContent = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // ── Document render ────────────────────────────────────────────────
  function resolveTheme(creation) {
    const t = (creation && creation.theme) || {};
    return {
      themeName: t.themeName || "Authentic Era Box Art Palette",
      bgColor: t.bgColor || "#0055aa",
      cardBg: t.cardBg || "#ffffff",
      textColor: t.textColor || "#000000",
      accentColor: t.accentColor || "#ffaa00",
      headerBg: t.headerBg || "#0055aa",
      fontStyle: t.fontStyle || "retro-sans",
      boxArtStyle: t.boxArtStyle || "",
    };
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatCreatedAt(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return String(iso).slice(0, 10);
      return d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch (_) {
      return String(iso).slice(0, 10);
    }
  }

  function stopSpeech() {
    if ("speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (_) {
        /* ignore */
      }
    }
    state.speechPlaying = false;
    const btn = $("#btn-voice");
    if (btn) {
      btn.textContent = "Voice Reader";
      btn.classList.remove("speaking");
    }
  }

  function toggleVoiceReader() {
    if (!state.active) return;
    if (!("speechSynthesis" in window)) {
      showToast("Speech synthesis is not supported in this WebView");
      return;
    }
    if (state.speechPlaying) {
      stopSpeech();
      beep(400, 0.05);
      return;
    }
    const c = state.active;
    const parts = [
      c.game + " for " + c.platform + ".",
      c.creationType + ".",
      c.overview || "",
    ];
    (c.sections || []).forEach((s) => {
      parts.push((s.title || "") + ". " + (s.content || ""));
    });
    const utterance = new SpeechSynthesisUtterance(parts.join(" "));
    utterance.rate = 0.95;
    utterance.pitch = 0.9;
    utterance.onend = () => stopSpeech();
    utterance.onerror = () => stopSpeech();
    window.speechSynthesis.speak(utterance);
    state.speechPlaying = true;
    const btn = $("#btn-voice");
    if (btn) {
      btn.textContent = "Stop Reading";
      btn.classList.add("speaking");
    }
    beep(700, 0.04);
  }

  function setViewerTab(tab) {
    state.viewerTab = tab || "doc";
    document.querySelectorAll(".viewer-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === state.viewerTab);
    });
    if (state.active) renderDocument(state.active);
  }

  function overviewIsTruncatedBody(creation) {
    const overview = String(creation.overview || "").trim();
    if (!overview) return true;
    const sections = creation.sections || [];
    if (!sections.length) return false;
    const body = String(sections[0].content || "").trim();
    if (!body) return false;
    const clipped = overview.replace(/…\s*$/u, "").replace(/\.\.\.\s*$/, "").trim();
    if (!clipped) return true;
    // Freeform Text creations used to store overview = body[:500] + "…"
    if (body.startsWith(clipped) || clipped === body.slice(0, clipped.length)) {
      return true;
    }
    if (
      (creation.creationType || "") === "Text" &&
      body.length > overview.length &&
      body.indexOf(clipped.slice(0, Math.min(60, clipped.length))) === 0
    ) {
      return true;
    }
    return false;
  }

  /** Hide empty or legacy "Response" section titles from display/export. */
  function shouldHideSectionHeading(secTitle) {
    const t = String(secTitle || "").trim();
    return !t || /^response$/i.test(t);
  }

  function renderDocTab(creation, theme) {
    const meta = creation.meta || {};
    const title = creationTitle(creation);
    let html = "";
    html +=
      '<div class="doc-header" style="background:' +
      escapeHtml(theme.headerBg || "#000080") +
      ';color:#fff;padding:8px 10px;margin:-12px -12px 12px;">';
    html += "<h2>" + escapeHtml(title) + "</h2>";
    html +=
      "<div>" +
      escapeHtml(creation.creationType || "Text") +
      (creation.platform && creation.platform !== "General"
        ? " — " + escapeHtml(creation.platform)
        : "") +
      "</div></div>";

    if (creation.prompt) {
      html +=
        '<p class="doc-prompt"><strong>Prompt:</strong> ' +
        escapeHtml(creation.prompt) +
        "</p>";
    }

    html += '<div class="doc-meta">';
    [
      ["Year", meta.releaseYear],
      ["Developer", meta.developer],
      ["Publisher", meta.publisher],
      ["Designer", meta.designer],
      ["Genre", meta.genre],
      ["Media", meta.mediaFormat],
      ["Hardware", meta.systemRequirements],
    ].forEach(([label, val]) => {
      if (!val) return;
      html +=
        "<div><strong>" +
        escapeHtml(label) +
        ":</strong> " +
        escapeHtml(val) +
        "</div>";
    });
    html += "</div>";

    const overview = String(creation.overview || "").trim();
    if (overview && !overviewIsTruncatedBody(creation)) {
      html += '<p class="doc-overview">' + escapeHtml(overview) + "</p>";
    }

    (creation.sections || []).forEach((sec) => {
      const secTitle = String(sec.title || "").trim();
      html += '<div class="doc-section">';
      if (!shouldHideSectionHeading(secTitle)) {
        html +=
          '<h3 style="color:' +
          escapeHtml(theme.accentColor || "#000080") +
          '">' +
          escapeHtml(secTitle) +
          "</h3>";
      }
      html +=
        '<div class="doc-section-body">' +
        escapeHtml(sec.content || "") +
        "</div>";
      if (sec.keyValues && sec.keyValues.length) {
        html += '<table class="kv-table"><tbody>';
        sec.keyValues.forEach((kv) => {
          html +=
            "<tr><td>" +
            escapeHtml(kv.label) +
            "</td><td>" +
            escapeHtml(kv.value) +
            "</td></tr>";
        });
        html += "</tbody></table>";
      }
      html += "</div>";
    });

    if (creation.accuracyNote) {
      html +=
        '<p class="doc-export-hide" style="margin-top:16px;font-size:11px;opacity:0.85"><em>' +
        escapeHtml(creation.accuracyNote) +
        "</em></p>";
    }
    return html;
  }

  function renderMediaPlaceholder(creation, modality) {
    return (
      '<div class="media-pane media-pane-loading">' +
      "<p>Loading " +
      escapeHtml(modality) +
      "…</p>" +
      (creation.prompt
        ? '<p class="muted">' + escapeHtml(creation.prompt) + "</p>"
        : "") +
      "</div>"
    );
  }

  async function loadMediaIntoCanvas(creation) {
    const canvas = $("#doc-canvas");
    if (!canvas || !creation) return;
    const a = api();
    const modality = creationModality(creation);
    if (!a) {
      canvas.innerHTML =
        '<p class="muted">Python bridge required to display media.</p>';
      return;
    }
    try {
      const res = await a.get_media_payload(creation);
      if (!res || !res.ok) {
        canvas.innerHTML =
          '<p class="muted">' +
          escapeHtml((res && res.error) || "Media not found") +
          "</p>";
        return;
      }
      if (modality === "video" || res.modality === "video") {
        const src = res.fileUrl || res.dataUrl || "";
        if (!src) {
          canvas.innerHTML =
            '<p class="muted">Video URL missing — restart the app and try again.</p>';
          return;
        }
        canvas.innerHTML =
          '<div class="media-pane">' +
          '<video class="media-video" controls playsinline preload="metadata" src="' +
          escapeHtml(src) +
          '">' +
          "Your WebView could not play this video." +
          "</video>" +
          (creation.prompt
            ? '<p class="media-caption">' + escapeHtml(creation.prompt) + "</p>"
            : "") +
          "</div>";
        const vid = canvas.querySelector("video.media-video");
        if (vid) {
          vid.addEventListener("error", () => {
            const err = vid.error;
            const detail = err
              ? " (code " + err.code + ")"
              : "";
            showToast("Video failed to load" + detail + ". Try Save MP4… or restart the app.");
          });
        }
      } else {
        const src = res.fileUrl || res.dataUrl || "";
        if (!src) {
          canvas.innerHTML =
            '<p class="muted">Image URL missing — restart the app and try again.</p>';
          return;
        }
        canvas.innerHTML =
          '<div class="media-pane">' +
          '<img class="media-image" alt="' +
          escapeHtml(creationTitle(creation)) +
          '" src="' +
          escapeHtml(src) +
          '" />' +
          (creation.prompt
            ? '<p class="media-caption">' + escapeHtml(creation.prompt) + "</p>"
            : "") +
          "</div>";
      }
    } catch (err) {
      canvas.innerHTML =
        '<p class="muted">Failed to load media: ' + escapeHtml(String(err)) + "</p>";
    }
  }

  function renderGroundingTab(creation) {
    const sources = creation.groundingSources || [];
    let html =
      '<div class="sources-intro"><strong>Search grounding &amp; cross-check</strong><br/>' +
      "Citations recorded when Google Search grounding was used during generation." +
      "</div>";
    if (!sources.length) {
      html +=
        '<p class="muted">No grounding sources on this document. Enable Google Search grounding in Control Panel and regenerate, or import a document that includes sources.</p>';
      return html;
    }
    html += '<p><strong>Verified archival web citations:</strong></p><ul class="sources-list">';
    sources.forEach((src, idx) => {
      const title = src.title || src.url || "Source " + (idx + 1);
      const url = src.url || "";
      html += "<li><span>[" + (idx + 1) + "]</span> ";
      if (url) {
        html +=
          '<a href="' +
          escapeHtml(url) +
          '" target="_blank" rel="noreferrer">' +
          escapeHtml(title) +
          "</a>";
        html += '<span class="sources-url">' + escapeHtml(url) + "</span>";
      } else {
        html += escapeHtml(title);
      }
      html += "</li>";
    });
    html += "</ul>";
    return html;
  }

  function getExtractedText(creation) {
    if (!creation || !creation.meta) return "";
    return String(creation.meta.extractedText || "").trim();
  }

  function renderExtractedTab(creation) {
    const text = getExtractedText(creation);
    const meta = (creation && creation.meta) || {};
    const kind = String(meta.extractionKind || "").toLowerCase();
    const label = kind === "transcript" ? "Transcript" : "Extracted text";
    const modality = creationModality(creation);
    let html = '<div class="extracted-pane">';
    html += '<div class="extracted-intro"><strong>' + escapeHtml(label) + "</strong>";
    if (meta.extractedAt || meta.extractionModel) {
      html +=
        '<span class="extracted-meta">' +
        escapeHtml(
          [meta.extractionProvider, meta.extractionModel, meta.extractedAt]
            .filter(Boolean)
            .join(" · ")
        ) +
        "</span>";
    }
    html += "</div>";
    if (!text) {
      html +=
        '<p class="muted">' +
        (modality === "video"
          ? "No transcript yet. Click <strong>Transcribe…</strong> to pull speech (or on-screen text) from this video."
          : "No text extracted yet. Click <strong>Extract Text…</strong> to OCR this image.") +
        "</p>";
    } else {
      html +=
        '<textarea class="extracted-text" readonly>' +
        escapeHtml(text) +
        "</textarea>";
      html +=
        '<div class="extracted-actions">' +
        '<button type="button" id="btn-copy-extracted">Copy</button>' +
        "</div>";
    }
    html += "</div>";
    return html;
  }

  function renderPrintTab(creation) {
    const meta = creation.meta || {};
    let html = '<div class="print-layout">';
    html += '<div class="print-header">';
    html += "<h2>" + escapeHtml(creation.game) + "</h2>";
    html +=
      "<p><strong>QUICK REFERENCE · " +
      escapeHtml((creation.platform || "").toUpperCase()) +
      "</strong></p>";
    html +=
      "<p>Published by " +
      escapeHtml(meta.publisher || "Publisher") +
      " (" +
      escapeHtml(meta.releaseYear || "N/A") +
      ") · " +
      escapeHtml(meta.systemRequirements || creation.platform || "") +
      "</p></div>";
    html += '<div class="print-grid">';
    (creation.sections || []).forEach((sec) => {
      html += '<div class="print-card">';
      const secTitle = String(sec.title || "").trim();
      if (!shouldHideSectionHeading(secTitle)) {
        html += "<h3>" + escapeHtml(secTitle) + "</h3>";
      }
      html += "<p>" + escapeHtml(sec.content || "") + "</p>";
      (sec.keyValues || []).forEach((kv) => {
        html +=
          '<div class="print-kv"><span>' +
          escapeHtml(kv.label) +
          "</span><span>" +
          escapeHtml(kv.value) +
          "</span></div>";
      });
      html += "</div>";
    });
    html += "</div>";
    html +=
      '<div class="print-footer">Fold or print on cardstock to place next to your keyboard or console.</div>';
    html += "</div>";
    return html;
  }

  function renderDocument(creation) {
    state.active = creation;
    const canvas = $("#doc-canvas");
    const groundingTab = $("#tab-grounding");

    if (!creation) {
      stopSpeech();
      canvas.classList.remove("tab-ascii");
      canvas.style.background = "";
      canvas.style.color = "";
      canvas.style.fontFamily = "";
      canvas.innerHTML =
        '<p class="muted">Open a creation from Archives or generate a new one.</p>';
      $("#viewer-title").textContent = "Viewer";
      $("#viewer-status").textContent = "No creation loaded";
      if (groundingTab) groundingTab.textContent = "Sources (0)";
      syncViewerChrome(null);
      renderTaskbar();
      return;
    }

    syncViewerChrome(creation);
    const modality = creationModality(creation);
    const theme = resolveTheme(creation);
    const sources = creation.groundingSources || [];
    if (groundingTab) groundingTab.textContent = "Sources (" + sources.length + ")";

    const title = creationTitle(creation);
    $("#viewer-title").textContent = "Viewer — " + title;
    const model = (creation._model && creation._model.repo_id) || "model";
    const created = formatCreatedAt(creation.createdAt);
    $("#viewer-status").textContent =
      (creation.creationType || modality) +
      " · " +
      modality +
      " · " +
      model +
      (created ? " · " + created : "");

    const tab = state.viewerTab || (modality === "text" ? "doc" : "media");
    canvas.classList.toggle("tab-ascii", tab === "ascii");

    if (modality === "image" || modality === "video") {
      canvas.style.background = "#111";
      canvas.style.color = "#eee";
      canvas.style.fontFamily = FONT_STACKS.sans;
      if (tab === "extracted") {
        canvas.style.background = "#ffffff";
        canvas.style.color = "#000000";
        canvas.style.fontFamily = FONT_STACKS.mono;
        canvas.innerHTML = renderExtractedTab(creation);
      } else if (tab === "grounding") {
        canvas.style.background = "#ffffff";
        canvas.style.color = "#000000";
        canvas.style.fontFamily = FONT_STACKS.mono;
        canvas.innerHTML = renderGroundingTab(creation);
      } else {
        canvas.innerHTML = renderMediaPlaceholder(creation, modality);
        loadMediaIntoCanvas(creation);
      }
    } else if (tab === "ascii") {
      canvas.style.background = "#000";
      canvas.style.color = "#00ff66";
      canvas.style.fontFamily = FONT_STACKS.mono;
      canvas.innerHTML =
        '<textarea class="ascii-pane" readonly>' +
        escapeHtml(creationToAscii(creation)) +
        "</textarea>";
    } else if (tab === "grounding") {
      canvas.style.background = "#ffffff";
      canvas.style.color = "#000000";
      canvas.style.fontFamily = FONT_STACKS.mono;
      canvas.innerHTML = renderGroundingTab(creation);
    } else if (tab === "print") {
      canvas.style.background = "#ffffff";
      canvas.style.color = "#000000";
      canvas.style.fontFamily = FONT_STACKS.mono;
      canvas.innerHTML = renderPrintTab(creation);
    } else {
      canvas.style.background = theme.cardBg || "#fff";
      canvas.style.color = theme.textColor || "#000";
      canvas.style.fontFamily = fontStackFromStyle(theme.fontStyle);
      canvas.innerHTML = renderDocTab(creation, theme);
    }

    openWindow("viewer");
  }

  function creationToAscii(c) {
    if (!c) return "";
    const lines = [];
    const overview = String(c.overview || "").trim();
    if (overview && !overviewIsTruncatedBody(c)) {
      lines.push(overview);
      lines.push("");
    }
    (c.sections || []).forEach((s) => {
      const secTitle = String(s.title || "").trim();
      if (!shouldHideSectionHeading(secTitle)) {
        lines.push(secTitle);
        lines.push("");
      }
      if (s.content) lines.push(s.content);
      lines.push("");
      if (s.keyValues && s.keyValues.length) {
        s.keyValues.forEach((kv) => {
          lines.push("  * " + (kv.label || "") + " : " + (kv.value || ""));
        });
        lines.push("");
      }
    });
    return lines.join("\n").replace(/\n+$/, "\n");
  }

  function exportCreationMetadata(creation) {
    if (!creation) return {};
    const model = Object.assign({}, creation._model || {});
    const meta = {
      id: creation.id || null,
      title: creationTitle(creation),
      creationType: creation.creationType || null,
      modality: creationModality(creation),
      platform: creation.platform || null,
      createdAt: creation.createdAt || null,
      prompt: creation.prompt || "",
      model: model,
      overview: creation.overview || "",
      sections: creation.sections || [],
      meta: creation.meta || {},
      groundingSources: creation.groundingSources || [],
      accuracyNote: creation.accuracyNote || "",
    };
    if (creation.mediaPath) meta.mediaPath = creation.mediaPath;
    if (creation.mimeType) meta.mimeType = creation.mimeType;
    if (creation.theme) meta.theme = creation.theme;
    return meta;
  }

  function exportBaseName(creation) {
    return creationTitle(creation)
      .replace(/[^\w\-]+/g, "_")
      .replace(/_+/g, "_")
      .slice(0, 60) || "creation";
  }

  function buildTextExportBodyHtml(creation, theme) {
    let html = "";
    const overview = String(creation.overview || "").trim();
    if (overview && !overviewIsTruncatedBody(creation)) {
      html +=
        '<p class="doc-overview" style="margin:0 0 12px;white-space:pre-wrap;">' +
        escapeHtml(overview) +
        "</p>";
    }
    (creation.sections || []).forEach((sec) => {
      const secTitle = String(sec.title || "").trim();
      html += '<div class="doc-section" style="margin:0 0 16px;">';
      if (!shouldHideSectionHeading(secTitle)) {
        html +=
          '<h3 style="margin:0 0 8px;color:' +
          escapeHtml(theme.accentColor || "#000080") +
          '">' +
          escapeHtml(secTitle) +
          "</h3>";
      }
      html +=
        '<div class="doc-section-body" style="white-space:pre-wrap;word-wrap:break-word;line-height:1.35;margin:0;">' +
        escapeHtml(sec.content || "") +
        "</div>";
      if (sec.keyValues && sec.keyValues.length) {
        html += '<table class="kv-table" style="margin-top:8px;"><tbody>';
        sec.keyValues.forEach((kv) => {
          html +=
            "<tr><td>" +
            escapeHtml(kv.label) +
            "</td><td>" +
            escapeHtml(kv.value) +
            "</td></tr>";
        });
        html += "</tbody></table>";
      }
      html += "</div>";
    });
    return html || '<p style="margin:0;">(empty)</p>';
  }

  async function withOffscreenTextExport(creation, fn) {
    if (!window.htmlToImage) {
      throw new Error("html-to-image is unavailable");
    }
    const theme = resolveTheme(creation);
    const host = document.createElement("div");
    host.setAttribute("data-export-host", "1");
    // Keep in the layout tree (not far off-screen) so WebView paints full height.
    host.style.cssText = [
      "position:fixed",
      "left:0",
      "top:0",
      "width:800px",
      "max-width:800px",
      "padding:24px",
      "box-sizing:border-box",
      "margin:0",
      "overflow:visible",
      "max-height:none",
      "height:auto",
      "opacity:0",
      "pointer-events:none",
      "z-index:2147483646",
      "background:" + (theme.cardBg || "#ffffff"),
      "color:" + (theme.textColor || "#000000"),
      "font-family:" + fontStackFromStyle(theme.fontStyle),
      "font-size:14px",
      "line-height:1.35",
    ].join(";");
    host.innerHTML = buildTextExportBodyHtml(creation, theme);
    document.body.appendChild(host);

    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve))
    );

    const fullWidth = Math.max(host.scrollWidth, host.offsetWidth, 800);
    const fullHeight = Math.max(host.scrollHeight, host.offsetHeight, 1);
    host.style.width = fullWidth + "px";
    host.style.height = fullHeight + "px";

    await new Promise((resolve) => requestAnimationFrame(resolve));

    // Stay under typical canvas dimension limits (~16384px) for long documents
    const maxDim = 16000;
    let pixelRatio = 2;
    if (fullWidth * pixelRatio > maxDim || fullHeight * pixelRatio > maxDim) {
      pixelRatio = Math.max(
        1,
        Math.min(maxDim / fullWidth, maxDim / fullHeight)
      );
    }

    const opts = {
      pixelRatio: pixelRatio,
      cacheBust: true,
      backgroundColor: theme.cardBg || "#ffffff",
      width: fullWidth,
      height: fullHeight,
      style: {
        opacity: "1",
        position: "static",
        left: "auto",
        top: "auto",
        transform: "none",
        maxHeight: "none",
        overflow: "visible",
        height: fullHeight + "px",
        width: fullWidth + "px",
      },
    };

    try {
      return await fn(host, opts);
    } finally {
      if (host.parentNode) host.parentNode.removeChild(host);
    }
  }

  async function exportDocumentImage(format) {
    if (!state.active) return;
    const a = api();
    if (!a) return;
    const modality = creationModality(state.active);

    // Native image → PNG: copy original bytes; PDF: embed image full-bleed
    if (modality === "image") {
      try {
        const payload = await a.get_media_payload(state.active);
        if (!payload || !payload.ok || !payload.dataUrl) {
          showToast((payload && payload.error) || "Image not found");
          return;
        }
        const base = exportBaseName(state.active);
        if (format === "png") {
          const res = await a.save_binary_file_dialog(base + ".png", payload.dataUrl);
          if (res.ok) {
            showToast("Saved PNG");
            beep(900, 0.05);
          } else if (!res.cancelled) {
            showToast(res.error || "PNG export failed");
          }
          return;
        }
        showToast("Building PDF…");
        const jspdfNS = window.jspdf || window.jsPDF;
        const JsPDF = jspdfNS && (jspdfNS.jsPDF || jspdfNS);
        if (!JsPDF) throw new Error("jsPDF is unavailable");
        const img = new Image();
        await new Promise((resolve, reject) => {
          img.onload = resolve;
          img.onerror = reject;
          img.src = payload.dataUrl;
        });
        const pdf = new JsPDF({
          orientation: img.width > img.height ? "landscape" : "portrait",
          unit: "px",
          format: [img.width, img.height],
        });
        const fmt = (payload.mimeType || "").includes("jpeg") ? "JPEG" : "PNG";
        pdf.addImage(payload.dataUrl, fmt, 0, 0, img.width, img.height);
        const dataUri = pdf.output("datauristring");
        const res = await a.save_binary_file_dialog(base + ".pdf", dataUri);
        if (res.ok) {
          showToast("Saved PDF");
          beep(900, 0.05);
        } else if (!res.cancelled) {
          showToast(res.error || "PDF export failed");
        }
      } catch (err) {
        console.error(err);
        showToast("Export failed: " + (err && err.message ? err.message : err));
      }
      return;
    }

    // Text: render full body offscreen so parent window overflow cannot clip it
    showToast(format === "pdf" ? "Building PDF…" : "Capturing PNG…");
    try {
      const base = exportBaseName(state.active);
      if (format === "png") {
        const pngDataUrl = await withOffscreenTextExport(state.active, (el, opts) =>
          window.htmlToImage.toPng(el, opts)
        );
        const res = await a.save_binary_file_dialog(base + ".png", pngDataUrl);
        if (res.ok) {
          showToast("Saved PNG");
          beep(900, 0.05);
        } else if (!res.cancelled) {
          showToast(res.error || "PNG export failed");
        }
        return;
      }

      const jspdfNS = window.jspdf || window.jsPDF;
      const JsPDF = jspdfNS && (jspdfNS.jsPDF || jspdfNS);
      if (!JsPDF) throw new Error("jsPDF is unavailable");

      const canvas = await withOffscreenTextExport(state.active, (el, opts) =>
        window.htmlToImage.toCanvas(el, opts)
      );
      const imgData = canvas.toDataURL("image/png");
      const pdf = new JsPDF({
        orientation: canvas.width > canvas.height ? "landscape" : "portrait",
        unit: "px",
        format: [canvas.width / 2, canvas.height / 2],
      });
      pdf.addImage(imgData, "PNG", 0, 0, canvas.width / 2, canvas.height / 2);
      const dataUri = pdf.output("datauristring");
      const res = await a.save_binary_file_dialog(base + ".pdf", dataUri);
      if (res.ok) {
        showToast("Saved PDF");
        beep(900, 0.05);
      } else if (!res.cancelled) {
        showToast(res.error || "PDF export failed");
      }
    } catch (err) {
      console.error(err);
      showToast("Export failed: " + (err && err.message ? err.message : err));
    }
  }

  function creationModalityLabel(creation) {
    const m = creationModality(creation);
    if (m === "image") return "Image";
    if (m === "video") return "Video";
    return "Text";
  }

  function archiveSortValue(creation, key) {
    if (key === "name") return creationTitle(creation).toLowerCase();
    if (key === "type") return creationModalityLabel(creation).toLowerCase();
    if (key === "created") {
      const t = Date.parse(creation && creation.createdAt);
      return Number.isFinite(t) ? t : 0;
    }
    return "";
  }

  function compareArchiveRows(a, b, key, dir) {
    const av = archiveSortValue(a, key);
    const bv = archiveSortValue(b, key);
    let cmp = 0;
    if (typeof av === "number" && typeof bv === "number") {
      cmp = av - bv;
    } else {
      cmp = String(av).localeCompare(String(bv), undefined, {
        sensitivity: "base",
        numeric: true,
      });
    }
    if (cmp === 0) {
      // Stable-ish secondary: newest id / created
      const at = archiveSortValue(a, "created");
      const bt = archiveSortValue(b, "created");
      cmp = bt - at;
    }
    return dir === "desc" ? -cmp : cmp;
  }

  function syncArchiveSortHeaders() {
    const sort = state.archiveSort || { key: "created", dir: "desc" };
    document.querySelectorAll(".archive-table thead th[aria-sort]").forEach((th) => {
      const btn = th.querySelector(".arch-sort-btn");
      const key = btn && btn.getAttribute("data-sort");
      if (!key) return;
      const label =
        key === "name" ? "Name" : key === "type" ? "Type" : "Created";
      if (sort.key === key) {
        th.setAttribute("aria-sort", sort.dir === "asc" ? "ascending" : "descending");
        btn.textContent = label + (sort.dir === "asc" ? " ▲" : " ▼");
        btn.setAttribute("aria-pressed", "true");
      } else {
        th.setAttribute("aria-sort", "none");
        btn.textContent = label;
        btn.setAttribute("aria-pressed", "false");
      }
    });
  }

  function setArchiveSort(key) {
    if (!key) return;
    const cur = state.archiveSort || { key: "created", dir: "desc" };
    if (cur.key === key) {
      state.archiveSort = { key: key, dir: cur.dir === "asc" ? "desc" : "asc" };
    } else {
      // Dates default newest-first; text columns start A→Z
      state.archiveSort = {
        key: key,
        dir: key === "created" ? "desc" : "asc",
      };
    }
    renderArchives();
    beep(650, 0.02);
  }

  function renderArchives() {
    const q = ($("#archive-search").value || "").toLowerCase();
    const list = $("#archive-list");
    if (!list) return;
    list.innerHTML = "";
    const sort = state.archiveSort || { key: "created", dir: "desc" };
    syncArchiveSortHeaders();
    state.creations
      .filter((c) => {
        if (!q) return true;
        const typeLabel = creationModalityLabel(c).toLowerCase();
        return (
          (c.game || "").toLowerCase().includes(q) ||
          (c.title || "").toLowerCase().includes(q) ||
          (c.prompt || "").toLowerCase().includes(q) ||
          (c.creationType || "").toLowerCase().includes(q) ||
          (c.platform || "").toLowerCase().includes(q) ||
          typeLabel.includes(q) ||
          creationModality(c).includes(q)
        );
      })
      .slice()
      .sort((a, b) => compareArchiveRows(a, b, sort.key, sort.dir))
      .forEach((c) => {
        const tr = document.createElement("tr");
        const mod = creationModality(c);
        const isMedia = mod === "image" || mod === "video";

        const tdName = document.createElement("td");
        tdName.className = "arch-col-name";
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.className = "arch-open";
        openBtn.textContent = creationTitle(c);
        openBtn.title = "Open in Viewer";
        openBtn.addEventListener("click", () => {
          renderDocument(c);
          beep(700, 0.04);
        });
        tdName.appendChild(openBtn);

        const tdType = document.createElement("td");
        tdType.className = "arch-col-type";
        tdType.textContent = creationModalityLabel(c);

        const tdDate = document.createElement("td");
        tdDate.className = "arch-col-date";
        tdDate.textContent = c.createdAt ? formatCreatedAt(c.createdAt) : "—";

        const tdActions = document.createElement("td");
        tdActions.className = "arch-col-actions";
        const basis = document.createElement("button");
        basis.type = "button";
        basis.textContent = isMedia ? "Edit…" : "Basis";
        basis.title = isMedia
          ? "Open a copy in the " + mod + " editor"
          : "Use as basis for a new text creation";
        basis.addEventListener("click", () => {
          useCreationAsBasis(c);
        });
        const del = document.createElement("button");
        del.type = "button";
        del.textContent = "Del";
        del.addEventListener("click", async () => {
          const a = api();
          if (!a) return;
          state.creations = await a.delete_creation(c.id);
          if (state.active && state.active.id === c.id) {
            renderDocument(null);
          }
          renderArchives();
          beep(300, 0.08);
        });
        tdActions.appendChild(basis);
        tdActions.appendChild(del);

        tr.appendChild(tdName);
        tr.appendChild(tdType);
        tr.appendChild(tdDate);
        tr.appendChild(tdActions);
        list.appendChild(tr);
      });
  }

  function syncBackendPanels() {
    const provider = ($("#backend-provider") && $("#backend-provider").value) || "gemini";
    const gemini = $("#gemini-settings");
    const openrouter = $("#openrouter-settings");
    const hf = $("#hf-settings");
    if (gemini) gemini.hidden = provider !== "gemini";
    if (openrouter) openrouter.hidden = provider !== "openrouter";
    if (hf) hf.hidden = provider !== "huggingface";
    syncGeminiTwoPassAvailability();
  }

  function syncGeminiTwoPassAvailability() {
    const search = $("#gemini-search");
    const twoPass = $("#gemini-two-pass");
    const hint = $("#gemini-two-pass-hint");
    if (!twoPass) return;
    const searchOn = !search || search.checked;
    twoPass.disabled = !searchOn;
    if (hint) {
      hint.classList.toggle("muted", !searchOn);
    }
  }

  function modelOptionLabel(m, maxLen) {
    // Short labels only — OpenRouter "name" fields can be paragraph-length and
    // native <select> in WebView2 sizes to the longest option text.
    maxLen = maxLen == null ? 44 : maxLen;
    const label = String((m && m.label) || (m && m.repo_id) || "").trim();
    let text = label || "model";
    // If the API stuffed a description after an em dash / hyphen, keep the title part
    const cut = text.search(/\s[—–-]\s/);
    if (cut > 12 && cut < maxLen) text = text.slice(0, cut);
    if (text.length > maxLen) text = text.slice(0, maxLen - 1) + "…";
    return text;
  }

  function modelOptionTitle(m) {
    const parts = [
      (m && m.label) || "",
      (m && m.notes) || "",
      (m && m.repo_id) || "",
    ]
      .map((s) => String(s || "").trim())
      .filter(Boolean);
    return parts.filter((p, i) => p !== parts[i - 1]).join("\n");
  }

  function appendModelOption(sel, m, modality) {
    const opt = document.createElement("option");
    opt.value = m.repo_id;
    opt.textContent = modelOptionLabel(m);
    opt.title = modelOptionTitle(m);
    if (modality) opt.dataset.modality = modality;
    sel.appendChild(opt);
    return opt;
  }

  function fillModelSelect(sel, selected, suggestions) {
    if (!sel) return;
    const list = suggestions || [];
    sel.innerHTML = "";
    const groups = { text: [], image: [], video: [], other: [] };
    list.forEach((m) => {
      const mod = (m.modality || "text").toLowerCase();
      if (groups[mod]) groups[mod].push(m);
      else groups.other.push(m);
    });
    const labels = {
      text: "Text",
      image: "Image",
      video: "Video",
      other: "Other",
    };
    ["text", "image", "video", "other"].forEach((key) => {
      const items = groups[key];
      if (!items.length) return;
      const og = document.createElement("optgroup");
      og.label = labels[key];
      items.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.repo_id;
        opt.textContent = modelOptionLabel(m);
        opt.title = modelOptionTitle(m);
        opt.dataset.modality = m.modality || key;
        og.appendChild(opt);
      });
      sel.appendChild(og);
    });
    if (selected && ![...sel.options].some((o) => o.value === selected)) {
      const opt = document.createElement("option");
      opt.value = selected;
      opt.textContent = modelOptionLabel({ label: selected, repo_id: selected });
      opt.title = selected;
      sel.appendChild(opt);
    }
    if (list.length || sel.options.length) {
      sel.value = selected;
    }
  }

  /** Fill a Gemini modality picker with only compatible models. */
  function fillGeminiModalitySelect(sel, selected, suggestions, modality) {
    if (!sel) return;
    const want = (modality || "text").toLowerCase();
    const defaults = {
      text: "gemini-2.5-flash",
      image: "gemini-2.5-flash-image",
      video: "veo-2.0-generate-001",
    };
    const filtered = (suggestions || []).filter(
      (m) => (m.modality || "text").toLowerCase() === want
    );
    sel.innerHTML = "";
    filtered.forEach((m) => appendModelOption(sel, m, want));
    let pick = selected || defaults[want] || "";
    if (pick && ![...sel.options].some((o) => o.value === pick)) {
      appendModelOption(
        sel,
        { repo_id: pick, label: pick, notes: "saved" },
        want
      );
    }
    if (!pick && sel.options.length) pick = sel.options[0].value;
    if (pick) sel.value = pick;
  }

  /** Fill an OpenRouter modality picker with only compatible models. */
  function fillOpenRouterModalitySelect(sel, selected, suggestions, modality) {
    if (!sel) return;
    const want = (modality || "text").toLowerCase();
    const defaults = {
      text: "google/gemini-2.5-flash",
      image: "google/gemini-2.5-flash-image",
      video: "google/veo-2.0",
    };
    const filtered = (suggestions || []).filter(
      (m) => (m.modality || "text").toLowerCase() === want
    );
    sel.innerHTML = "";
    filtered.forEach((m) => appendModelOption(sel, m, want));
    let pick = selected || defaults[want] || "";
    if (pick && ![...sel.options].some((o) => o.value === pick)) {
      appendModelOption(
        sel,
        { repo_id: pick, label: pick, notes: "saved" },
        want
      );
    }
    if (!pick && sel.options.length) pick = sel.options[0].value;
    if (pick) sel.value = pick;
  }

  /** Fill a Hugging Face modality picker with only compatible models. */
  function fillHfModalitySelect(sel, selected, suggestions, modality) {
    if (!sel) return;
    const want = (modality || "text").toLowerCase();
    const defaults = {
      text: "microsoft/Phi-3.5-mini-instruct",
      image: "stable-diffusion-v1-5/stable-diffusion-v1-5",
      video: "ali-vilab/text-to-video-ms-1.7b",
    };
    const filtered = (suggestions || []).filter(
      (m) => (m.modality || "text").toLowerCase() === want
    );
    sel.innerHTML = "";
    filtered.forEach((m) => appendModelOption(sel, m, want));
    let pick = selected || defaults[want] || "";
    if (pick && ![...sel.options].some((o) => o.value === pick)) {
      appendModelOption(
        sel,
        { repo_id: pick, label: pick, notes: "saved" },
        want
      );
    }
    if (!pick && sel.options.length) pick = sel.options[0].value;
    if (pick) sel.value = pick;
  }

  function creationModality(creation) {
    if (!creation) return "text";
    const m = String(creation.modality || "").toLowerCase();
    if (m === "image" || m === "video" || m === "text") return m;
    if (creation.mediaPath) {
      const mime = String(creation.mimeType || "").toLowerCase();
      if (mime.startsWith("video/")) return "video";
      return "image";
    }
    return "text";
  }

  function creationTitle(creation) {
    if (!creation) return "Untitled";
    return (
      creation.title ||
      creation.game ||
      (creation.prompt && String(creation.prompt).split("\n")[0].trim()) ||
      "Untitled"
    );
  }

  function syncViewerChrome(creation) {
    const modality = creation ? creationModality(creation) : "";
    const isMedia = modality === "image" || modality === "video";
    const extracted = getExtractedText(creation);

    const tabDoc = $("#tab-doc");
    const tabMedia = $("#tab-media");
    const tabExtracted = $("#tab-extracted");
    const tabGrounding = $("#tab-grounding");
    const tabPrint = $("#tab-print");
    const tabAscii = $("#tab-ascii");
    if (tabDoc) tabDoc.hidden = isMedia;
    if (tabMedia) {
      tabMedia.hidden = !isMedia;
      tabMedia.textContent = modality === "video" ? "Video" : "Image";
    }
    if (tabExtracted) {
      tabExtracted.hidden = !isMedia;
      const kind =
        creation &&
        creation.meta &&
        String(creation.meta.extractionKind || "").toLowerCase();
      tabExtracted.textContent =
        kind === "transcript" ? "Transcript" : "Extracted";
    }
    if (tabPrint) tabPrint.hidden = isMedia || !creation;
    if (tabAscii) tabAscii.hidden = isMedia || !creation;
    if (tabGrounding) {
      const sources = (creation && creation.groundingSources) || [];
      tabGrounding.hidden = !creation || (isMedia && !sources.length);
    }

    const showTxt = modality === "text" || (isMedia && !!extracted);
    const showPng = modality === "text" || modality === "image";
    const showPdf = modality === "text" || modality === "image";
    const showMp4 = modality === "video";
    const showAscii = modality === "text";
    const showVoice = modality === "text";
    const showEditImage = modality === "image";
    const showEditVideo = modality === "video";
    const showExtract = isMedia;
    const showMetadata = !!creation;

    if ($("#btn-export-txt")) {
      $("#btn-export-txt").hidden = !showTxt;
      $("#btn-export-txt").textContent =
        isMedia && extracted ? "Export Extracted TXT" : "Export TXT";
    }
    if ($("#btn-export-png")) {
      $("#btn-export-png").hidden = !showPng;
      $("#btn-export-png").textContent =
        modality === "image" ? "Save PNG" : "Export PNG";
    }
    if ($("#btn-export-pdf")) {
      $("#btn-export-pdf").hidden = !showPdf;
      $("#btn-export-pdf").textContent =
        modality === "image" ? "Save PDF" : "Export PDF";
    }
    if ($("#btn-export-media")) {
      // Video native file only — images use Save PNG / Save PDF
      $("#btn-export-media").hidden = !showMp4;
      $("#btn-export-media").textContent = "Save MP4…";
    }
    if ($("#btn-extract-text")) {
      $("#btn-extract-text").hidden = !showExtract;
      $("#btn-extract-text").textContent = extracted
        ? "Re-extract Text…"
        : modality === "video"
          ? "Transcribe…"
          : "Extract Text…";
    }
    if ($("#btn-edit-image")) $("#btn-edit-image").hidden = !showEditImage;
    if ($("#btn-edit-video")) $("#btn-edit-video").hidden = !showEditVideo;
    if ($("#btn-copy-ascii")) $("#btn-copy-ascii").hidden = !showAscii;
    if ($("#btn-voice")) $("#btn-voice").hidden = !showVoice;
    if ($("#btn-export-json")) {
      $("#btn-export-json").hidden = !showMetadata;
      $("#btn-export-json").textContent = "Export Metadata";
    }

    if (isMedia && (state.viewerTab === "doc" || state.viewerTab === "print" || state.viewerTab === "ascii")) {
      state.viewerTab = "media";
    }
    if (!isMedia && (state.viewerTab === "media" || state.viewerTab === "extracted")) {
      state.viewerTab = "doc";
    }
  }

  function fillControlPanel(boot) {
    if (boot && boot.config) state.config = boot.config;
    const model = (boot.config && boot.config.huggingface) || {};
    const gemini = (boot.config && boot.config.gemini) || {};
    const openrouter = (boot.config && boot.config.openrouter) || {};
    const backend = (boot.config && boot.config.backend) || {};
    const ui = (boot.config && boot.config.ui) || {};
    const promptCfg = (boot.config && boot.config.prompt) || {};

    if ($("#backend-provider")) {
      $("#backend-provider").value = backend.provider || "gemini";
    }

    if ($("#gemini-temp")) {
      $("#gemini-temp").value = gemini.temperature ?? 0;
    }
    if ($("#gemini-search")) {
      $("#gemini-search").checked = gemini.google_search !== false;
    }
    if ($("#gemini-two-pass")) {
      $("#gemini-two-pass").checked = gemini.two_pass_verify !== false;
    }
    syncGeminiTwoPassAvailability();

    const suggested = boot.suggestedGeminiModels || [];
    fillGeminiModalitySelect(
      $("#gemini-text-model"),
      gemini.text_model || "gemini-2.5-flash",
      suggested,
      "text"
    );
    fillGeminiModalitySelect(
      $("#gemini-image-model"),
      gemini.image_model || "gemini-2.5-flash-image",
      suggested,
      "image"
    );
    fillGeminiModalitySelect(
      $("#gemini-video-model"),
      gemini.video_model || "veo-2.0-generate-001",
      suggested,
      "video"
    );

    if ($("#openrouter-temp")) {
      $("#openrouter-temp").value = openrouter.temperature ?? 0;
    }
    const orSuggested =
      state.suggestedOpenRouterModels || boot.suggestedOpenRouterModels || [];
    fillOpenRouterModalitySelect(
      $("#openrouter-text-model"),
      openrouter.text_model || "google/gemini-2.5-flash",
      orSuggested,
      "text"
    );
    fillOpenRouterModalitySelect(
      $("#openrouter-image-model"),
      openrouter.image_model || "google/gemini-2.5-flash-image",
      orSuggested,
      "image"
    );
    fillOpenRouterModalitySelect(
      $("#openrouter-video-model"),
      openrouter.video_model || "google/veo-2.0",
      orSuggested,
      "video"
    );

    updateApiKeyIndicators();

    const hfSuggested =
      state.suggestedHfModels || boot.suggestedModels || [];
    fillHfModalitySelect(
      $("#hf-text-model"),
      model.text_model || model.repo_id || "microsoft/Phi-3.5-mini-instruct",
      hfSuggested,
      "text"
    );
    fillHfModalitySelect(
      $("#hf-image-model"),
      model.image_model || "stable-diffusion-v1-5/stable-diffusion-v1-5",
      hfSuggested,
      "image"
    );
    fillHfModalitySelect(
      $("#hf-video-model"),
      model.video_model || "ali-vilab/text-to-video-ms-1.7b",
      hfSuggested,
      "video"
    );
    if ($("#model-device")) $("#model-device").value = model.device || "auto";
    if ($("#model-dtype")) $("#model-dtype").value = model.torch_dtype || "auto";
    if ($("#model-tokens")) $("#model-tokens").value = model.max_new_tokens || 2048;
    if ($("#model-temp")) $("#model-temp").value = model.temperature ?? 0;
    if ($("#model-token")) $("#model-token").value = model.hf_token || "";
    if ($("#system-extra")) $("#system-extra").value = promptCfg.extra_instructions || "";
    $("#opt-sound").checked = ui.sound_enabled !== false;
    $("#opt-crt").checked = !!ui.crt_enabled;
    state.soundEnabled = $("#opt-sound").checked;
    state.crtEnabled = $("#opt-crt").checked;
    $("#crt-overlay").hidden = !state.crtEnabled;
    applyUiScale(ui.ui_scale != null ? ui.ui_scale : 1);
    if ($("#ui-scale")) {
      const scaleVal = String(state.uiScale);
      const sel = $("#ui-scale");
      if (![...sel.options].some((o) => o.value === scaleVal)) {
        const opt = document.createElement("option");
        opt.value = scaleVal;
        opt.textContent = Math.round(state.uiScale * 100) + "%";
        sel.appendChild(opt);
      }
      sel.value = scaleVal;
    }

    fillAppThemeSelect();
    fillUiFontSelect();
    const custom = ui.custom_theme || {};
    state.customTheme = {
      desktopColor: normalizeHexColor(custom.desktop_color, "#008080"),
      windowColor: normalizeHexColor(custom.window_color, "#c0c0c0"),
      titleColor: normalizeHexColor(custom.title_color, "#000080"),
      textColor: normalizeHexColor(custom.text_color, "#222222"),
      font: resolveCustomFontKey(custom.font || "sans"),
    };
    writeCustomThemeToControls(state.customTheme);
    state.uiFont = resolveUiFontKey(
      ui.ui_font || (custom.font === "serif" || custom.font === "mono" ? custom.font : null) || "inter"
    );
    applyUiFont(state.uiFont);
    state.appTheme = resolveAppThemeKey(ui.app_theme || "light");
    if ($("#app-theme")) {
      $("#app-theme").value = state.appTheme;
    }
    applyAppTheme(state.appTheme);
    // Sync theme/status only — don't overwrite studio fields mid-session
    applyGameDefaults({ applyPlatform: false, applyTheme: true });

    syncBackendPanels();
    updateStudioBackendLabel(boot);
  }

  function updateStudioBackendLabel(boot) {
    const modelField = $("#studio-model-field");
    if (!modelField) return;
    const provider =
      (boot && boot.config && boot.config.backend && boot.config.backend.provider) ||
      ($("#backend-provider") && $("#backend-provider").value) ||
      "gemini";
    if (provider === "huggingface") {
      const h =
        (boot && boot.config && boot.config.huggingface) ||
        (state.config && state.config.huggingface) ||
        {};
      const textM =
        h.text_model ||
        h.repo_id ||
        ($("#hf-text-model") && $("#hf-text-model").value) ||
        "local HF";
      const imageM =
        h.image_model ||
        ($("#hf-image-model") && $("#hf-image-model").value) ||
        "";
      const videoM =
        h.video_model ||
        ($("#hf-video-model") && $("#hf-video-model").value) ||
        "";
      modelField.textContent =
        "Backend: Hugging Face · text " +
        textM +
        " · image " +
        imageM +
        " · video " +
        videoM;
    } else if (provider === "openrouter") {
      const o =
        (boot && boot.config && boot.config.openrouter) ||
        (state.config && state.config.openrouter) ||
        {};
      const textM =
        o.text_model ||
        ($("#openrouter-text-model") && $("#openrouter-text-model").value) ||
        "google/gemini-2.5-flash";
      const imageM =
        o.image_model ||
        ($("#openrouter-image-model") && $("#openrouter-image-model").value) ||
        "google/gemini-2.5-flash-image";
      const videoM =
        o.video_model ||
        ($("#openrouter-video-model") && $("#openrouter-video-model").value) ||
        "google/veo-2.0";
      modelField.textContent =
        "Backend: OpenRouter · text " +
        textM +
        " · image " +
        imageM +
        " · video " +
        videoM;
    } else {
      const g =
        (boot && boot.config && boot.config.gemini) ||
        (state.config && state.config.gemini) ||
        {};
      const textM =
        g.text_model ||
        ($("#gemini-text-model") && $("#gemini-text-model").value) ||
        "gemini-2.5-flash";
      const imageM =
        g.image_model ||
        ($("#gemini-image-model") && $("#gemini-image-model").value) ||
        "gemini-2.5-flash-image";
      const videoM =
        g.video_model ||
        ($("#gemini-video-model") && $("#gemini-video-model").value) ||
        "veo-2.0-generate-001";
      modelField.textContent =
        "Backend: Gemini · text " +
        textM +
        " · image " +
        imageM +
        " · video " +
        videoM;
    }
  }

  function savedBackendProvider() {
    return (
      (state.config &&
        state.config.backend &&
        state.config.backend.provider) ||
      "gemini"
    );
  }

  function providerLabel(provider) {
    if (provider === "openrouter") return "OpenRouter";
    if (provider === "huggingface") return "Hugging Face";
    return "Gemini";
  }

  function updateApiKeyIndicators() {
    const selected =
      ($("#backend-provider") && $("#backend-provider").value) || "gemini";
    const saved = savedBackendProvider();
    const providerChanged = selected !== saved;

    const geminiSet = !!(
      state.config &&
      state.config.gemini &&
      state.config.gemini.api_key_set
    );
    const openrouterSet = !!(
      state.config &&
      state.config.openrouter &&
      state.config.openrouter.api_key_set
    );

    const geminiBadge = $("#gemini-key-badge");
    const geminiStatus = $("#gemini-key-status");
    const geminiInput = $("#gemini-key");
    if (geminiBadge) {
      geminiBadge.textContent = geminiSet ? "Saved" : "Not set";
      geminiBadge.classList.toggle("key-badge-set", geminiSet);
      geminiBadge.classList.toggle("key-badge-missing", !geminiSet);
    }
    if (geminiInput) {
      geminiInput.placeholder = geminiSet
        ? "Leave blank to keep saved key"
        : "Paste Gemini API key";
    }
    if (geminiStatus) {
      if (geminiSet) {
        geminiStatus.textContent =
          selected === "gemini" && providerChanged
            ? "A Gemini API key is already saved — Save to switch providers (leave blank to keep it)."
            : "A Gemini API key is already saved. Leave the field blank to keep it.";
      } else if (selected === "gemini" && providerChanged) {
        geminiStatus.textContent =
          "Provider changed — paste a Gemini API key before saving.";
      } else {
        geminiStatus.textContent = "No Gemini API key saved yet.";
      }
    }

    const orBadge = $("#openrouter-key-badge");
    const orStatus = $("#openrouter-key-status");
    const orInput = $("#openrouter-key");
    if (orBadge) {
      orBadge.textContent = openrouterSet ? "Saved" : "Not set";
      orBadge.classList.toggle("key-badge-set", openrouterSet);
      orBadge.classList.toggle("key-badge-missing", !openrouterSet);
    }
    if (orInput) {
      orInput.placeholder = openrouterSet
        ? "Leave blank to keep saved key"
        : "Paste OpenRouter API key";
    }
    if (orStatus) {
      if (openrouterSet) {
        orStatus.textContent =
          selected === "openrouter" && providerChanged
            ? "An OpenRouter API key is already saved — Save to switch providers (leave blank to keep it)."
            : "An OpenRouter API key is already saved. Leave the field blank to keep it.";
      } else if (selected === "openrouter" && providerChanged) {
        orStatus.textContent =
          "Provider changed — paste an OpenRouter API key before saving.";
      } else {
        orStatus.textContent = "No OpenRouter API key saved yet.";
      }
    }
  }

  function providerApiKeyReady(provider) {
    if (provider === "huggingface") return true;

    const typed =
      provider === "openrouter"
        ? (($("#openrouter-key") && $("#openrouter-key").value.trim()) || "")
        : (($("#gemini-key") && $("#gemini-key").value.trim()) || "");

    if (typed) return true;
    if (provider === "openrouter") {
      return !!(
        state.config &&
        state.config.openrouter &&
        state.config.openrouter.api_key_set
      );
    }
    return !!(state.config && state.config.gemini && state.config.gemini.api_key_set);
  }

  function ensureApiKeyBeforeSave() {
    const provider =
      ($("#backend-provider") && $("#backend-provider").value) || "gemini";
    if (providerApiKeyReady(provider)) return true;

    const changed = provider !== savedBackendProvider();
    const label = providerLabel(provider);
    showToast(
      changed
        ? "Paste a " + label + " API key before switching providers."
        : "Paste a " + label + " API key before saving."
    );
    if (provider === "openrouter" && $("#openrouter-key")) {
      $("#openrouter-key").focus();
    } else if (provider === "gemini" && $("#gemini-key")) {
      $("#gemini-key").focus();
    }
    return false;
  }

  function currentGeminiUiConfig() {
    const text =
      ($("#gemini-text-model") && $("#gemini-text-model").value) ||
      "gemini-2.5-flash";
    return {
      text_model: text,
      image_model:
        ($("#gemini-image-model") && $("#gemini-image-model").value) ||
        "gemini-2.5-flash-image",
      video_model:
        ($("#gemini-video-model") && $("#gemini-video-model").value) ||
        "veo-2.0-generate-001",
    };
  }

  function currentOpenRouterUiConfig() {
    const text =
      ($("#openrouter-text-model") && $("#openrouter-text-model").value) ||
      "google/gemini-2.5-flash";
    return {
      text_model: text,
      image_model:
        ($("#openrouter-image-model") && $("#openrouter-image-model").value) ||
        "google/gemini-2.5-flash-image",
      video_model:
        ($("#openrouter-video-model") && $("#openrouter-video-model").value) ||
        "google/veo-2.0",
    };
  }

  function currentHfUiConfig() {
    const text =
      ($("#hf-text-model") && $("#hf-text-model").value) ||
      "microsoft/Phi-3.5-mini-instruct";
    return {
      text_model: text,
      repo_id: text,
      image_model:
        ($("#hf-image-model") && $("#hf-image-model").value) ||
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
      video_model:
        ($("#hf-video-model") && $("#hf-video-model").value) ||
        "ali-vilab/text-to-video-ms-1.7b",
    };
  }

  function collectSettings(reload) {
    const provider = ($("#backend-provider") && $("#backend-provider").value) || "gemini";
    const hfText =
      ($("#hf-text-model") && $("#hf-text-model").value.trim()) ||
      "microsoft/Phi-3.5-mini-instruct";
    return {
      reload_model: !!reload,
      backend: { provider: provider },
      gemini: {
        text_model:
          ($("#gemini-text-model") && $("#gemini-text-model").value.trim()) ||
          "gemini-2.5-flash",
        image_model:
          ($("#gemini-image-model") && $("#gemini-image-model").value.trim()) ||
          "gemini-2.5-flash-image",
        video_model:
          ($("#gemini-video-model") && $("#gemini-video-model").value.trim()) ||
          "veo-2.0-generate-001",
        api_key: ($("#gemini-key") && $("#gemini-key").value.trim()) || "",
        google_search: $("#gemini-search") ? $("#gemini-search").checked : true,
        two_pass_verify: $("#gemini-two-pass") ? $("#gemini-two-pass").checked : true,
        temperature: $("#gemini-temp") ? Number($("#gemini-temp").value) || 0 : 0,
      },
      openrouter: {
        text_model:
          ($("#openrouter-text-model") && $("#openrouter-text-model").value.trim()) ||
          "google/gemini-2.5-flash",
        image_model:
          ($("#openrouter-image-model") && $("#openrouter-image-model").value.trim()) ||
          "google/gemini-2.5-flash-image",
        video_model:
          ($("#openrouter-video-model") && $("#openrouter-video-model").value.trim()) ||
          "google/veo-2.0",
        api_key: ($("#openrouter-key") && $("#openrouter-key").value.trim()) || "",
        temperature: $("#openrouter-temp")
          ? Number($("#openrouter-temp").value) || 0
          : 0,
      },
      huggingface: {
        text_model: hfText,
        repo_id: hfText,
        image_model:
          ($("#hf-image-model") && $("#hf-image-model").value.trim()) ||
          "stable-diffusion-v1-5/stable-diffusion-v1-5",
        video_model:
          ($("#hf-video-model") && $("#hf-video-model").value.trim()) ||
          "ali-vilab/text-to-video-ms-1.7b",
        device: ($("#model-device") && $("#model-device").value) || "auto",
        torch_dtype: ($("#model-dtype") && $("#model-dtype").value) || "auto",
        max_new_tokens: ($("#model-tokens") && Number($("#model-tokens").value)) || 2048,
        temperature: ($("#model-temp") && Number($("#model-temp").value)) || 0,
        hf_token: ($("#model-token") && $("#model-token").value.trim()) || null,
        trust_remote_code: false,
      },
      prompt: {
        extra_instructions: ($("#system-extra") && $("#system-extra").value) || "",
      },
      ui: {
        sound_enabled: $("#opt-sound").checked,
        crt_enabled: $("#opt-crt").checked,
        ui_scale: readUiScaleFromControl(),
        ui_font:
          ($("#ui-font") && $("#ui-font").value) || state.uiFont || "inter",
        app_theme: ($("#app-theme") && $("#app-theme").value) || state.appTheme || "light",
        custom_theme: (function () {
          const c =
            (($("#app-theme") && $("#app-theme").value) || state.appTheme) === "custom"
              ? readCustomThemeFromControls()
              : state.customTheme;
          return {
            desktop_color: c.desktopColor,
            window_color: c.windowColor,
            title_color: c.titleColor,
            text_color: c.textColor,
            font: c.font || "sans",
          };
        })(),
      },
    };
  }

  function readUiScaleFromControl() {
    const raw = $("#ui-scale") ? Number($("#ui-scale").value) : state.uiScale || 1;
    if (!Number.isFinite(raw)) return 1;
    return Math.min(2, Math.max(0.75, raw));
  }

  function applyUiScale(scale) {
    const s = Number(scale);
    const clamped = Number.isFinite(s) ? Math.min(2, Math.max(0.75, s)) : 1;
    state.uiScale = clamped;
    // Chromium / WebView2 zoom scales fonts, chrome, and layout together
    document.documentElement.style.zoom = String(clamped);
    const label = $("#ui-scale-label");
    if (label) label.textContent = Math.round(clamped * 100) + "%";
    requestAnimationFrame(() => syncDesktopScrollExtent());
  }

  function setControlTab(tab) {
    const allowed = { ai: true, display: true };
    state.controlTab = allowed[tab] ? tab : "ai";
    document.querySelectorAll('.control-tabs [role="tab"]').forEach((tabEl) => {
      const selected =
        tabEl.getAttribute("data-control-tab") === state.controlTab;
      tabEl.setAttribute("aria-selected", selected ? "true" : "false");
    });
    document.querySelectorAll(".control-pane").forEach((pane) => {
      const id = pane.getAttribute("data-control-pane");
      pane.hidden = id !== state.controlTab;
    });
    syncControlPanelWidth();
    requestAnimationFrame(() => syncDesktopScrollExtent());
  }

  function syncControlPanelWidth() {
    const win = $("#win-control");
    if (!win) return;
    const ai = state.controlTab !== "display";
    win.classList.toggle("control-tab-ai", ai);
    win.classList.toggle("control-tab-display", !ai);
    // Keep inline style in sync so open/drag layout matches CSS
    win.style.width = ai ? "820px" : "560px";
    // Drop any leftover resize height so the panel sizes to content / max-height
    win.style.height = "";
    win.style.maxHeight = "";
    win.style.maxWidth = "";
  }

  function applyDisplaySettingsFromControls() {
    state.soundEnabled = $("#opt-sound").checked;
    state.crtEnabled = $("#opt-crt").checked;
    $("#crt-overlay").hidden = !state.crtEnabled;
    applyUiScale(readUiScaleFromControl());
    applyUiFont(
      ($("#ui-font") && $("#ui-font").value) || state.uiFont || "inter"
    );
    const themeKey =
      ($("#app-theme") && $("#app-theme").value) || state.appTheme || "light";
    applyAppTheme(themeKey);
  }

  function fillAppThemeSelect() {
    const dst = $("#app-theme");
    if (!dst) return;
    const prev = resolveAppThemeKey(dst.value || state.appTheme || "light");
    dst.innerHTML = "";
    [
      ["light", "Light Mode (Day)"],
      ["dark", "Dark Mode (Night)"],
      ["custom", "Customize…"],
    ].forEach(([value, label]) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = label;
      dst.appendChild(opt);
    });
    dst.value = prev;
    writeCustomThemeToControls(state.customTheme);
    syncCustomThemeControlsVisibility();
  }

  function themeDisplayName(themeKey) {
    if (!themeKey || themeKey === "auto") return "Auto Box Art Palette";
    if (THEMES[themeKey] && THEMES[themeKey].themeName) return THEMES[themeKey].themeName;
    return themeKey;
  }

  function updateStudioThemeField() {
    const el = $("#studio-theme-field");
    if (!el) return;
    el.textContent = "Theme Engine: " + themeDisplayName("auto");
  }

  function applyGameDefaults(_opts) {
    updateStudioThemeField();
  }

  function applyCreationPlaceholders(template, game, platform) {
    let text = String(template || "").replace(/\r\n/g, "\n");
    const g = String(game || "").trim();
    const p = String(platform || "").trim();
    if (g) text = text.replace(/\[GAME\]/gi, g);
    if (p) text = text.replace(/\[PLATFORM\]/gi, p);
    return text;
  }

  function syncCreationDescription() {
    // Prompt is user-authored; no auto-fill from catalogs.
  }

  function getCreationDescription() {
    return getStudioPrompt();
  }

  function fillCatalogs(boot) {
    const creationTypes =
      (boot && boot.creationTypes) ||
      (window.RGC_CATALOG && window.RGC_CATALOG.creationTypes) ||
      [];
    const presets =
      (boot && boot.presets) ||
      (window.RGC_CATALOG && window.RGC_CATALOG.presets) ||
      [];
    state.presets = presets;
    state.creationTypes = creationTypes;
  }

  window.__onProgress = function (payload) {
    let message = "";
    let percent = undefined;
    let title = null;
    let phase = "";
    if (payload && typeof payload === "object") {
      message = payload.message || payload.detail || "";
      if (payload.percent != null) percent = payload.percent;
      if (payload.title) title = payload.title;
      phase = String(payload.phase || "");
    } else {
      message = String(payload || "");
    }

    // Keep create vs model-download framing distinct even when generation
    // briefly downloads/loads a local model first.
    if (busy.activity === "generate") {
      if (phase === "download") {
        title = "Creating…";
        if (message && !/^preparing model/i.test(message)) {
          message = "Preparing model — " + message;
        }
      } else if (phase === "load") {
        title = "Creating…";
        if (message && !/^loading model/i.test(message)) {
          message = "Loading model — " + message;
        }
      } else if (title) {
        // Keep provider titles like "Generating image"
      } else if (phase === "generate") {
        title = "Creating…";
      } else {
        title = title || busy.title || "Creating…";
      }
    } else if (busy.activity === "preload") {
      if (phase === "download") title = title || "Downloading models";
      else if (phase === "load") title = title || "Loading models";
      else if (phase === "ready") title = title || "Models ready";
      else title = title || busy.title || "Downloading models";
    } else {
      if (phase === "download") title = title || "Downloading model";
      if (phase === "load") title = title || "Loading model";
      if (phase === "generate") title = title || "Creating…";
    }

    updateBusy(message, percent, title);
  };

  function applyGenerationResult(creation) {
    if (!creation) return;
    // Idempotent — poll and evaluate_js may both fire
    if (state._lastHandledId === creation.id) return;
    state._lastHandledId = creation.id;

    state.generating = false;
    setCreateBlocked(false);
    endBusy("Ready");
    if (state.studioBasis) clearStudioBasis();
    state.creations = [creation].concat(
      state.creations.filter((c) => c.id !== creation.id)
    );
    renderArchives();
    renderDocument(creation);
    openWindow("viewer");
    focusWindow("viewer");
    beep(880, 0.08, "triangle");
    beep(1175, 0.1, "triangle");
  }

  function applyGenerationError(err) {
    state.generating = false;
    setCreateBlocked(false);
    endBusy("Ready");
    showToast(String(err));
    beep(200, 0.2, "sawtooth");
  }

  function applyGenerationCancelled() {
    state.generating = false;
    setCreateBlocked(false);
    endBusy("Ready");
    showToast("Generation cancelled");
    beep(320, 0.08, "triangle");
  }

  function applyExtractResult(creation) {
    if (!creation) {
      endBusy();
      return;
    }
    endBusy("Ready");
    state.creations = [creation].concat(
      state.creations.filter((c) => c.id !== creation.id)
    );
    renderArchives();
    state.viewerTab = "extracted";
    renderDocument(creation);
    openWindow("viewer");
    focusWindow("viewer");
    const kind =
      creation.meta && String(creation.meta.extractionKind || "").toLowerCase();
    showToast(
      kind === "transcript" ? "Transcript ready." : "Extracted text ready."
    );
    beep(880, 0.08, "triangle");
  }

  async function extractCreationText() {
    if (!state.active) return;
    const modality = creationModality(state.active);
    if (modality !== "image" && modality !== "video") {
      showToast("Extract Text is for images and videos.");
      return;
    }
    if (state.generating || state.modelLoading) {
      showToast("Wait for the current AI job to finish.");
      return;
    }
    const a = api();
    if (!a) {
      showToast("Python bridge not ready.");
      return;
    }
    const title = modality === "video" ? "Transcribing…" : "Extracting text…";
    beginBusy(title, "Starting…", {
      delayMs: 0,
      cancellable: true,
      activity: "other",
      hint:
        modality === "video"
          ? "Pulling speech from the video via your text model. This can take a minute."
          : "Reading text from the image via your text model.",
    });
    try {
      const res = await a.extract_creation_text(state.active.id);
      if (!res || !res.ok) {
        endBusy();
        showToast((res && res.error) || "Could not start Extract Text.");
        return;
      }
      busy.jobId = res.job_id;
      await pollJob(res.job_id, "extract");
    } catch (err) {
      endBusy();
      showToast(String(err));
    }
  }

  async function requestCancelBusyJob() {
    if (!busy.cancellable || busy.cancelling) return;
    const jobId = busy.jobId;
    if (!jobId) {
      showToast("Nothing to cancel yet.");
      return;
    }
    const a = api();
    if (!a || typeof a.cancel_job !== "function") {
      showToast("Cancel is not available.");
      return;
    }
    busy.cancelling = true;
    setBusyCancelVisible(true);
    updateBusy("Cancelling…");
    try {
      const res = await a.cancel_job(jobId);
      if (!res || !res.ok) {
        busy.cancelling = false;
        setBusyCancelVisible(true);
        showToast((res && res.error) || "Could not cancel");
        return;
      }
      updateBusy("Cancelling — waiting for the current step to stop…");
    } catch (err) {
      busy.cancelling = false;
      setBusyCancelVisible(true);
      showToast("Cancel failed: " + err);
    }
  }

  let _choiceHandledKey = "";

  async function applyNeedsChoice(payload) {
    if (!payload || payload.kind !== "ambiguous") return;
    const candidates = Array.isArray(payload.candidates) ? payload.candidates : [];
    const key =
      String(payload.query || "") +
      "|" +
      candidates.map((c) => (c && c.game) || "").join("|");
    if (_choiceHandledKey === key) return;
    _choiceHandledKey = key;

    state.generating = false;
    setCreateBlocked(false);
    endBusy("Ready");

    if (candidates.length < 2) {
      showToast('Game Not Found — could not disambiguate "' + (payload.query || "") + '".');
      beep(200, 0.2, "sawtooth");
      return;
    }

    beep(660, 0.06, "triangle");
    const picked = await showSearchResults(payload.query, candidates);
    if (!picked || !picked.game) {
      showToast("Cancelled — pick a game from Search Results when ready.");
      return;
    }

    const gameInput = $("#studio-prompt");
    if (gameInput && picked.game && !gameInput.value.trim()) {
      gameInput.value = picked.game;
    }

    await startGeneration({
      exactTitle: true,
      game: picked.game,
      platform: picked.platform || "General",
    });
  }

  /**
   * Poll Python get_job until done/error/needs_choice. This is the reliable completion path
   * on Windows WebView2 where evaluate_js from worker threads often fails.
   */
  async function pollJob(jobId, kind) {
    const a = api();
    if (!a || !jobId) return;
    const started = Date.now();
    const maxMs = 60 * 60 * 1000;

    while (Date.now() - started < maxMs) {
      let job;
      try {
        job = await a.get_job(jobId);
      } catch (err) {
        if (kind === "preload") {
          finishModelDownload(false, "Lost connection to Python bridge: " + err);
        } else if (kind === "extract") {
          endBusy();
          showToast("Lost connection to Python bridge: " + err);
        } else {
          applyGenerationError("Lost connection to Python bridge: " + err);
        }
        return;
      }

      if (!job) {
        await sleep(500);
        continue;
      }

      if (job.progress) {
        window.__onProgress(job.progress);
      }

      if (job.status === "done") {
        if (kind === "generate") {
          applyGenerationResult(job.result);
        } else if (kind === "preload") {
          finishModelDownload(true);
        } else if (kind === "extract") {
          applyExtractResult(job.result);
        }
        return;
      }

      if (job.status === "needs_choice") {
        if (kind === "generate") {
          await applyNeedsChoice(job.result);
        }
        return;
      }

      if (job.status === "cancelled") {
        if (kind === "generate") {
          applyGenerationCancelled();
        } else if (kind === "extract") {
          endBusy();
          showToast("Extract Text cancelled.");
        } else {
          finishModelDownload(false, "Cancelled");
        }
        return;
      }

      if (job.status === "cancelling") {
        updateBusy("Cancelling…");
      }

      if (job.status === "error" || job.status === "missing") {
        if (kind === "generate") {
          applyGenerationError(job.error || "Generation failed");
        } else if (kind === "extract") {
          endBusy();
          showToast(job.error || "Extract Text failed");
        } else {
          finishModelDownload(false, job.error || "Model load failed");
        }
        return;
      }

      await sleep(500);
    }

    if (kind === "generate") {
      applyGenerationError("Timed out waiting for generation.");
    } else if (kind === "extract") {
      endBusy();
      showToast("Timed out waiting for Extract Text.");
    } else {
      finishModelDownload(false, "Timed out waiting for model load.");
    }
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  let startGenerationLock = false;

  function applyModalityMismatch(res) {
    const msg =
      (res && res.error) ||
      "This prompt needs Google Gemini (image/video). Switch provider in Control Panel.";
    showToast(msg, 14000);
    setProgress("Stopped — switch provider");
    beep(200, 0.2, "sawtooth");
    openWindow("control");
    if ($("#backend-provider") && $("#backend-provider").value !== "gemini") {
      // Leave provider panel visible — user should switch to Gemini
    }
  }

  async function startGeneration(opts) {
    const exactTitle = !!(opts && opts.exactTitle);
    if (startGenerationLock || state.generating) {
      showToast("A generation is already running…");
      return;
    }
    if (state.modelLoading) {
      showToast("Wait for the local model download / load to finish.");
      return;
    }
    // Fresh user-initiated search may need a new Search Results dialog
    if (!exactTitle) _choiceHandledKey = "";
    startGenerationLock = true;

    try {
      const a = api();
      if (!a) {
        showToast("Python bridge not ready. Launch via: python -m retro_98_ai_creator");
        return;
      }

      const prompt = getStudioPrompt().trim();
      if (!prompt) {
        showToast("Enter a prompt to create.");
        return;
      }

      const basisId =
        (state.studioBasis && state.studioBasis.creationId) || "";
      // With a media basis, force that modality in the preflight prompt hint
      const compatPrompt = basisId
        ? state.studioBasis.modality === "video"
          ? "Generate a video: " + prompt
          : "Create an image: " + prompt
        : prompt;

      // Preflight: image/video prompts on text models (and reverse) stop here
      try {
        if (typeof a.check_modality_match === "function") {
          const compat = await a.check_modality_match(compatPrompt);
          if (compat && compat.ok === false) {
            applyModalityMismatch(compat);
            return;
          }
        }
      } catch (_) {
        /* fall through — server create_creation still guards */
      }

      const game = ((opts && opts.game) || "Prompt").trim() || "Prompt";
      const platform =
        ((opts && opts.platform) || "General").trim() || "General";
      const creationType = "Custom";
      const creationDescription = prompt;

      state.generating = true;
      $("#btn-generate").disabled = true;
      beginBusy("Creating…", "Starting generation…", {
        delayMs: 0,
        cancellable: true,
        activity: "generate",
        hint: BUSY_HINTS.generate,
      });
      beep(400, 0.05);

      try {
        await a.ping();
      } catch (err) {
        applyGenerationError("Python bridge not responding: " + err);
        return;
      }

      let res;
      try {
        res = await a.create_creation(
          game,
          platform,
          creationType,
          true,
          creationDescription,
          basisId
        );
      } catch (err) {
        applyGenerationError(err);
        return;
      }

      if (!res || !res.ok) {
        if (res && res.modalityMismatch) {
          state.generating = false;
          setCreateBlocked(false);
          endBusy("Ready");
          applyModalityMismatch(res);
          return;
        }
        applyGenerationError((res && res.error) || "Generation failed to start");
        return;
      }
      if (!res.job_id) {
        applyGenerationError("Backend did not return a job id.");
        return;
      }
      busy.jobId = res.job_id;
      busy.cancellable = true;
      setBusyCancelVisible(true);
      updateBusy(
        exactTitle
          ? "Creating for selected title…"
          : "Generation started…",
        undefined,
        "Creating…"
      );
      pollJob(res.job_id, "generate");
    } finally {
      startGenerationLock = false;
    }
  }

  window.__onGenerationComplete = function (creation) {
    // evaluate_js best-effort path
    if (!creation) return;
    if (!state.generating && !busy.visible) {
      // Already handled via poll
      return;
    }
    applyGenerationResult(creation);
  };

  window.__onGenerateError = function (err) {
    if (!state.generating && !busy.visible) return;
    applyGenerationError(err);
  };

  window.__onGenerateCancelled = function () {
    if (!state.generating && !busy.visible) return;
    applyGenerationCancelled();
  };

  window.__onNeedsChoice = function (payload) {
    if (!state.generating && !busy.visible) return;
    applyNeedsChoice(payload);
  };

  window.__onModelStatus = async function () {
    // Don't endBusy here if a generate job is still running
    if (state.generating) return;

    // Preload finished (Python pushes this from the worker thread). Prefer
    // resolving via job status so we don't leave the busy dialog open forever
    // if pollJob was stalled.
    if (state.modelLoading) {
      const a = api();
      const jobId = state.preloadJobId;
      if (a && jobId) {
        try {
          const job = await a.get_job(jobId);
          if (job && job.status === "done") {
            finishModelDownload(true);
            return;
          }
          if (job && (job.status === "error" || job.status === "missing")) {
            finishModelDownload(false, job.error || "Model load failed");
            return;
          }
        } catch (_) {
          /* pollJob may still be running */
        }
      }
      return;
    }
    endBusy("Ready");
  };

  // ── Image Edit (ReFrame-style filters + crop + rotate) ─────────────
  const imageEdit = {
    sourceImg: null,
    creationId: null,
    standalone: true, // desktop app vs Viewer Edit (Apply)
    filters: null,
    rotation: 0,
    crop: null, // {x,y,w,h} in source pixels
    cropDrag: null,
    dirty: false,
    raf: 0,
  };

  function markImageEditDirty() {
    imageEdit.dirty = true;
  }

  function setImageEditLoadedLabel(creation) {
    const el = $("#iedit-loaded-label");
    if (!el) return;
    el.textContent = creation
      ? "Loaded: " + creationTitle(creation)
      : "No image loaded";
  }

  function syncImageEditChrome() {
    const toolbar = $("#win-image-edit .editor-app-toolbar");
    if (toolbar) toolbar.hidden = !imageEdit.standalone;
    if ($("#btn-edit-apply")) $("#btn-edit-apply").hidden = !!imageEdit.standalone;
    if ($("#btn-edit-save")) $("#btn-edit-save").hidden = !imageEdit.standalone;
    // Save As is always available once an image is loaded (Archives Apply or desktop editor)
    if ($("#btn-edit-save-as")) $("#btn-edit-save-as").hidden = false;
    const hint = $("#image-edit-hint");
    if (hint) {
      hint.textContent = imageEdit.standalone
        ? "Load an image to begin. At 0° rotation, drag to set a crop, then drag the box or handles to adjust. Save writes Archives; Save As… exports a file."
        : "At 0° rotation, drag on the image to set a crop. Drag the yellow box to move, or use the handles to resize. Clear Crop to reset. Apply saves to Archives; Save As… exports a file.";
    }
  }

  function prepareEmptyImageEditor() {
    imageEdit.sourceImg = null;
    imageEdit.creationId = null;
    imageEdit.standalone = true;
    imageEdit.crop = null;
    imageEdit.cropDrag = null;
    imageEdit.dirty = false;
    imageEdit.rotation = 0;
    if (window.R98ImageEdit) {
      imageEdit.filters = Object.assign({}, window.R98ImageEdit.DEFAULT_FILTERS);
      writeImageEditFiltersToUi(imageEdit.filters);
    }
    if ($("#edit-rotation")) $("#edit-rotation").value = 0;
    syncImageEditValueLabels();
    const canvas = $("#image-edit-canvas");
    if (canvas) {
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvas.width || 0, canvas.height || 0);
      canvas.width = 320;
      canvas.height = 200;
      if (ctx) {
        ctx.fillStyle = "#808080";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#000";
        ctx.font = "12px sans-serif";
        ctx.fillText("Load an image to begin", 16, 28);
      }
    }
    const box = $("#image-edit-crop-box");
    if (box) box.hidden = true;
    setImageEditLoadedLabel(null);
    syncImageEditChrome();
  }

  async function loadImageIntoEditorFromFile() {
    const a = api();
    if (!a) return;
    beginBusy("Loading image", "Importing into Archives…", { delayMs: 0 });
    try {
      const res = await a.import_media_file("image");
      if (!res || res.cancelled) return;
      if (!res.ok) {
        showToast(res.error || "Import failed");
        return;
      }
      rememberImportedCreation(res.creation);
      await openImageEditor(res.creation, { standalone: true });
      showToast("Image loaded into Image Edit");
    } catch (err) {
      showToast("Load failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  function readImageEditFiltersFromUi() {
    const num = (id, fallback) => {
      const el = $("#" + id);
      if (!el) return fallback;
      const n = Number(el.value);
      return Number.isFinite(n) ? n : fallback;
    };
    return {
      brightness: num("edit-brightness", 0),
      contrast: num("edit-contrast", 0),
      grayscale: !!($("#edit-grayscale") && $("#edit-grayscale").checked),
      threshold: !!($("#edit-threshold") && $("#edit-threshold").checked),
      sharpen: !!($("#edit-sharpen") && $("#edit-sharpen").checked),
      saturation: num("edit-saturation", 100),
      hueRotate: num("edit-hue", 0),
      invert: num("edit-invert", 0),
      sepia: num("edit-sepia", 0),
      blur: num("edit-blur", 0),
      exposure: num("edit-exposure", 0),
      gamma: num("edit-gamma", 1),
      vignette: num("edit-vignette", 0),
      tintRed: num("edit-tint-r", 0),
      tintGreen: num("edit-tint-g", 0),
      tintBlue: num("edit-tint-b", 0),
      bgRemove: !!($("#edit-bg-remove") && $("#edit-bg-remove").checked),
      bgRemoveTolerance: num("edit-bg-tolerance", 35),
      bgRemoveFromEdges: !!($("#edit-bg-edges") && $("#edit-bg-edges").checked),
    };
  }

  function writeImageEditFiltersToUi(filters) {
    const f = (window.R98ImageEdit && window.R98ImageEdit.normalizeFilters(filters)) || filters;
    const map = {
      "edit-brightness": f.brightness,
      "edit-contrast": f.contrast,
      "edit-saturation": f.saturation,
      "edit-hue": f.hueRotate,
      "edit-invert": f.invert,
      "edit-sepia": f.sepia,
      "edit-blur": f.blur,
      "edit-exposure": f.exposure,
      "edit-gamma": f.gamma,
      "edit-vignette": f.vignette,
      "edit-tint-r": f.tintRed,
      "edit-tint-g": f.tintGreen,
      "edit-tint-b": f.tintBlue,
      "edit-bg-tolerance": f.bgRemoveTolerance,
    };
    Object.keys(map).forEach((id) => {
      const el = $("#" + id);
      if (el) el.value = map[id];
    });
    if ($("#edit-grayscale")) $("#edit-grayscale").checked = !!f.grayscale;
    if ($("#edit-threshold")) $("#edit-threshold").checked = !!f.threshold;
    if ($("#edit-sharpen")) $("#edit-sharpen").checked = !!f.sharpen;
    if ($("#edit-bg-remove")) $("#edit-bg-remove").checked = !!f.bgRemove;
    if ($("#edit-bg-edges")) $("#edit-bg-edges").checked = !!f.bgRemoveFromEdges;
    syncImageEditValueLabels();
    syncBgRemoveRows();
  }

  function syncImageEditValueLabels() {
    document.querySelectorAll("#win-image-edit .edit-val[data-for]").forEach((el) => {
      const id = el.getAttribute("data-for");
      const input = id && $("#" + id);
      if (input) el.textContent = input.value;
    });
    if ($("#edit-rotation-label") && $("#edit-rotation")) {
      $("#edit-rotation-label").textContent = $("#edit-rotation").value + "°";
    }
  }

  function syncBgRemoveRows() {
    const on = !!($("#edit-bg-remove") && $("#edit-bg-remove").checked);
    if ($("#edit-bg-tol-row")) $("#edit-bg-tol-row").hidden = !on;
    if ($("#edit-bg-edges-row")) $("#edit-bg-edges-row").hidden = !on;
  }

  function scheduleImageEditPreview() {
    if (imageEdit.raf) cancelAnimationFrame(imageEdit.raf);
    imageEdit.raf = requestAnimationFrame(() => {
      imageEdit.raf = 0;
      renderImageEditPreview();
    });
  }

  function renderImageEditPreview() {
    const apiEdit = window.R98ImageEdit;
    const canvas = $("#image-edit-canvas");
    if (!apiEdit || !canvas || !imageEdit.sourceImg) return;
    imageEdit.filters = readImageEditFiltersFromUi();
    imageEdit.rotation = Number($("#edit-rotation") && $("#edit-rotation").value) || 0;
    // At 0° show the full filtered image so crop is drawn as an overlay.
    // When rotated, bake crop into the preview (overlay mapping is unreliable).
    const previewCrop = imageEdit.rotation ? imageEdit.crop : null;
    const out = apiEdit.renderEditedCanvas(
      imageEdit.sourceImg,
      imageEdit.filters,
      previewCrop,
      imageEdit.rotation
    );
    canvas.width = out.width;
    canvas.height = out.height;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(out, 0, 0);
    updateCropBoxOverlay();
  }

  /** Map pointer → source image pixels using the visible canvas box. */
  function imageEditClientToSourcePixels(clientX, clientY, opts) {
    opts = opts || {};
    const canvas = $("#image-edit-canvas");
    const img = imageEdit.sourceImg;
    if (!canvas || !img) return null;
    const rect = canvas.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return null;
    const sw = img.naturalWidth || img.width || canvas.width;
    const sh = img.naturalHeight || img.height || canvas.height;
    let nx = (clientX - rect.left) / rect.width;
    let ny = (clientY - rect.top) / rect.height;
    if (!opts.clamp) {
      if (nx < 0 || ny < 0 || nx > 1 || ny > 1) return null;
    } else {
      nx = Math.min(1, Math.max(0, nx));
      ny = Math.min(1, Math.max(0, ny));
    }
    return {
      x: Math.min(sw, Math.max(0, nx * sw)),
      y: Math.min(sh, Math.max(0, ny * sh)),
      sw: sw,
      sh: sh,
    };
  }

  function clampImageEditCrop(crop, sw, sh) {
    if (!crop) return null;
    let w = Math.max(1, Math.min(Number(crop.w) || 1, sw));
    let h = Math.max(1, Math.min(Number(crop.h) || 1, sh));
    let x = Number(crop.x) || 0;
    let y = Number(crop.y) || 0;
    x = Math.min(Math.max(0, x), Math.max(0, sw - w));
    y = Math.min(Math.max(0, y), Math.max(0, sh - h));
    return { x: x, y: y, w: w, h: h };
  }

  function ensureImageEditCropHandles(box) {
    if (!box || box.querySelector(".crop-handle")) return;
    ["nw", "n", "ne", "e", "se", "s", "sw", "w"].forEach((dir) => {
      const handle = document.createElement("div");
      handle.className = "crop-handle crop-handle-" + dir;
      handle.dataset.handle = dir;
      box.appendChild(handle);
    });
  }

  function updateCropBoxOverlay() {
    const box = $("#image-edit-crop-box");
    const canvas = $("#image-edit-canvas");
    if (!box || !canvas || !imageEdit.sourceImg) return;
    const crop = imageEdit.crop;
    if (!crop || imageEdit.rotation) {
      box.hidden = true;
      return;
    }
    ensureImageEditCropHandles(box);
    // Crop box is positioned inside .image-edit-canvas-wrap (same box as the canvas),
    // so percentages track CSS scaling / centering without stage scroll math.
    const sw = imageEdit.sourceImg.naturalWidth || imageEdit.sourceImg.width || canvas.width;
    const sh = imageEdit.sourceImg.naturalHeight || imageEdit.sourceImg.height || canvas.height;
    box.hidden = false;
    box.style.left = (crop.x / sw) * 100 + "%";
    box.style.top = (crop.y / sh) * 100 + "%";
    box.style.width = (crop.w / sw) * 100 + "%";
    box.style.height = (crop.h / sh) * 100 + "%";
  }

  function resizeImageEditCropFromHandle(startCrop, handle, x1, y1, sw, sh) {
    const left0 = startCrop.x;
    const top0 = startCrop.y;
    const right0 = startCrop.x + startCrop.w;
    const bottom0 = startCrop.y + startCrop.h;
    let left = left0;
    let top = top0;
    let right = right0;
    let bottom = bottom0;
    if (handle.indexOf("w") !== -1) left = x1;
    if (handle.indexOf("e") !== -1) right = x1;
    if (handle.indexOf("n") !== -1) top = y1;
    if (handle.indexOf("s") !== -1) bottom = y1;
    left = Math.min(Math.max(0, left), sw);
    right = Math.min(Math.max(0, right), sw);
    top = Math.min(Math.max(0, top), sh);
    bottom = Math.min(Math.max(0, bottom), sh);
    return clampImageEditCrop(
      {
        x: Math.min(left, right),
        y: Math.min(top, bottom),
        w: Math.max(1, Math.abs(right - left)),
        h: Math.max(1, Math.abs(bottom - top)),
      },
      sw,
      sh
    );
  }

  async function openImageEditor(creation, opts) {
    opts = opts || {};
    if (!creation || creationModality(creation) !== "image") {
      showToast("Edit is available for image creations.");
      return false;
    }
    if (!window.R98ImageEdit) {
      showToast("Image edit module failed to load.");
      return false;
    }
    const a = api();
    if (!a) {
      showToast("Python bridge required to edit images.");
      return false;
    }
    const payload = await a.get_media_payload(creation);
    if (!payload || !payload.ok || !payload.dataUrl) {
      showToast((payload && payload.error) || "Could not load image.");
      return false;
    }

    const img = new Image();
    try {
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = payload.dataUrl;
      });
    } catch (_) {
      showToast("Could not decode image for editing.");
      return false;
    }

    imageEdit.sourceImg = img;
    imageEdit.creationId = creation.id;
    imageEdit.standalone = typeof opts.standalone === "boolean" ? opts.standalone : true;
    imageEdit.crop = null;
    imageEdit.cropDrag = null;
    imageEdit.dirty = false;
    imageEdit.rotation = 0;
    imageEdit.filters = Object.assign({}, window.R98ImageEdit.DEFAULT_FILTERS);
    if ($("#edit-rotation")) $("#edit-rotation").value = 0;
    writeImageEditFiltersToUi(imageEdit.filters);
    setImageEditLoadedLabel(creation);
    syncImageEditChrome();
    openWindow("image-edit");
    // Preview after the window is shown/laid out
    requestAnimationFrame(() => scheduleImageEditPreview());
    beep(700, 0.04);
    return true;
  }

  function resetImageEditor() {
    if (!window.R98ImageEdit) return;
    imageEdit.filters = Object.assign({}, window.R98ImageEdit.DEFAULT_FILTERS);
    imageEdit.crop = null;
    imageEdit.rotation = 0;
    imageEdit.dirty = false;
    if ($("#edit-rotation")) $("#edit-rotation").value = 0;
    writeImageEditFiltersToUi(imageEdit.filters);
    scheduleImageEditPreview();
  }

  function encodeEditedImageDataUrl() {
    if (!imageEdit.sourceImg || !window.R98ImageEdit) return null;
    const filters = readImageEditFiltersFromUi();
    const rotation = Number($("#edit-rotation") && $("#edit-rotation").value) || 0;
    const out = window.R98ImageEdit.renderEditedCanvas(
      imageEdit.sourceImg,
      filters,
      imageEdit.crop,
      rotation
    );
    const needsAlpha = !!(filters && filters.bgRemove);
    const mime = needsAlpha ? "image/png" : "image/jpeg";
    const dataUrl = window.R98ImageEdit.canvasToDataUrl(out, mime);
    if (!dataUrl || dataUrl.length < 32) return null;
    return { dataUrl, mime, filters };
  }

  async function persistEditedImageToArchives() {
    if (!imageEdit.creationId) {
      showToast("No Archive item — use Load Image… first.");
      return null;
    }
    const encoded = encodeEditedImageDataUrl();
    if (!encoded) {
      showToast("Could not encode edited image.");
      return null;
    }
    const httpRes = await fetch("/api/replace-creation-media", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        creationId: imageEdit.creationId,
        dataUrl: encoded.dataUrl,
        mimeType: encoded.mime,
      }),
    });
    let res = null;
    try {
      res = await httpRes.json();
    } catch (_) {
      res = null;
    }
    if (!httpRes.ok || !res || !res.ok) {
      showToast(
        (res && res.error) ||
          "Failed to save edited image (HTTP " + httpRes.status + ")"
      );
      return null;
    }
    const saved = res.creation;
    state.creations = [saved].concat(
      state.creations.filter((c) => c.id !== saved.id)
    );
    state.active = saved;
    renderArchives();
    return saved;
  }

  async function reloadImageEditorFromCreation(creation) {
    const a = api();
    if (!a || !creation) return;
    const payload = await a.get_media_payload(creation);
    if (!payload || !payload.ok || !payload.dataUrl) {
      showToast((payload && payload.error) || "Could not reload image.");
      return;
    }
    const img = new Image();
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      img.src = payload.dataUrl;
    });
    imageEdit.sourceImg = img;
    imageEdit.creationId = creation.id;
    imageEdit.crop = null;
    imageEdit.cropDrag = null;
    imageEdit.rotation = 0;
    imageEdit.dirty = false;
    if (window.R98ImageEdit) {
      imageEdit.filters = Object.assign({}, window.R98ImageEdit.DEFAULT_FILTERS);
      writeImageEditFiltersToUi(imageEdit.filters);
    }
    if ($("#edit-rotation")) $("#edit-rotation").value = 0;
    setImageEditLoadedLabel(creation);
    syncImageEditValueLabels();
    scheduleImageEditPreview();
  }

  async function applyImageEditor() {
    if (!imageEdit.sourceImg || !window.R98ImageEdit) {
      showToast("Load an image first.");
      return;
    }
    beginBusy("Saving edit", "Applying filters and writing media…", { delayMs: 0 });
    try {
      const saved = await persistEditedImageToArchives();
      if (!saved) return;
      renderDocument(saved);
      closeImageEditor();
      showToast("Image edit applied");
      beep(900, 0.05);
    } catch (err) {
      showToast("Edit failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  async function saveImageEditor() {
    if (!imageEdit.sourceImg || !window.R98ImageEdit) {
      showToast("Load an image first.");
      return;
    }
    beginBusy("Saving image", "Writing edited image to Archives…", { delayMs: 0 });
    try {
      const saved = await persistEditedImageToArchives();
      if (!saved) return;
      await reloadImageEditorFromCreation(saved);
      showToast("Image saved");
      beep(900, 0.05);
    } catch (err) {
      showToast("Save failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  async function saveImageEditorAs() {
    if (!imageEdit.sourceImg || !window.R98ImageEdit) {
      showToast("Load an image first.");
      return;
    }
    beginBusy("Save As", "Encoding image…", { delayMs: 0 });
    try {
      const encoded = encodeEditedImageDataUrl();
      if (!encoded) {
        showToast("Could not encode edited image.");
        return;
      }
      const ext = encoded.mime === "image/png" ? ".png" : ".jpg";
      const creation =
        state.creations.find((c) => c.id === imageEdit.creationId) || state.active;
      const base = exportBaseName(creation || { title: "image" }) + ext;
      const httpRes = await fetch("/api/save-media-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          defaultName: base,
          dataUrl: encoded.dataUrl,
        }),
      });
      let res = null;
      try {
        res = await httpRes.json();
      } catch (_) {
        res = null;
      }
      if (res && res.cancelled) return;
      if (!httpRes.ok || !res || !res.ok) {
        showToast(
          (res && res.error) ||
            "Save As failed (HTTP " + httpRes.status + ")"
        );
        return;
      }
      showToast("Saved to " + (res.path || "file"));
      beep(900, 0.05);
    } catch (err) {
      showToast("Save As failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  function closeImageEditor() {
    closeWindow("image-edit");
  }

  async function requestCloseImageEditor() {
    await requestCloseWindow("image-edit");
  }

  function setupImageEditCropInteraction() {
    const stage = $("#image-edit-stage");
    const canvas = $("#image-edit-canvas");
    if (!stage || !canvas) return;

    stage.addEventListener("pointerdown", (e) => {
      if (!imageEdit.sourceImg) return;
      if (imageEdit.rotation) {
        showToast("Set rotation to 0° before drawing a crop (or crop first, then rotate).");
        return;
      }
      const handleEl =
        e.target && e.target.closest
          ? e.target.closest(".crop-handle")
          : null;
      const onCropBox =
        e.target && e.target.closest
          ? e.target.closest("#image-edit-crop-box")
          : null;
      const clamp = !!(handleEl || onCropBox || imageEdit.crop);
      const pt = imageEditClientToSourcePixels(e.clientX, e.clientY, {
        clamp: clamp,
      });
      if (!pt) return;

      if (handleEl && imageEdit.crop) {
        imageEdit.cropDrag = {
          mode: "resize",
          handle: handleEl.getAttribute("data-handle") || "se",
          x0: pt.x,
          y0: pt.y,
          startCrop: Object.assign({}, imageEdit.crop),
          pointerId: e.pointerId,
        };
      } else if (onCropBox && imageEdit.crop) {
        imageEdit.cropDrag = {
          mode: "move",
          handle: null,
          x0: pt.x,
          y0: pt.y,
          startCrop: Object.assign({}, imageEdit.crop),
          pointerId: e.pointerId,
        };
      } else {
        imageEdit.cropDrag = {
          mode: "draw",
          handle: null,
          x0: pt.x,
          y0: pt.y,
          startCrop: null,
          pointerId: e.pointerId,
        };
        // Tiny seed rect so overlay appears immediately
        imageEdit.crop = { x: pt.x, y: pt.y, w: 1, h: 1 };
      }
      updateCropBoxOverlay();
      stage.setPointerCapture(e.pointerId);
      e.preventDefault();
    });

    stage.addEventListener("pointermove", (e) => {
      if (!imageEdit.cropDrag || e.pointerId !== imageEdit.cropDrag.pointerId) return;
      const drag = imageEdit.cropDrag;
      const pt = imageEditClientToSourcePixels(e.clientX, e.clientY, {
        clamp: true,
      });
      if (!pt) return;
      const sw = pt.sw;
      const sh = pt.sh;

      if (drag.mode === "move" && drag.startCrop) {
        const dx = pt.x - drag.x0;
        const dy = pt.y - drag.y0;
        imageEdit.crop = clampImageEditCrop(
          {
            x: drag.startCrop.x + dx,
            y: drag.startCrop.y + dy,
            w: drag.startCrop.w,
            h: drag.startCrop.h,
          },
          sw,
          sh
        );
      } else if (drag.mode === "resize" && drag.startCrop && drag.handle) {
        imageEdit.crop = resizeImageEditCropFromHandle(
          drag.startCrop,
          drag.handle,
          pt.x,
          pt.y,
          sw,
          sh
        );
      } else {
        const x0 = drag.x0;
        const y0 = drag.y0;
        imageEdit.crop = clampImageEditCrop(
          {
            x: Math.min(x0, pt.x),
            y: Math.min(y0, pt.y),
            w: Math.max(1, Math.abs(pt.x - x0)),
            h: Math.max(1, Math.abs(pt.y - y0)),
          },
          sw,
          sh
        );
      }
      updateCropBoxOverlay();
    });

    const endDrag = (e) => {
      if (!imageEdit.cropDrag || e.pointerId !== imageEdit.cropDrag.pointerId) return;
      const mode = imageEdit.cropDrag.mode;
      imageEdit.cropDrag = null;
      try {
        stage.releasePointerCapture(e.pointerId);
      } catch (_) {
        /* ignore */
      }
      // Drop accidental clicks when drawing a new crop (no real drag)
      if (
        mode === "draw" &&
        imageEdit.crop &&
        (imageEdit.crop.w < 2 || imageEdit.crop.h < 2)
      ) {
        imageEdit.crop = null;
      } else if (imageEdit.crop || mode === "move" || mode === "resize") {
        markImageEditDirty();
      }
      updateCropBoxOverlay();
    };
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);
    stage.addEventListener("scroll", () => updateCropBoxOverlay());
    window.addEventListener("resize", () => updateCropBoxOverlay());
  }

  function wireImageEditEvents() {
    if ($("#btn-edit-image")) {
      $("#btn-edit-image").addEventListener("click", () => {
        void openImageEditor(state.active, { standalone: false });
      });
    }
    const controlIds = [
      "edit-brightness",
      "edit-contrast",
      "edit-saturation",
      "edit-hue",
      "edit-invert",
      "edit-sepia",
      "edit-blur",
      "edit-exposure",
      "edit-gamma",
      "edit-vignette",
      "edit-tint-r",
      "edit-tint-g",
      "edit-tint-b",
      "edit-bg-tolerance",
      "edit-rotation",
    ];
    controlIds.forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      el.addEventListener("input", () => {
        markImageEditDirty();
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
      // Some WebView hosts fire change more reliably than input on ranges
      el.addEventListener("change", () => {
        markImageEditDirty();
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
    });
    ["edit-grayscale", "edit-threshold", "edit-sharpen", "edit-bg-remove", "edit-bg-edges"].forEach(
      (id) => {
        const el = $("#" + id);
        if (!el) return;
        el.addEventListener("change", () => {
          markImageEditDirty();
          syncBgRemoveRows();
          scheduleImageEditPreview();
        });
      }
    );
    if ($("#btn-edit-rot-cw")) {
      $("#btn-edit-rot-cw").addEventListener("click", () => {
        const cur = Number($("#edit-rotation").value) || 0;
        $("#edit-rotation").value = String((cur + 90) % 360);
        markImageEditDirty();
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
    }
    if ($("#btn-edit-rot-ccw")) {
      $("#btn-edit-rot-ccw").addEventListener("click", () => {
        const cur = Number($("#edit-rotation").value) || 0;
        $("#edit-rotation").value = String((cur + 270) % 360);
        markImageEditDirty();
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
    }
    if ($("#btn-edit-crop-clear")) {
      $("#btn-edit-crop-clear").addEventListener("click", () => {
        if (imageEdit.crop) markImageEditDirty();
        imageEdit.crop = null;
        scheduleImageEditPreview();
        beep(650, 0.03);
      });
    }
    if ($("#btn-edit-reset")) {
      $("#btn-edit-reset").addEventListener("click", () => {
        resetImageEditor();
        beep(650, 0.03);
      });
    }
    if ($("#btn-edit-cancel")) {
      $("#btn-edit-cancel").addEventListener("click", () => {
        requestCloseImageEditor();
      });
    }
    if ($("#btn-edit-apply")) {
      $("#btn-edit-apply").addEventListener("click", () => {
        applyImageEditor();
      });
    }
    if ($("#btn-edit-save")) {
      $("#btn-edit-save").addEventListener("click", () => {
        saveImageEditor();
      });
    }
    if ($("#btn-edit-save-as")) {
      $("#btn-edit-save-as").addEventListener("click", () => {
        saveImageEditorAs();
      });
    }
    setupImageEditCropInteraction();
  }

  // ── Video Edit (segment timeline + filters) ────────────────────────
  const videoEdit = {
    creationId: null,
    standalone: true, // desktop app vs Viewer Edit (Apply)
    fileUrl: null,
    duration: 0,
    crop: null, // normalized {x,y,w,h, normalized:true}
    cropDrag: null,
    rotation: 0,
    segments: [], // [{id, start, end}] source times, edit order
    selectedSegId: null,
    segSeq: 0,
    playSegIdx: 0, // which segment is playing in edit order
    boundarySeeking: false, // ignore timeupdates while jumping between segments
    raf: 0,
    showFilterPreview: false,
    dirty: false,
  };

  function markVideoEditDirty() {
    videoEdit.dirty = true;
  }

  function setVideoEditLoadedLabel(creation) {
    const el = $("#vedit-loaded-label");
    if (!el) return;
    el.textContent = creation
      ? "Loaded: " + creationTitle(creation)
      : "No video loaded";
  }

  function syncVideoEditChrome() {
    const toolbar = $("#win-video-edit .editor-app-toolbar");
    if (toolbar) toolbar.hidden = !videoEdit.standalone;
    if ($("#btn-vedit-apply")) $("#btn-vedit-apply").hidden = !!videoEdit.standalone;
    if ($("#btn-vedit-save")) $("#btn-vedit-save").hidden = !videoEdit.standalone;
    // Save As is always available once a video is loaded
    if ($("#btn-vedit-save-as")) $("#btn-vedit-save-as").hidden = false;
    const hint = $("#video-edit-hint");
    if (hint) {
      hint.textContent = videoEdit.standalone
        ? "Load a video to begin. Sliders preview live on the player (play, scrub, and timeline keep working). Save writes Archives; Save As… exports MP4 (ffmpeg required)."
        : "Sliders preview live on the player while you play and edit the timeline. Apply rebuilds the video in Archives; Save As… exports MP4 (requires ffmpeg on PATH). Drag a paused frame (0°) to crop. Timeline starts at 0.00s.";
    }
  }

  function prepareEmptyVideoEditor() {
    resetVideoEditRuntime();
    videoEdit.standalone = true;
    videoEdit.dirty = false;
    setVideoEditLoadedLabel(null);
    syncVideoEditChrome();
  }

  async function loadVideoIntoEditorFromFile() {
    const a = api();
    if (!a) return;
    beginBusy("Loading video", "Importing into Archives…", { delayMs: 0 });
    try {
      const res = await a.import_media_file("video");
      if (!res || res.cancelled) return;
      if (!res.ok) {
        showToast(res.error || "Import failed");
        return;
      }
      rememberImportedCreation(res.creation);
      await openVideoEditor(res.creation, { standalone: true });
      showToast("Video loaded into Video Edit");
    } catch (err) {
      showToast("Load failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  function nextSegId() {
    videoEdit.segSeq += 1;
    return "seg_" + videoEdit.segSeq;
  }

  function initVideoSegments(duration) {
    const dur = Math.max(0.1, Number(duration) || 0.1);
    videoEdit.segments = [{ id: nextSegId(), start: 0, end: dur }];
    videoEdit.selectedSegId = videoEdit.segments[0].id;
  }

  function segmentTotalDuration() {
    return videoEdit.segments.reduce(
      (sum, s) => sum + Math.max(0, s.end - s.start),
      0
    );
  }

  /** Edited-timeline offset (0 = left edge) for the start of segment idx. */
  function editedOffsetForSegment(idx) {
    let off = 0;
    for (let i = 0; i < idx && i < videoEdit.segments.length; i++) {
      const s = videoEdit.segments[i];
      off += Math.max(0, s.end - s.start);
    }
    return off;
  }

  /** Map source player time → position on the edited timeline (0 … total). */
  function editedTimeFromSource(sourceT) {
    const t = Number(sourceT) || 0;
    let elapsed = 0;
    for (let i = 0; i < videoEdit.segments.length; i++) {
      const seg = videoEdit.segments[i];
      const len = Math.max(0, seg.end - seg.start);
      if (t >= seg.start - 0.001 && t <= seg.end + 0.001) {
        return elapsed + Math.min(len, Math.max(0, t - seg.start));
      }
      elapsed += len;
    }
    return null;
  }

  /** Map edited timeline time → source seek time + segment index. */
  function sourceFromEditedTime(editedT) {
    let remaining = Math.max(0, Number(editedT) || 0);
    const segs = videoEdit.segments;
    if (!segs.length) return { sourceTime: 0, segIdx: 0 };
    for (let i = 0; i < segs.length; i++) {
      const seg = segs[i];
      const len = Math.max(0.05, seg.end - seg.start);
      if (remaining <= len + 0.0001 || i === segs.length - 1) {
        const into = Math.min(len, remaining);
        return { sourceTime: seg.start + into, segIdx: i };
      }
      remaining -= len;
    }
    const last = segs[segs.length - 1];
    return { sourceTime: last.end, segIdx: segs.length - 1 };
  }

  /** After cut/reorder, keep the player on a valid segment; left edge = edited 0.00. */
  function snapPlayerToEditedTimeline(preferEditedTime) {
    const player = $("#video-edit-player");
    if (!player || !videoEdit.segments.length) return;
    let edited =
      preferEditedTime != null
        ? preferEditedTime
        : editedTimeFromSource(player.currentTime);
    if (edited == null || edited < 0) edited = 0;
    const mapped = sourceFromEditedTime(edited);
    videoEdit.playSegIdx = mapped.segIdx;
    if (videoEdit.segments[mapped.segIdx]) {
      videoEdit.selectedSegId = videoEdit.segments[mapped.segIdx].id;
    }
    player.currentTime = mapped.sourceTime;
  }

  function renderVideoSegments() {
    const track = $("#vedit-timeline-track");
    const summary = $("#vedit-segments-summary");
    if (!track) return;
    track.innerHTML = "";
    videoEdit.segments.forEach((seg, idx) => {
      const len = Math.max(0.05, seg.end - seg.start);
      const editStart = editedOffsetForSegment(idx);
      const editEnd = editStart + len;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "vedit-seg" + (seg.id === videoEdit.selectedSegId ? " selected" : "");
      btn.style.flexGrow = String(len);
      btn.dataset.segId = seg.id;
      btn.title =
        "Clip " +
        (idx + 1) +
        ": " +
        editStart.toFixed(2) +
        "s → " +
        editEnd.toFixed(2) +
        "s on timeline (source " +
        seg.start.toFixed(2) +
        "–" +
        seg.end.toFixed(2) +
        ")";
      btn.textContent = idx + 1 + " · " + len.toFixed(1) + "s";
      btn.addEventListener("click", () => {
        videoEdit.selectedSegId = seg.id;
        videoEdit.playSegIdx = idx;
        const player = $("#video-edit-player");
        if (player) {
          // Seek to this clip's start on the edited timeline (leftmost = 0.00)
          player.currentTime = seg.start;
          updateVideoEditTimeLabel();
        }
        renderVideoSegments();
        beep(650, 0.02);
      });
      track.appendChild(btn);
    });
    if (summary) {
      const n = videoEdit.segments.length;
      summary.textContent =
        n +
        " segment" +
        (n === 1 ? "" : "s") +
        " · " +
        segmentTotalDuration().toFixed(1) +
        "s total (timeline starts at 0.00)";
    }
    updateVideoTimelinePlayhead();
  }

  function updateVideoTimelinePlayhead() {
    const head = $("#vedit-playhead");
    const track = $("#vedit-timeline-track");
    const player = $("#video-edit-player");
    if (!head || !track || !player || !videoEdit.segments.length) {
      if (head) head.hidden = true;
      return;
    }
    const edited = editedTimeFromSource(player.currentTime || 0);
    const total = segmentTotalDuration() || 1;
    if (edited == null) {
      head.hidden = true;
      return;
    }
    head.hidden = false;
    head.style.left =
      Math.min(100, Math.max(0, (edited / total) * 100)) + "%";
  }

  function splitVideoSegmentAtPlayhead() {
    const player = $("#video-edit-player");
    const t = player ? player.currentTime : 0;
    const minLen = 0.15;
    const idx = videoEdit.segments.findIndex(
      (s) => t > s.start + minLen && t < s.end - minLen
    );
    if (idx < 0) {
      showToast("Move the playhead inside a segment (not near an edge) to split.");
      return;
    }
    const seg = videoEdit.segments[idx];
    const left = { id: seg.id, start: seg.start, end: t };
    const right = { id: nextSegId(), start: t, end: seg.end };
    videoEdit.segments.splice(idx, 1, left, right);
    videoEdit.selectedSegId = right.id;
    videoEdit.playSegIdx = idx + 1;
    markVideoEditDirty();
    renderVideoSegments();
    updateVideoEditTimeLabel();
    beep(700, 0.04);
  }

  function deleteSelectedVideoSegment() {
    if (videoEdit.segments.length <= 1) {
      showToast("Keep at least one segment.");
      return;
    }
    const id = videoEdit.selectedSegId;
    if (!id) {
      showToast("Select a segment to delete.");
      return;
    }
    const idx = videoEdit.segments.findIndex((s) => s.id === id);
    if (idx < 0) return;
    // Keep playhead near the same edited time after the cut
    const keepEdited = editedOffsetForSegment(idx);
    videoEdit.segments.splice(idx, 1);
    const nextIdx = Math.min(idx, videoEdit.segments.length - 1);
    videoEdit.selectedSegId = videoEdit.segments[nextIdx].id;
    videoEdit.playSegIdx = nextIdx;
    markVideoEditDirty();
    snapPlayerToEditedTimeline(keepEdited);
    renderVideoSegments();
    updateVideoEditTimeLabel();
    beep(300, 0.06);
  }

  function moveSelectedVideoSegment(dir) {
    const id = videoEdit.selectedSegId;
    const idx = videoEdit.segments.findIndex((s) => s.id === id);
    if (idx < 0) return;
    const j = idx + dir;
    if (j < 0 || j >= videoEdit.segments.length) return;
    // Preserve position within the moved clip on the edited timeline
    const player = $("#video-edit-player");
    const within = player
      ? Math.max(0, (player.currentTime || 0) - videoEdit.segments[idx].start)
      : 0;
    const tmp = videoEdit.segments[idx];
    videoEdit.segments[idx] = videoEdit.segments[j];
    videoEdit.segments[j] = tmp;
    videoEdit.playSegIdx = j;
    markVideoEditDirty();
    const newEditStart = editedOffsetForSegment(j);
    snapPlayerToEditedTimeline(newEditStart + within);
    renderVideoSegments();
    updateVideoEditTimeLabel();
    beep(650, 0.03);
  }

  function clearVideoFilterPreview() {
    if (videoEdit.raf) {
      cancelAnimationFrame(videoEdit.raf);
      videoEdit.raf = 0;
    }
    videoEdit.showFilterPreview = false;
    const stage = $("#video-edit-stage");
    if (stage) stage.classList.remove("previewing-filters");
    const player = $("#video-edit-player");
    if (player) {
      player.style.filter = "";
      player.style.transform = "";
    }
    const canvas = $("#video-edit-preview-canvas");
    if (canvas) {
      canvas.hidden = true;
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvas.width || 0, canvas.height || 0);
      canvas.width = 0;
      canvas.height = 0;
    }
    const box = $("#video-edit-crop-box");
    if (box) box.hidden = true;
    syncVideoEditPlayButton();
  }

  function cssFilterFromVideoEdit(filters) {
    const apiEdit = window.R98ImageEdit;
    const f =
      (apiEdit && apiEdit.normalizeFilters(filters)) ||
      filters ||
      {};
    const parts = [];
    // Match image_edit / ffmpeg approximate mapping for live preview
    const brightness = 1 + (Number(f.brightness) || 0) / 100 + ((Number(f.exposure) || 0) / 100) * 0.5;
    const contrast = 1 + (Number(f.contrast) || 0) / 100;
    parts.push("brightness(" + Math.max(0, brightness) + ")");
    parts.push("contrast(" + Math.max(0, contrast) + ")");
    if (f.grayscale) parts.push("grayscale(1)");
    const sat = Number(f.saturation);
    parts.push(
      "saturate(" +
        (Number.isFinite(sat) ? Math.max(0, sat) / 100 : 1) +
        ")"
    );
    const hue = Number(f.hueRotate) || 0;
    if (hue) parts.push("hue-rotate(" + hue + "deg)");
    const inv = Number(f.invert) || 0;
    if (inv) parts.push("invert(" + Math.max(0, Math.min(100, inv)) / 100 + ")");
    const sepia = Number(f.sepia) || 0;
    if (sepia) parts.push("sepia(" + Math.max(0, Math.min(100, sepia)) / 100 + ")");
    const blur = Number(f.blur) || 0;
    if (blur) parts.push("blur(" + Math.max(0, blur) + "px)");
    // gamma / vignette / tint / sharpen still apply on Save via ffmpeg; no clean CSS equivalent
    return parts.join(" ");
  }

  function syncVideoEditPlayButton() {
    const btn = $("#btn-vedit-play");
    const player = $("#video-edit-player");
    if (!btn) return;
    const playing = !!(player && !player.paused && !player.ended && player.readyState > 0);
    btn.textContent = playing ? "Pause" : "Play";
  }

  function toggleVideoEditPlayback() {
    const player = $("#video-edit-player");
    if (!player || !videoEdit.creationId) {
      showToast("Load a video first.");
      return;
    }
    if (player.paused || player.ended) {
      if (!videoEdit.segments.length) {
        showToast("Keep at least one segment.");
        return;
      }
      // If outside kept ranges, snap to timeline start before playing
      if (editedTimeFromSource(player.currentTime || 0) == null) {
        snapPlayerToEditedTimeline(0);
      }
      videoEdit.playSegIdx = sourceFromEditedTime(
        editedTimeFromSource(player.currentTime || 0) || 0
      ).segIdx;
      player.play().catch(() => {
        /* autoplay / decode errors surface via UI */
      });
    } else {
      player.pause();
    }
    syncVideoEditPlayButton();
  }

  function resetVideoEditRuntime() {
    clearVideoFilterPreview();
    const player = $("#video-edit-player");
    if (player) {
      player.pause();
      player.onloadedmetadata = null;
      player.ontimeupdate = null;
      player.onplay = null;
      player.onpause = null;
      player.onseeked = null;
      player.onended = null;
      player.removeAttribute("src");
      player.load();
    }
    videoEdit.creationId = null;
    videoEdit.fileUrl = null;
    videoEdit.duration = 0;
    videoEdit.crop = null;
    videoEdit.cropDrag = null;
    videoEdit.rotation = 0;
    videoEdit.segments = [];
    videoEdit.selectedSegId = null;
    videoEdit.boundarySeeking = false;
    if (window.R98ImageEdit) {
      writeVideoEditFiltersToUi(window.R98ImageEdit.DEFAULT_FILTERS);
    }
    if ($("#vedit-rotation")) $("#vedit-rotation").value = 0;
    syncVideoEditValueLabels();
    const track = $("#vedit-timeline-track");
    if (track) track.innerHTML = "";
    const summary = $("#vedit-segments-summary");
    if (summary) summary.textContent = "No segments";
    syncVideoEditPlayButton();
  }

  function closeVideoEditor() {
    closeWindow("video-edit");
  }

  async function requestCloseVideoEditor() {
    await requestCloseWindow("video-edit");
  }

  function readVideoEditFiltersFromUi() {
    return {
      brightness: Number($("#vedit-brightness") && $("#vedit-brightness").value) || 0,
      contrast: Number($("#vedit-contrast") && $("#vedit-contrast").value) || 0,
      grayscale: !!($("#vedit-grayscale") && $("#vedit-grayscale").checked),
      sharpen: !!($("#vedit-sharpen") && $("#vedit-sharpen").checked),
      saturation: Number($("#vedit-saturation") && $("#vedit-saturation").value) || 100,
      hueRotate: Number($("#vedit-hue") && $("#vedit-hue").value) || 0,
      invert: Number($("#vedit-invert") && $("#vedit-invert").value) || 0,
      sepia: Number($("#vedit-sepia") && $("#vedit-sepia").value) || 0,
      blur: Number($("#vedit-blur") && $("#vedit-blur").value) || 0,
      exposure: Number($("#vedit-exposure") && $("#vedit-exposure").value) || 0,
      gamma: Number($("#vedit-gamma") && $("#vedit-gamma").value) || 1,
      vignette: Number($("#vedit-vignette") && $("#vedit-vignette").value) || 0,
      tintRed: Number($("#vedit-tint-r") && $("#vedit-tint-r").value) || 0,
      tintGreen: Number($("#vedit-tint-g") && $("#vedit-tint-g").value) || 0,
      tintBlue: Number($("#vedit-tint-b") && $("#vedit-tint-b").value) || 0,
    };
  }

  function writeVideoEditFiltersToUi(filters) {
    const f =
      (window.R98ImageEdit && window.R98ImageEdit.normalizeFilters(filters)) ||
      filters ||
      {};
    const map = {
      "vedit-brightness": f.brightness,
      "vedit-contrast": f.contrast,
      "vedit-saturation": f.saturation,
      "vedit-hue": f.hueRotate,
      "vedit-invert": f.invert,
      "vedit-sepia": f.sepia,
      "vedit-blur": f.blur,
      "vedit-exposure": f.exposure,
      "vedit-gamma": f.gamma,
      "vedit-vignette": f.vignette,
      "vedit-tint-r": f.tintRed,
      "vedit-tint-g": f.tintGreen,
      "vedit-tint-b": f.tintBlue,
    };
    Object.keys(map).forEach((id) => {
      const el = $("#" + id);
      if (el && map[id] !== undefined) el.value = map[id];
    });
    if ($("#vedit-grayscale")) $("#vedit-grayscale").checked = !!f.grayscale;
    if ($("#vedit-sharpen")) $("#vedit-sharpen").checked = !!f.sharpen;
    syncVideoEditValueLabels();
  }

  function syncVideoEditValueLabels() {
    document.querySelectorAll("#win-video-edit .edit-val[data-for]").forEach((el) => {
      const id = el.getAttribute("data-for");
      const input = id && $("#" + id);
      if (input) el.textContent = input.value;
    });
    if ($("#vedit-rotation-label") && $("#vedit-rotation")) {
      $("#vedit-rotation-label").textContent = $("#vedit-rotation").value + "°";
    }
  }

  function findSegmentIndexAtTime(t) {
    return videoEdit.segments.findIndex(
      (s) => t >= s.start - 0.001 && t <= s.end + 0.001
    );
  }

  function syncPlaySegIdxFromTime(t) {
    const idx = findSegmentIndexAtTime(t);
    if (idx >= 0) videoEdit.playSegIdx = idx;
  }

  /**
   * Seek to an edit-order segment. Guards against stale timeupdate races while seeking,
   * and resumes playback when continuing past source EOF (HTMLVideoElement 'ended').
   */
  function seekToEditedSegment(idx, opts) {
    opts = opts || {};
    const play = opts.play !== false;
    const player = $("#video-edit-player");
    const segs = videoEdit.segments;
    if (!player || idx < 0 || idx >= segs.length) return;
    const target = Math.max(0, segs[idx].start);
    videoEdit.playSegIdx = idx;
    if (segs[idx]) videoEdit.selectedSegId = segs[idx].id;
    videoEdit.boundarySeeking = true;

    const clearGuard = () => {
      videoEdit.boundarySeeking = false;
      player.removeEventListener("seeked", onSeeked);
    };
    const onSeeked = () => clearGuard();
    player.addEventListener("seeked", onSeeked);
    window.setTimeout(clearGuard, 500);

    try {
      player.currentTime = target;
    } catch (_) {
      /* ignore */
    }
    if (play) {
      const p = player.play();
      if (p && typeof p.catch === "function") {
        p.catch(() => {
          /* autoplay / play() rejection */
        });
      }
    }
  }

  /** Jump from the current edit-order segment to the next, or stop at timeline end. */
  function continueEditedPlaybackFromBoundary() {
    const player = $("#video-edit-player");
    if (!player || !videoEdit.segments.length) return false;
    const segs = videoEdit.segments;
    let idx = videoEdit.playSegIdx;
    if (idx < 0 || idx >= segs.length) {
      idx = findSegmentIndexAtTime(player.currentTime);
      if (idx < 0) idx = 0;
      videoEdit.playSegIdx = idx;
    }
    const next = idx + 1;
    if (next >= segs.length) {
      videoEdit.playSegIdx = Math.max(0, segs.length - 1);
      try {
        player.pause();
      } catch (_) {
        /* ignore */
      }
      scheduleVideoFilterPreview();
      return false;
    }
    seekToEditedSegment(next, { play: true });
    return true;
  }

  /** During playback, stay inside segments in edit order (skip deletes / honor reorder). */
  function advanceEditedPlayback() {
    const player = $("#video-edit-player");
    if (!player || !videoEdit.segments.length) return;
    if (videoEdit.boundarySeeking) return;
    // When a segment ends at source EOF, the element pauses via 'ended' before
    // the next timeupdate — still allow advancing in that case.
    if (player.paused && !player.ended) return;

    const segs = videoEdit.segments;
    let idx = videoEdit.playSegIdx;
    if (idx < 0 || idx >= segs.length) {
      idx = findSegmentIndexAtTime(player.currentTime);
      if (idx < 0) idx = 0;
      videoEdit.playSegIdx = idx;
    }
    const seg = segs[idx];
    const t = player.currentTime;
    const mediaDur = Number(player.duration);
    const nearMediaEnd =
      Number.isFinite(mediaDur) && mediaDur > 0 && t >= mediaDur - 0.15;

    if (!player.ended && t < seg.start - 0.02) {
      seekToEditedSegment(idx, { play: !player.paused });
      return;
    }

    // Only treat as segment-complete when time is actually in/near this segment
    // (avoids stale currentTime after a seek to an earlier source range).
    const inOrPastSeg =
      player.ended ||
      nearMediaEnd ||
      (t >= seg.start - 0.05 && t >= seg.end - 0.05);
    if (inOrPastSeg && (player.ended || nearMediaEnd || t >= seg.end - 0.04)) {
      continueEditedPlaybackFromBoundary();
    }
  }

  function onVideoEditEnded() {
    // Source EOF while more edit-order clips remain (e.g. end clip moved first).
    if (videoEdit.boundarySeeking) return;
    continueEditedPlaybackFromBoundary();
    updateVideoEditTimeLabel();
  }

  function updateVideoEditTimeLabel() {
    const player = $("#video-edit-player");
    if (!player || !$("#vedit-time-label")) return;
    advanceEditedPlayback();
    const editedDur = segmentTotalDuration();
    let edited = editedTimeFromSource(player.currentTime || 0);
    if (edited == null) {
      // Outside kept ranges (e.g. just deleted) — snap to timeline start
      snapPlayerToEditedTimeline(0);
      edited = editedTimeFromSource(player.currentTime || 0) || 0;
    }
    $("#vedit-time-label").textContent =
      edited.toFixed(2) + "s / " + editedDur.toFixed(2) + "s";
    if ($("#vedit-scrub") && editedDur > 0) {
      $("#vedit-scrub").value = String(
        Math.round((edited / editedDur) * 1000)
      );
    }
    updateVideoTimelinePlayhead();
  }

  function scheduleVideoFilterPreview() {
    if (videoEdit.raf) cancelAnimationFrame(videoEdit.raf);
    videoEdit.raf = requestAnimationFrame(() => {
      videoEdit.raf = 0;
      renderVideoFilterPreview();
    });
  }

  function renderVideoFilterPreview() {
    const player = $("#video-edit-player");
    const canvas = $("#video-edit-preview-canvas");
    const stage = $("#video-edit-stage");
    if (!player || !stage || !videoEdit.creationId) return;

    // Always keep the native player visible (size + play controls). Preview via CSS.
    if (canvas) canvas.hidden = true;
    if (stage) stage.classList.remove("previewing-filters");

    const filters = readVideoEditFiltersFromUi();
    videoEdit.rotation = Number($("#vedit-rotation") && $("#vedit-rotation").value) || 0;
    const cssFilter = cssFilterFromVideoEdit(filters);
    player.style.filter = cssFilter || "";
    player.style.transform = videoEdit.rotation
      ? "rotate(" + videoEdit.rotation + "deg)"
      : "";
    videoEdit.showFilterPreview = !!(cssFilter || videoEdit.rotation || videoEdit.crop);
    updateVideoCropOverlay();
    syncVideoEditPlayButton();
  }

  function updateVideoCropOverlay() {
    const box = $("#video-edit-crop-box");
    const stage = $("#video-edit-stage");
    const player = $("#video-edit-player");
    if (!box || !stage) return;
    const crop = videoEdit.crop;
    if (!crop || videoEdit.rotation) {
      box.hidden = true;
      return;
    }
    const target = player;
    if (!target) {
      box.hidden = true;
      return;
    }
    const targetRect = target.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    const scaleX = targetRect.width;
    const scaleY = targetRect.height;
    box.hidden = false;
    box.style.left =
      targetRect.left - stageRect.left + stage.scrollLeft + crop.x * scaleX + "px";
    box.style.top =
      targetRect.top - stageRect.top + stage.scrollTop + crop.y * scaleY + "px";
    box.style.width = Math.max(1, crop.w * scaleX) + "px";
    box.style.height = Math.max(1, crop.h * scaleY) + "px";
  }

  async function openVideoEditor(creation, opts) {
    opts = opts || {};
    if (!creation || creationModality(creation) !== "video") {
      showToast("Edit is available for video creations.");
      return false;
    }
    const a = api();
    if (!a) {
      showToast("Python bridge required to edit videos.");
      return false;
    }
    const status = await a.ffmpeg_status();
    if (!status || !status.ok) {
      showToast(
        (status && status.error) ||
          "ffmpeg not found. Install ffmpeg and add it to PATH."
      );
      return false;
    }

    const payload = await a.get_media_payload(creation);
    if (!payload || !payload.ok || !payload.fileUrl) {
      showToast((payload && payload.error) || "Could not load video.");
      return false;
    }

    let info = { duration: 0 };
    try {
      info = await a.get_video_info(creation.id);
    } catch (_) {
      /* ignore */
    }

    videoEdit.creationId = creation.id;
    videoEdit.standalone =
      typeof opts.standalone === "boolean" ? opts.standalone : true;
    videoEdit.fileUrl = payload.fileUrl;
    videoEdit.duration = Number(info.duration) || 0;
    videoEdit.crop = null;
    videoEdit.cropDrag = null;
    videoEdit.rotation = 0;
    videoEdit.dirty = false;
    clearVideoFilterPreview();
    if ($("#vedit-rotation")) $("#vedit-rotation").value = 0;
    writeVideoEditFiltersToUi(
      (window.R98ImageEdit && window.R98ImageEdit.DEFAULT_FILTERS) || {}
    );
    initVideoSegments(videoEdit.duration || 0.1);

    const player = $("#video-edit-player");
    if (player) {
      player.pause();
      player.src = payload.fileUrl;
      player.onloadedmetadata = () => {
        if (!videoEdit.duration && player.duration) {
          videoEdit.duration = player.duration;
          initVideoSegments(player.duration);
          renderVideoSegments();
        }
        updateVideoEditTimeLabel();
        scheduleVideoFilterPreview();
        syncVideoEditPlayButton();
      };
      player.ontimeupdate = () => updateVideoEditTimeLabel();
      player.onplay = () => syncVideoEditPlayButton();
      player.onpause = () => {
        syncVideoEditPlayButton();
        scheduleVideoFilterPreview();
      };
      player.onseeked = () => scheduleVideoFilterPreview();
      player.onended = () => {
        syncVideoEditPlayButton();
        onVideoEditEnded();
      };
    }

    renderVideoSegments();
    setVideoEditLoadedLabel(creation);
    syncVideoEditChrome();
    openWindow("video-edit");
    scheduleVideoFilterPreview();
    beep(700, 0.04);
    return true;
  }

  function resetVideoEditor() {
    writeVideoEditFiltersToUi(
      (window.R98ImageEdit && window.R98ImageEdit.DEFAULT_FILTERS) || {}
    );
    videoEdit.crop = null;
    videoEdit.rotation = 0;
    videoEdit.dirty = false;
    if ($("#vedit-rotation")) $("#vedit-rotation").value = 0;
    initVideoSegments(videoEdit.duration || 0.1);
    syncVideoEditValueLabels();
    clearVideoFilterPreview();
    renderVideoSegments();
    scheduleVideoFilterPreview();
  }

  function buildVideoEditOps() {
    const filters = readVideoEditFiltersFromUi();
    const rotation = Number($("#vedit-rotation") && $("#vedit-rotation").value) || 0;
    const ops = {
      filters,
      rotation,
      segments: videoEdit.segments.map((s) => ({
        start: s.start,
        end: s.end,
      })),
    };
    if (videoEdit.crop) {
      ops.crop = {
        x: videoEdit.crop.x,
        y: videoEdit.crop.y,
        w: videoEdit.crop.w,
        h: videoEdit.crop.h,
        normalized: true,
      };
    }
    return ops;
  }

  async function applyVideoEditor() {
    if (!videoEdit.creationId) {
      showToast("Load a video first.");
      return;
    }
    if (!videoEdit.segments.length) {
      showToast("Keep at least one segment.");
      return;
    }
    const a = api();
    if (!a) return;
    beginBusy("Saving video edit", "Cutting and assembling segments…", {
      delayMs: 0,
    });
    try {
      const res = await a.edit_video(videoEdit.creationId, buildVideoEditOps());
      if (!res || !res.ok) {
        showToast((res && res.error) || "Failed to save edited video");
        return;
      }
      const saved = res.creation;
      state.creations = [saved].concat(
        state.creations.filter((c) => c.id !== saved.id)
      );
      state.active = saved;
      renderArchives();
      renderDocument(saved);
      closeVideoEditor();
      showToast("Video edit applied");
      beep(900, 0.05);
    } catch (err) {
      showToast("Video edit failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  async function saveVideoEditor() {
    if (!videoEdit.creationId) {
      showToast("Load a video first.");
      return;
    }
    if (!videoEdit.segments.length) {
      showToast("Keep at least one segment.");
      return;
    }
    const a = api();
    if (!a) return;
    const keepStandalone = videoEdit.standalone;
    beginBusy("Saving video", "Cutting and assembling segments…", {
      delayMs: 0,
    });
    try {
      const res = await a.edit_video(videoEdit.creationId, buildVideoEditOps());
      if (!res || !res.ok) {
        showToast((res && res.error) || "Failed to save edited video");
        return;
      }
      const saved = res.creation;
      state.creations = [saved].concat(
        state.creations.filter((c) => c.id !== saved.id)
      );
      state.active = saved;
      renderArchives();
      await openVideoEditor(saved, { standalone: keepStandalone });
      showToast("Video saved");
      beep(900, 0.05);
    } catch (err) {
      showToast("Save failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  async function saveVideoEditorAs() {
    if (!videoEdit.creationId) {
      showToast("Load a video first.");
      return;
    }
    if (!videoEdit.segments.length) {
      showToast("Keep at least one segment.");
      return;
    }
    const a = api();
    if (!a) return;
    beginBusy("Save As", "Rendering edited video…", { delayMs: 0 });
    try {
      const res = await a.export_edited_video(
        videoEdit.creationId,
        buildVideoEditOps()
      );
      if (res && res.cancelled) return;
      if (!res || !res.ok) {
        showToast((res && res.error) || "Save As failed");
        return;
      }
      showToast("Saved to " + (res.path || "file"));
      beep(900, 0.05);
    } catch (err) {
      showToast("Save As failed: " + err);
    } finally {
      endBusy("Ready");
    }
  }

  function setupVideoEditCropInteraction() {
    const stage = $("#video-edit-stage");
    if (!stage) return;

    stage.addEventListener("pointerdown", (e) => {
      if (!videoEdit.creationId) return;
      if (videoEdit.rotation) {
        showToast("Set rotation to 0° before drawing a crop.");
        return;
      }
      const player = $("#video-edit-player");
      if (player && !player.paused) player.pause();
      const target = player;
      if (!target) return;
      const rect = target.getBoundingClientRect();
      if (rect.width < 1 || rect.height < 1) return;
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      if (x < 0 || y < 0 || x > 1 || y > 1) return;
      videoEdit.cropDrag = { x0: x, y0: y, pointerId: e.pointerId };
      stage.setPointerCapture(e.pointerId);
      e.preventDefault();
    });

    stage.addEventListener("pointermove", (e) => {
      if (!videoEdit.cropDrag || e.pointerId !== videoEdit.cropDrag.pointerId) return;
      const player = $("#video-edit-player");
      const target = player;
      if (!target) return;
      const rect = target.getBoundingClientRect();
      const x = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
      const y = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height));
      const x0 = videoEdit.cropDrag.x0;
      const y0 = videoEdit.cropDrag.y0;
      videoEdit.crop = {
        x: Math.min(x0, x),
        y: Math.min(y0, y),
        w: Math.max(0.01, Math.abs(x - x0)),
        h: Math.max(0.01, Math.abs(y - y0)),
        normalized: true,
      };
      updateVideoCropOverlay();
    });

    const endDrag = (e) => {
      if (!videoEdit.cropDrag || e.pointerId !== videoEdit.cropDrag.pointerId) return;
      videoEdit.cropDrag = null;
      try {
        stage.releasePointerCapture(e.pointerId);
      } catch (_) {
        /* ignore */
      }
      if (videoEdit.crop) markVideoEditDirty();
      scheduleVideoFilterPreview();
    };
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);
  }

  function wireVideoEditEvents() {
    if ($("#btn-edit-video")) {
      $("#btn-edit-video").addEventListener("click", () => {
        void openVideoEditor(state.active, { standalone: false });
      });
    }
    const sliderIds = [
      "vedit-brightness",
      "vedit-contrast",
      "vedit-saturation",
      "vedit-hue",
      "vedit-invert",
      "vedit-sepia",
      "vedit-blur",
      "vedit-exposure",
      "vedit-gamma",
      "vedit-vignette",
      "vedit-tint-r",
      "vedit-tint-g",
      "vedit-tint-b",
      "vedit-rotation",
    ];
    sliderIds.forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      el.addEventListener("input", () => {
        markVideoEditDirty();
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
      el.addEventListener("change", () => {
        markVideoEditDirty();
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
    });
    ["vedit-grayscale", "vedit-sharpen"].forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      el.addEventListener("change", () => {
        markVideoEditDirty();
        scheduleVideoFilterPreview();
      });
    });

    if ($("#vedit-scrub")) {
      $("#vedit-scrub").addEventListener("input", () => {
        const player = $("#video-edit-player");
        const editedDur = segmentTotalDuration();
        if (!player || editedDur <= 0) return;
        const edited =
          (Number($("#vedit-scrub").value) / 1000) * editedDur;
        const mapped = sourceFromEditedTime(edited);
        videoEdit.playSegIdx = mapped.segIdx;
        player.currentTime = mapped.sourceTime;
        updateVideoEditTimeLabel();
      });
    }
    if ($("#btn-vedit-play")) {
      $("#btn-vedit-play").addEventListener("click", () => {
        toggleVideoEditPlayback();
        beep(650, 0.03);
      });
    }
    if ($("#btn-vedit-rewind")) {
      $("#btn-vedit-rewind").addEventListener("click", () => {
        const player = $("#video-edit-player");
        if (!player || !videoEdit.segments.length) return;
        player.pause();
        snapPlayerToEditedTimeline(0);
        updateVideoEditTimeLabel();
        scheduleVideoFilterPreview();
        syncVideoEditPlayButton();
        beep(650, 0.03);
      });
    }
    if ($("#btn-vedit-split")) {
      $("#btn-vedit-split").addEventListener("click", () =>
        splitVideoSegmentAtPlayhead()
      );
    }
    if ($("#btn-vedit-seg-delete")) {
      $("#btn-vedit-seg-delete").addEventListener("click", () =>
        deleteSelectedVideoSegment()
      );
    }
    if ($("#btn-vedit-seg-left")) {
      $("#btn-vedit-seg-left").addEventListener("click", () =>
        moveSelectedVideoSegment(-1)
      );
    }
    if ($("#btn-vedit-seg-right")) {
      $("#btn-vedit-seg-right").addEventListener("click", () =>
        moveSelectedVideoSegment(1)
      );
    }
    if ($("#btn-vedit-rot-cw")) {
      $("#btn-vedit-rot-cw").addEventListener("click", () => {
        const cur = Number($("#vedit-rotation").value) || 0;
        $("#vedit-rotation").value = String((cur + 90) % 360);
        markVideoEditDirty();
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
    }
    if ($("#btn-vedit-rot-ccw")) {
      $("#btn-vedit-rot-ccw").addEventListener("click", () => {
        const cur = Number($("#vedit-rotation").value) || 0;
        $("#vedit-rotation").value = String((cur + 270) % 360);
        markVideoEditDirty();
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
    }
    if ($("#btn-vedit-crop-clear")) {
      $("#btn-vedit-crop-clear").addEventListener("click", () => {
        if (videoEdit.crop) markVideoEditDirty();
        videoEdit.crop = null;
        scheduleVideoFilterPreview();
      });
    }
    if ($("#btn-vedit-reset")) {
      $("#btn-vedit-reset").addEventListener("click", () => {
        resetVideoEditor();
        beep(650, 0.03);
      });
    }
    if ($("#btn-vedit-cancel")) {
      $("#btn-vedit-cancel").addEventListener("click", () =>
        requestCloseVideoEditor()
      );
    }
    if ($("#btn-vedit-apply")) {
      $("#btn-vedit-apply").addEventListener("click", () => applyVideoEditor());
    }
    if ($("#btn-vedit-save")) {
      $("#btn-vedit-save").addEventListener("click", () => saveVideoEditor());
    }
    if ($("#btn-vedit-save-as")) {
      $("#btn-vedit-save-as").addEventListener("click", () => saveVideoEditorAs());
    }
    setupVideoEditCropInteraction();
  }

  function wireEvents() {
    // Desktop icons + Start menu items (event delegation)
    document.addEventListener("click", (e) => {
      const openEl = e.target.closest("[data-open]");
      if (openEl) {
        e.preventDefault();
        openWindow(openEl.getAttribute("data-open"));
        toggleStartMenu(false);
        return;
      }

      // Title-bar minimize / close — must win over long title text
      const chromeBtn = e.target.closest(".title-bar-controls button");
      if (chromeBtn) {
        e.preventDefault();
        e.stopPropagation();
        const win = chromeBtn.closest(".app-window");
        if (!win) return;
        const id = win.dataset.window;
        const action =
          chromeBtn.getAttribute("data-action") ||
          chromeBtn.getAttribute("aria-label") ||
          "";
        const a = action.toLowerCase();
        if (a === "close") requestCloseWindow(id);
        else if (a === "minimize") minimizeWindow(id);
        return;
      }

      if (e.target.closest("#start-btn")) {
        e.preventDefault();
        e.stopPropagation();
        toggleStartMenu();
        beep(600, 0.03);
        return;
      }

      if (!e.target.closest("#start-menu") && !e.target.closest("#start-btn")) {
        toggleStartMenu(false);
      }
    });

    document.addEventListener("mousedown", (e) => {
      const win = e.target.closest(".app-window");
      if (win && win.dataset.window) focusWindow(win.dataset.window);
    });

    $("#create-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      await startGeneration();
    });

    $("#btn-generate").addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      await startGeneration();
    });

    if ($("#btn-studio-load-text")) {
      $("#btn-studio-load-text").addEventListener("click", () => studioLoadTextFile());
    }
    if ($("#btn-studio-load-image")) {
      $("#btn-studio-load-image").addEventListener("click", () =>
        studioLoadMediaFile("image")
      );
    }
    if ($("#btn-studio-load-video")) {
      $("#btn-studio-load-video").addEventListener("click", () =>
        studioLoadMediaFile("video")
      );
    }
    if ($("#btn-studio-use-active")) {
      $("#btn-studio-use-active").addEventListener("click", () =>
        useCreationAsBasis(state.active)
      );
    }
    if ($("#btn-studio-clear-basis")) {
      $("#btn-studio-clear-basis").addEventListener("click", () => {
        clearStudioBasis();
        showToast("Media basis cleared");
        beep(650, 0.03);
      });
    }
    if ($("#btn-use-basis")) {
      $("#btn-use-basis").addEventListener("click", () =>
        useCreationAsBasis(state.active)
      );
    }
    if ($("#btn-iedit-load")) {
      $("#btn-iedit-load").addEventListener("click", () =>
        loadImageIntoEditorFromFile()
      );
    }
    if ($("#btn-vedit-load")) {
      $("#btn-vedit-load").addEventListener("click", () =>
        loadVideoIntoEditorFromFile()
      );
    }

    if ($("#busy-cancel")) {
      $("#busy-cancel").addEventListener("click", () => {
        requestCancelBusyJob();
      });
    }

    $("#archive-search").addEventListener("input", renderArchives);
    document.querySelectorAll(".arch-sort-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        setArchiveSort(btn.getAttribute("data-sort"));
      });
    });

    $("#btn-export-all").addEventListener("click", async () => {
      const a = api();
      if (!a) return;
      const json = await a.export_creations_json();
      const date = new Date().toISOString().slice(0, 10);
      await a.save_file_dialog("retro_98_ai_creator_archives_" + date + ".json", json);
      beep(900, 0.05);
    });

    $("#btn-import").addEventListener("click", async () => {
      const a = api();
      if (!a) return;
      const res = await a.open_json_import();
      if (res.ok) {
        state.creations = res.creations;
        renderArchives();
        showToast("Imported " + res.imported + " item(s)");
        beep(900, 0.05);
      } else if (!res.cancelled) {
        showToast(res.error || "Import failed");
      }
    });

    if ($("#btn-import-text")) {
      $("#btn-import-text").addEventListener("click", () => archivesImportText());
    }
    if ($("#btn-import-image")) {
      $("#btn-import-image").addEventListener("click", () =>
        archivesImportMedia("image")
      );
    }
    if ($("#btn-import-video")) {
      $("#btn-import-video").addEventListener("click", () =>
        archivesImportMedia("video")
      );
    }

    $("#btn-export-txt").addEventListener("click", async () => {
      if (!state.active) return;
      const modality = creationModality(state.active);
      const extracted = getExtractedText(state.active);
      if (modality !== "text" && !extracted) {
        showToast("Run Extract Text… first, or open a text creation.");
        return;
      }
      const a = api();
      if (!a) return;
      try {
        const txt = await a.export_creation_txt(state.active);
        const suffix =
          modality === "video"
            ? "_transcript.txt"
            : modality === "image"
              ? "_ocr.txt"
              : ".txt";
        const name =
          modality === "text"
            ? exportBaseName(state.active) + ".txt"
            : exportBaseName(state.active) + suffix;
        await a.save_file_dialog(name, txt);
      } catch (err) {
        showToast(String(err));
      }
    });

    if ($("#btn-extract-text")) {
      $("#btn-extract-text").addEventListener("click", () => {
        extractCreationText();
      });
    }

    const docCanvas = $("#doc-canvas");
    if (docCanvas) {
      docCanvas.addEventListener("click", async (e) => {
        const btn = e.target && e.target.closest && e.target.closest("#btn-copy-extracted");
        if (!btn) return;
        const text = getExtractedText(state.active);
        if (!text) return;
        try {
          await navigator.clipboard.writeText(text);
          showToast("Copied extracted text.");
        } catch (_) {
          showToast("Could not copy to clipboard.");
        }
      });
    }

    $("#btn-export-json").addEventListener("click", async () => {
      if (!state.active) return;
      const a = api();
      if (!a) return;
      const name = exportBaseName(state.active) + ".json";
      const payload = exportCreationMetadata(state.active);
      await a.save_file_dialog(name, JSON.stringify(payload, null, 2));
    });

    $("#btn-export-png").addEventListener("click", () => {
      exportDocumentImage("png");
    });

    $("#btn-export-pdf").addEventListener("click", () => {
      exportDocumentImage("pdf");
    });

    if ($("#btn-export-media")) {
      $("#btn-export-media").addEventListener("click", async () => {
        if (!state.active) return;
        const a = api();
        if (!a) return;
        const res = await a.export_creation_media(state.active);
        if (res.ok) {
          showToast(
            creationModality(state.active) === "video"
              ? "Saved MP4"
              : "Saved media file"
          );
          beep(900, 0.05);
        } else if (!res.cancelled) {
          showToast(res.error || "Media save failed");
        }
      });
    }

    $("#btn-voice").addEventListener("click", () => {
      toggleVoiceReader();
    });

    document.querySelectorAll(".viewer-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        setViewerTab(btn.getAttribute("data-tab"));
        beep(650, 0.03);
      });
    });

    $("#btn-copy-ascii").addEventListener("click", async () => {
      if (!state.active || creationModality(state.active) !== "text") {
        showToast("ASCII copy is for text creations only.");
        return;
      }
      const text = creationToAscii(state.active);
      try {
        await navigator.clipboard.writeText(text);
        showToast("ASCII document copied to clipboard");
        beep(1000, 0.04);
      } catch (_) {
        showToast("Clipboard unavailable");
      }
    });

    ["hf-text-model", "hf-image-model", "hf-video-model"].forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      el.addEventListener("change", () => {
        updateStudioBackendLabel({
          config: {
            backend: {
              provider:
                ($("#backend-provider") && $("#backend-provider").value) ||
                "huggingface",
            },
            gemini: currentGeminiUiConfig(),
            openrouter: currentOpenRouterUiConfig(),
            huggingface: currentHfUiConfig(),
          },
        });
      });
    });

    ["gemini-text-model", "gemini-image-model", "gemini-video-model"].forEach(
      (id) => {
        const el = $("#" + id);
        if (!el) return;
        el.addEventListener("change", () => {
          updateStudioBackendLabel({
            config: {
              backend: {
                provider:
                  ($("#backend-provider") && $("#backend-provider").value) ||
                  "gemini",
              },
              gemini: currentGeminiUiConfig(),
              openrouter: currentOpenRouterUiConfig(),
              huggingface: currentHfUiConfig(),
            },
          });
        });
      }
    );

    [
      "openrouter-text-model",
      "openrouter-image-model",
      "openrouter-video-model",
    ].forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      el.addEventListener("change", () => {
        updateStudioBackendLabel({
          config: {
            backend: {
              provider:
                ($("#backend-provider") && $("#backend-provider").value) ||
                "openrouter",
            },
            gemini: currentGeminiUiConfig(),
            openrouter: currentOpenRouterUiConfig(),
            huggingface: currentHfUiConfig(),
          },
        });
      });
    });

    if ($("#backend-provider")) {
      $("#backend-provider").addEventListener("change", () => {
        syncBackendPanels();
        updateApiKeyIndicators();
        updateStudioBackendLabel({
          config: {
            backend: { provider: $("#backend-provider").value },
            gemini: currentGeminiUiConfig(),
            openrouter: currentOpenRouterUiConfig(),
            huggingface: currentHfUiConfig(),
          },
        });
      });
    }

    if ($("#gemini-search")) {
      $("#gemini-search").addEventListener("change", () => {
        syncGeminiTwoPassAvailability();
      });
    }

    $("#btn-save-model").addEventListener("click", async () => {
      await saveControlPanelSettings({ offerDownload: true });
    });

    if ($("#btn-hf-refresh-models")) {
      $("#btn-hf-refresh-models").addEventListener("click", () => {
        void refreshHfModelsForControlPanel();
      });
    }

    if ($("#btn-openrouter-refresh-models")) {
      $("#btn-openrouter-refresh-models").addEventListener("click", () => {
        void refreshOpenRouterModelsForControlPanel();
      });
    }

    $("#btn-save-settings").addEventListener("click", async () => {
      await saveControlPanelSettings({ applyDisplay: true });
    });

    document.querySelectorAll(".btn-cancel-control").forEach((btn) => {
      btn.addEventListener("click", () => {
        cancelControlPanel();
      });
    });

    document.querySelectorAll('.control-tabs [role="tab"]').forEach((tabEl) => {
      const activate = (e) => {
        e.preventDefault();
        setControlTab(tabEl.getAttribute("data-control-tab"));
        beep(650, 0.03);
      };
      const link = tabEl.querySelector("a");
      if (link) link.addEventListener("click", activate);
      else tabEl.addEventListener("click", activate);
    });

    $("#opt-sound").addEventListener("change", () => {
      state.soundEnabled = $("#opt-sound").checked;
    });
    $("#opt-crt").addEventListener("change", () => {
      state.crtEnabled = $("#opt-crt").checked;
      $("#crt-overlay").hidden = !state.crtEnabled;
    });
    if ($("#ui-scale")) {
      $("#ui-scale").addEventListener("change", () => {
        applyUiScale(readUiScaleFromControl());
        beep(700, 0.03);
      });
    }
    if ($("#app-theme")) {
      $("#app-theme").addEventListener("change", () => {
        syncCustomThemeControlsVisibility();
        applyAppTheme($("#app-theme").value);
        beep(700, 0.03);
      });
    }
    if ($("#ui-font")) {
      $("#ui-font").addEventListener("change", () => {
        applyUiFont($("#ui-font").value);
        beep(700, 0.03);
      });
    }
    [
      "custom-desktop-color",
      "custom-window-color",
      "custom-title-color",
      "custom-text-color",
    ].forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      el.addEventListener("input", () => {
        if ((($("#app-theme") && $("#app-theme").value) || "") !== "custom") return;
        applyAppTheme("custom");
      });
    });

    wireImageEditEvents();
    wireVideoEditEvents();
  }

  async function init() {
    // Catalogs first — never depend on Python for dropdowns
    fillCatalogs(null);
    fillAppThemeSelect();
    fillUiFontSelect();
    applyUiFont(state.uiFont || "inter");
    applyAppTheme(state.appTheme || "light");
    syncControlPanelWidth();
    wireEvents();
    enableWindowDragging();
    enableWindowResizing();
    tickClock();
    setInterval(tickClock, 15000);
    focusWindow("form");
    renderTaskbar();
    syncDesktopScrollExtent();
    window.addEventListener("resize", () => syncDesktopScrollExtent());

    const a = await waitForApi();
    if (!a) {
      showToast(
        "Running without Python bridge — open via: python -m retro_98_ai_creator"
      );
      return;
    }

    try {
      const boot = await a.get_bootstrap();
      state.config = boot.config;
      state.creations = boot.creations || [];
      fillCatalogs(boot);
      fillControlPanel(boot);
      applyGameDefaults({ applyPlatform: true, applyTheme: true });
      renderArchives();
      // Do not auto-open Viewer/Archives on launch — user opens them explicitly
      renderTaskbar();
    } catch (err) {
      console.error(err);
      showToast("Bootstrap failed: " + err);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
