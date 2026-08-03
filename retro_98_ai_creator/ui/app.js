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
    config: null,
    viewerTab: "doc",
    speechPlaying: false,
    controlTab: "ai",
    presets: [],
    creationTypes: [],
    defaultPlatform: "",
    defaultTheme: "auto",
    appTheme: "light",
    customTheme: {
      desktopColor: "#008080",
      windowColor: "#c0c0c0",
      titleColor: "#000080",
      textColor: "#222222",
      font: "sans",
    },
  };

  const UI_FONT_STACKS = {
    sans: '"Pixelated MS Sans Serif", "MS Sans Serif", Tahoma, sans-serif',
    serif: 'Georgia, "Times New Roman", Times, serif',
    mono: '"Courier New", Courier, monospace',
  };

  const FONT_STACKS = {
    mono: '"Courier New", Courier, monospace',
    serif: 'Georgia, "Times New Roman", serif',
    sans: '"Pixelated MS Sans Serif", "MS Sans Serif", Tahoma, sans-serif',
  };

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
      font: resolveCustomFontKey(
        $("#custom-ui-font") && $("#custom-ui-font").value
      ),
    };
  }

  function writeCustomThemeToControls(custom) {
    const c = custom || state.customTheme;
    if ($("#custom-desktop-color")) $("#custom-desktop-color").value = c.desktopColor;
    if ($("#custom-window-color")) $("#custom-window-color").value = c.windowColor;
    if ($("#custom-title-color")) $("#custom-title-color").value = c.titleColor;
    if ($("#custom-text-color")) $("#custom-text-color").value = c.textColor;
    if ($("#custom-ui-font")) $("#custom-ui-font").value = resolveCustomFontKey(c.font);
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
    const fontKey = resolveCustomFontKey(t.fontStyle);
    const uiFont = UI_FONT_STACKS[fontKey] || UI_FONT_STACKS.sans;

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
    root.style.setProperty("--ui-font", uiFont);

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
  const busy = {
    visible: false,
    showTimer: null,
    elapsedTimer: null,
    startedAt: 0,
    title: "Please wait…",
    cancellable: false,
    cancelling: false,
    jobId: null,
  };

  function showConfirm(title, message) {
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
      if (titleEl) titleEl.textContent = title || "Confirm";
      if (msgEl) msgEl.textContent = message || "";
      overlay.hidden = false;

      const finish = (value) => {
        overlay.hidden = true;
        yesBtn.removeEventListener("click", onYes);
        noBtn.removeEventListener("click", onNo);
        resolve(value);
      };
      const onYes = () => finish(true);
      const onNo = () => finish(false);
      yesBtn.addEventListener("click", onYes);
      noBtn.addEventListener("click", onNo);
      yesBtn.focus();
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
    const hint = $("#busy-hint");
    if (hint) {
      hint.textContent =
        "Gemini usually finishes in seconds. Local models can take minutes.";
    }
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
    const hint = $("#busy-hint");
    if (hint) {
      hint.textContent =
        "Downloading / loading the local model. Create is blocked until this finishes.";
    }
    beginBusy("Downloading model", "Starting Hugging Face download / load…", {
      delayMs: 0,
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
      "Download local model?",
      "Settings were saved.\n\n" +
        "Download and load the Hugging Face model now?\n\n" +
        "Yes — start the download (Create stays blocked until it finishes).\n" +
        "No — skip download for now."
    );
    if (!go) {
      showToast("Saved — local model not downloaded yet.");
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
    const hintEl = $("#busy-hint");
    if (hintEl && hint) hintEl.textContent = hint;
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
   */
  function beginBusy(title, message, opts) {
    opts = opts || {};
    const delayMs = opts.delayMs != null ? opts.delayMs : 1500;
    busy.title = title || "Please wait…";
    if ("cancellable" in opts) busy.cancellable = !!opts.cancellable;
    if ("jobId" in opts) busy.jobId = opts.jobId || null;
    if (!opts.cancellable) busy.cancelling = false;
    clearTimeout(busy.showTimer);
    setProgress(message || title || "Working…");

    if (delayMs <= 0) {
      _showBusyNow(busy.title, message, opts.percent, opts.hint);
      return;
    }

    // If already visible, just update
    if (busy.visible) {
      $("#busy-title").textContent = busy.title;
      $("#busy-message").textContent = message || "Working…";
      if (opts.hint && $("#busy-hint")) $("#busy-hint").textContent = opts.hint;
      if ("percent" in opts) setBusyPercent(opts.percent);
      setBusyCancelVisible(!!busy.cancellable);
      return;
    }

    busy.startedAt = Date.now();
    busy.showTimer = setTimeout(() => {
      _showBusyNow(busy.title, message, opts.percent, opts.hint);
    }, delayMs);
  }

  function updateBusy(message, percent) {
    if (message) {
      setProgress(message);
      const msgEl = $("#busy-message");
      if (msgEl) msgEl.textContent = message;
    }
    if (percent !== undefined) setBusyPercent(percent);

    // If a deferred show is pending and we got real progress, show immediately
    if (!busy.visible && busy.showTimer && (message || percent != null)) {
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
    busy.cancellable = false;
    busy.cancelling = false;
    busy.jobId = null;
    setBusyCancelVisible(false);
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
   * Text → Studio prompt. Image/video → duplicate into Archives, then open editor.
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

    beginBusy("Preparing basis", "Copying into Archives as a new item…", {
      delayMs: 0,
    });
    try {
      const res = await a.duplicate_creation(creation.id);
      if (!res || !res.ok) {
        showToast((res && res.error) || "Could not duplicate creation");
        return;
      }
      rememberImportedCreation(res.creation);
      renderDocument(res.creation);
      if (mod === "image") await openImageEditor(res.creation, { standalone: true });
      else await openVideoEditor(res.creation, { standalone: true });
      showToast("Opened a copy as basis — Save updates the copy, original stays intact.");
    } catch (err) {
      showToast("Basis failed: " + err);
    } finally {
      endBusy("Ready");
    }
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
    beginBusy("Importing " + modality, "Reading file into Archives…", { delayMs: 0 });
    try {
      const res = await a.import_media_file(modality);
      if (!res || res.cancelled) return;
      if (!res.ok) {
        showToast(res.error || "Import failed");
        return;
      }
      rememberImportedCreation(res.creation);
      renderDocument(res.creation);
      openWindow("viewer");
      if (modality === "image") await openImageEditor(res.creation, { standalone: true });
      else await openVideoEditor(res.creation, { standalone: true });
      showToast(
        (modality === "image" ? "Image" : "Video") +
          " imported — edit as a new Archive item."
      );
      beep(900, 0.05);
    } catch (err) {
      showToast("Import failed: " + err);
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
      }
      showToast("Text imported into Archives");
      beep(900, 0.05);
    } catch (err) {
      showToast("Import failed: " + err);
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
            model: textSel.value,
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

  function closeWindow(id) {
    if (id === "viewer") stopSpeech();
    if (id === "image-edit") {
      imageEdit.sourceImg = null;
      imageEdit.creationId = null;
      imageEdit.crop = null;
      imageEdit.cropDrag = null;
      imageEdit.filters = null;
      imageEdit.rotation = 0;
      if (window.R98ImageEdit) {
        writeImageEditFiltersToUi(window.R98ImageEdit.DEFAULT_FILTERS);
        if ($("#edit-rotation")) $("#edit-rotation").value = 0;
        syncImageEditValueLabels();
      }
    }
    if (id === "video-edit") {
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
      if (!win) return;
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
    const override = ($("#theme-override") && $("#theme-override").value) || "auto";
    if (override !== "auto" && THEMES[override]) {
      return Object.assign({}, THEMES[override]);
    }
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
      // Skip legacy "Response" heading on freeform Text creations
      const hideHeading =
        !secTitle ||
        (secTitle === "Response" && (creation.creationType || "") === "Text");
      html += '<div class="doc-section">';
      if (!hideHeading) {
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
        '<p style="margin-top:16px;font-size:11px;opacity:0.85"><em>' +
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
        const src = res.dataUrl || res.fileUrl || "";
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
      html += "<h3>" + escapeHtml(sec.title || "Section") + "</h3>";
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
    const paletteEl = $("#viewer-palette");
    const boxArtEl = $("#theme-boxart");
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
      if (paletteEl) paletteEl.textContent = "Palette: —";
      if (boxArtEl) boxArtEl.textContent = "";
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

    const autoOpt = $("#theme-override option[value='auto']");
    if (autoOpt) {
      autoOpt.textContent =
        "Auto: " + ((creation.theme && creation.theme.themeName) || "Theme");
    }
    if (boxArtEl) {
      const style =
        (creation.theme && creation.theme.boxArtStyle) || theme.boxArtStyle || "";
      boxArtEl.textContent = style ? "Box art: " + style : "";
      boxArtEl.title = style;
    }

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
    if (paletteEl) paletteEl.textContent = "Palette: " + (theme.themeName || "Custom");

    const tab = state.viewerTab || (modality === "text" ? "doc" : "media");
    canvas.classList.toggle("tab-ascii", tab === "ascii");

    if (modality === "image" || modality === "video") {
      canvas.style.background = "#111";
      canvas.style.color = "#eee";
      canvas.style.fontFamily = FONT_STACKS.sans;
      if (tab === "grounding") {
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
    const meta = c.meta || {};
    const lines = [];
    const title = creationTitle(c);
    lines.push("=".repeat(70));
    lines.push("   RETRO 98 AI CREATOR — " + String(title || "").toUpperCase());
    lines.push(
      "   TYPE: " +
        (c.creationType || creationModality(c)) +
        " | MODALITY: " +
        creationModality(c)
    );
    lines.push("=".repeat(70));
    lines.push("");
    if (c.prompt) {
      lines.push("PROMPT:");
      lines.push(c.prompt);
      lines.push("");
    }
    if (meta.developer || meta.publisher || meta.designer) {
      lines.push("DEVELOPER: " + (meta.developer || "N/A"));
      lines.push("PUBLISHER: " + (meta.publisher || "N/A"));
      lines.push("DESIGNER : " + (meta.designer || "N/A"));
      lines.push("");
    }
    const overview = String(c.overview || "").trim();
    if (overview && !overviewIsTruncatedBody(c)) {
      lines.push("-".repeat(70));
      lines.push("OVERVIEW:");
      lines.push(overview);
      lines.push("-".repeat(70));
      lines.push("");
    }
    (c.sections || []).forEach((s, idx) => {
      const secTitle = String(s.title || "").trim();
      const hideHeading =
        !secTitle ||
        (secTitle === "Response" && (c.creationType || "") === "Text");
      if (!hideHeading) {
        lines.push(
          "[SECTION " + (idx + 1) + ": " + secTitle.toUpperCase() + "]"
        );
      }
      lines.push(s.content || "");
      lines.push("");
      if (s.keyValues && s.keyValues.length) {
        lines.push("KEY VALUES:");
        s.keyValues.forEach((kv) => {
          const label = String(kv.label || "").padEnd(24, " ");
          lines.push("  * " + label + " : " + (kv.value || ""));
        });
        lines.push("");
      }
    });
    lines.push("=".repeat(70));
    if (c.accuracyNote) {
      lines.push("NOTE:");
      lines.push(c.accuracyNote);
      lines.push("=".repeat(70));
    }
    return lines.join("\n");
  }

  function exportBaseName(creation) {
    return creationTitle(creation)
      .replace(/[^\w\-]+/g, "_")
      .replace(/_+/g, "_")
      .slice(0, 60) || "creation";
  }

  async function withUnconstrainedCanvas(fn) {
    const targetEl = $("#doc-canvas");
    if (!targetEl || !window.htmlToImage) {
      throw new Error("Document canvas or html-to-image is unavailable");
    }
    const origMaxHeight = targetEl.style.maxHeight;
    const origOverflow = targetEl.style.overflow;
    const origHeight = targetEl.style.height;
    const origMinHeight = targetEl.style.minHeight;

    targetEl.classList.add("doc-canvas-exporting");
    targetEl.style.maxHeight = "none";
    targetEl.style.overflow = "visible";
    targetEl.style.height = "auto";
    targetEl.style.minHeight = "0";
    // Expand to full content height so html-to-image does not clip to the viewport
    targetEl.scrollTop = 0;
    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve))
    );
    const fullWidth = Math.max(targetEl.scrollWidth, targetEl.offsetWidth, 800);
    const fullHeight = Math.max(targetEl.scrollHeight, targetEl.offsetHeight, 1);
    targetEl.style.height = fullHeight + "px";
    await new Promise((resolve) => requestAnimationFrame(resolve));

    const opts = {
      pixelRatio: 2,
      cacheBust: true,
      backgroundColor:
        (targetEl.style && targetEl.style.backgroundColor) ||
        getComputedStyle(targetEl).backgroundColor ||
        "#ffffff",
      width: fullWidth,
      height: fullHeight,
      style: {
        maxHeight: "none",
        overflow: "visible",
        height: fullHeight + "px",
        width: fullWidth + "px",
      },
    };

    try {
      return await fn(targetEl, opts);
    } finally {
      targetEl.classList.remove("doc-canvas-exporting");
      targetEl.style.maxHeight = origMaxHeight;
      targetEl.style.overflow = origOverflow;
      targetEl.style.height = origHeight;
      targetEl.style.minHeight = origMinHeight;
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

    showToast(format === "pdf" ? "Building PDF…" : "Capturing PNG…");
    try {
      const base = exportBaseName(state.active);
      if (format === "png") {
        const pngDataUrl = await withUnconstrainedCanvas((el, opts) =>
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

      const canvas = await withUnconstrainedCanvas((el, opts) =>
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

  function renderArchives() {
    const q = ($("#archive-search").value || "").toLowerCase();
    const list = $("#archive-list");
    list.innerHTML = "";
    state.creations
      .filter(
        (c) =>
          !q ||
          (c.game || "").toLowerCase().includes(q) ||
          (c.title || "").toLowerCase().includes(q) ||
          (c.prompt || "").toLowerCase().includes(q) ||
          (c.creationType || "").toLowerCase().includes(q) ||
          (c.platform || "").toLowerCase().includes(q)
      )
      .forEach((c) => {
        const li = document.createElement("li");
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.className = "arch-open";
        openBtn.textContent =
          creationTitle(c) +
          " — " +
          (c.creationType || creationModality(c)) +
          (c.createdAt ? " · " + formatCreatedAt(c.createdAt) : "");
        openBtn.addEventListener("click", () => {
          renderDocument(c);
          beep(700, 0.04);
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
        const basis = document.createElement("button");
        basis.type = "button";
        basis.textContent = "Basis";
        basis.title = "Use as basis for a new " + creationModality(c);
        basis.addEventListener("click", () => {
          useCreationAsBasis(c);
        });
        li.appendChild(openBtn);
        li.appendChild(basis);
        li.appendChild(del);
        list.appendChild(li);
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
        opt.textContent = m.label + (m.notes ? " — " + m.notes : "");
        opt.dataset.modality = m.modality || key;
        og.appendChild(opt);
      });
      sel.appendChild(og);
    });
    if (selected && ![...sel.options].some((o) => o.value === selected)) {
      const opt = document.createElement("option");
      opt.value = selected;
      opt.textContent = selected;
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
    filtered.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.repo_id;
      opt.textContent = m.label + (m.notes ? " — " + m.notes : "");
      opt.dataset.modality = want;
      sel.appendChild(opt);
    });
    let pick = selected || defaults[want] || "";
    if (pick && ![...sel.options].some((o) => o.value === pick)) {
      const opt = document.createElement("option");
      opt.value = pick;
      opt.textContent = pick + " (saved)";
      opt.dataset.modality = want;
      sel.appendChild(opt);
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

    const tabDoc = $("#tab-doc");
    const tabMedia = $("#tab-media");
    const tabGrounding = $("#tab-grounding");
    const tabPrint = $("#tab-print");
    const tabAscii = $("#tab-ascii");
    if (tabDoc) tabDoc.hidden = isMedia;
    if (tabMedia) {
      tabMedia.hidden = !isMedia;
      tabMedia.textContent = modality === "video" ? "Video" : "Image";
    }
    if (tabPrint) tabPrint.hidden = isMedia || !creation;
    if (tabAscii) tabAscii.hidden = isMedia || !creation;
    if (tabGrounding) {
      const sources = (creation && creation.groundingSources) || [];
      tabGrounding.hidden = !creation || (isMedia && !sources.length);
    }

    const showTxt = modality === "text";
    const showPng = modality === "text" || modality === "image";
    const showPdf = modality === "text" || modality === "image";
    const showMp4 = modality === "video";
    const showAscii = modality === "text";
    const showVoice = modality === "text";
    const showTheme = modality === "text";
    const showEditImage = modality === "image";
    const showEditVideo = modality === "video";
    const showMetadata = !!creation;

    if ($("#btn-export-txt")) $("#btn-export-txt").hidden = !showTxt;
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
    if ($("#btn-edit-image")) $("#btn-edit-image").hidden = !showEditImage;
    if ($("#btn-edit-video")) $("#btn-edit-video").hidden = !showEditVideo;
    if ($("#btn-copy-ascii")) $("#btn-copy-ascii").hidden = !showAscii;
    if ($("#btn-voice")) $("#btn-voice").hidden = !showVoice;
    if ($("#btn-export-json")) {
      $("#btn-export-json").hidden = !showMetadata;
      $("#btn-export-json").textContent = "Export Metadata";
    }

    const themeBar = document.querySelector(".viewer-theme-bar");
    if (themeBar) themeBar.hidden = !showTheme;

    if (isMedia && (state.viewerTab === "doc" || state.viewerTab === "print" || state.viewerTab === "ascii")) {
      state.viewerTab = "media";
    }
    if (!isMedia && state.viewerTab === "media") {
      state.viewerTab = "doc";
    }
  }

  function fillControlPanel(boot) {
    if (boot && boot.config) state.config = boot.config;
    const model = (boot.config && boot.config.model) || {};
    const gemini = (boot.config && boot.config.gemini) || {};
    const openrouter = (boot.config && boot.config.openrouter) || {};
    const backend = (boot.config && boot.config.backend) || {};
    const ui = (boot.config && boot.config.ui) || {};
    const gen = (boot.config && boot.config.generation) || {};

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
      gemini.text_model || gemini.model || "gemini-2.5-flash",
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
    fillModelSelect(
      $("#openrouter-model"),
      openrouter.model || "google/gemini-2.5-flash",
      boot.suggestedOpenRouterModels || []
    );

    updateApiKeyIndicators();

    fillModelSelect(
      $("#model-repo"),
      model.repo_id || "microsoft/Phi-3.5-mini-instruct",
      boot.suggestedModels || []
    );
    if ($("#model-device")) $("#model-device").value = model.device || "auto";
    if ($("#model-dtype")) $("#model-dtype").value = model.torch_dtype || "auto";
    if ($("#model-tokens")) $("#model-tokens").value = model.max_new_tokens || 2048;
    if ($("#model-temp")) $("#model-temp").value = model.temperature ?? 0;
    if ($("#model-token")) $("#model-token").value = model.hf_token || "";
    if ($("#system-extra")) $("#system-extra").value = gen.system_extra || "";
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
    state.defaultPlatform = ui.default_platform || "";
    state.defaultTheme = ui.default_theme || "auto";
    const custom = ui.custom_theme || {};
    state.customTheme = {
      desktopColor: normalizeHexColor(custom.desktop_color, "#008080"),
      windowColor: normalizeHexColor(custom.window_color, "#c0c0c0"),
      titleColor: normalizeHexColor(custom.title_color, "#000080"),
      textColor: normalizeHexColor(custom.text_color, "#222222"),
      font: resolveCustomFontKey(custom.font || "sans"),
    };
    writeCustomThemeToControls(state.customTheme);
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
    const statusMod =
      (boot && boot.modelStatus && boot.modelStatus.modality) ||
      (state.config && state.config._modality) ||
      "";
    const modLabel = statusMod
      ? String(statusMod).charAt(0).toUpperCase() + String(statusMod).slice(1)
      : "";
    if (provider === "huggingface") {
      const repo =
        (boot && boot.config && boot.config.model && boot.config.model.repo_id) ||
        ($("#model-repo") && $("#model-repo").value) ||
        "local HF";
      modelField.textContent =
        "Backend: Hugging Face · " + repo + (modLabel ? " · " + modLabel : "");
    } else if (provider === "openrouter") {
      const model =
        (boot && boot.config && boot.config.openrouter && boot.config.openrouter.model) ||
        ($("#openrouter-model") && $("#openrouter-model").value) ||
        "google/gemini-2.5-flash";
      modelField.textContent =
        "Backend: OpenRouter · " + model + (modLabel ? " · " + modLabel : " · Text");
    } else {
      const g =
        (boot && boot.config && boot.config.gemini) ||
        (state.config && state.config.gemini) ||
        {};
      const textM =
        g.text_model ||
        ($("#gemini-text-model") && $("#gemini-text-model").value) ||
        g.model ||
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
      if (selected === "gemini" && providerChanged) {
        geminiStatus.textContent =
          "Provider changed — paste a Gemini API key before saving.";
      } else if (geminiSet) {
        geminiStatus.textContent =
          "A Gemini API key is already saved. Leave the field blank to keep it.";
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
      if (selected === "openrouter" && providerChanged) {
        orStatus.textContent =
          "Provider changed — paste an OpenRouter API key before saving.";
      } else if (openrouterSet) {
        orStatus.textContent =
          "An OpenRouter API key is already saved. Leave the field blank to keep it.";
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

    // Switching providers always requires pasting a key for the new provider.
    if (provider !== savedBackendProvider()) {
      return !!typed;
    }

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
      model: text,
    };
  }

  function collectSettings(reload) {
    const provider = ($("#backend-provider") && $("#backend-provider").value) || "gemini";
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
        model:
          ($("#gemini-text-model") && $("#gemini-text-model").value.trim()) ||
          "gemini-2.5-flash",
        api_key: ($("#gemini-key") && $("#gemini-key").value.trim()) || "",
        google_search: $("#gemini-search") ? $("#gemini-search").checked : true,
        two_pass_verify: $("#gemini-two-pass") ? $("#gemini-two-pass").checked : true,
        temperature: $("#gemini-temp") ? Number($("#gemini-temp").value) || 0 : 0,
      },
      openrouter: {
        model:
          ($("#openrouter-model") && $("#openrouter-model").value.trim()) ||
          "google/gemini-2.5-flash",
        api_key: ($("#openrouter-key") && $("#openrouter-key").value.trim()) || "",
        temperature: $("#openrouter-temp")
          ? Number($("#openrouter-temp").value) || 0
          : 0,
      },
      model: {
        repo_id: ($("#model-repo") && $("#model-repo").value.trim()) || "microsoft/Phi-3.5-mini-instruct",
        device: ($("#model-device") && $("#model-device").value) || "auto",
        torch_dtype: ($("#model-dtype") && $("#model-dtype").value) || "auto",
        max_new_tokens: ($("#model-tokens") && Number($("#model-tokens").value)) || 2048,
        temperature: ($("#model-temp") && Number($("#model-temp").value)) || 0,
        hf_token: ($("#model-token") && $("#model-token").value.trim()) || null,
        trust_remote_code: false,
      },
      generation: {
        system_extra: ($("#system-extra") && $("#system-extra").value) || "",
      },
      ui: {
        sound_enabled: $("#opt-sound").checked,
        crt_enabled: $("#opt-crt").checked,
        ui_scale: readUiScaleFromControl(),
        default_platform: state.defaultPlatform || null,
        default_theme: state.defaultTheme || "auto",
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
            font: c.font,
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
    requestAnimationFrame(() => syncDesktopScrollExtent());
  }

  function applyDisplaySettingsFromControls() {
    state.soundEnabled = $("#opt-sound").checked;
    state.crtEnabled = $("#opt-crt").checked;
    $("#crt-overlay").hidden = !state.crtEnabled;
    applyUiScale(readUiScaleFromControl());
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
    const sel = $("#theme-override");
    if (sel) {
      const match = [...sel.options].find((o) => o.value === themeKey);
      if (match) return match.textContent;
    }
    return themeKey;
  }

  function updateStudioThemeField() {
    const el = $("#studio-theme-field");
    if (!el) return;
    el.textContent = "Theme Engine: " + themeDisplayName(state.defaultTheme || "auto");
  }

  function applyGameDefaults(opts) {
    opts = opts || {};
    const platform = state.defaultPlatform || "";
    const themeKey = state.defaultTheme || "auto";

    if (opts.applyPlatform !== false && platform) {
      setStudioPlatform(platform);
      syncCreationDescription();
    }

    if (opts.applyTheme !== false) {
      if ($("#theme-override")) {
        $("#theme-override").value = themeKey;
      }
      if (state.active) renderDocument(state.active);
    }

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
    if (payload && typeof payload === "object") {
      message = payload.message || payload.detail || "";
      if (payload.percent != null) percent = payload.percent;
      if (payload.title) title = payload.title;
      if (payload.phase === "download") title = title || "Downloading model";
      if (payload.phase === "load") title = title || "Loading model";
      if (payload.phase === "generate") title = title || "Generating document";
    } else {
      message = String(payload || "");
    }
    if (title) busy.title = title;
    updateBusy(message, percent);
  };

  function applyGenerationResult(creation) {
    if (!creation) return;
    // Idempotent — poll and evaluate_js may both fire
    if (state._lastHandledId === creation.id) return;
    state._lastHandledId = creation.id;

    state.generating = false;
    setCreateBlocked(false);
    endBusy("Ready");
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
        } else {
          finishModelDownload(false, job.error || "Model load failed");
        }
        return;
      }

      await sleep(500);
    }

    if (kind === "generate") {
      applyGenerationError("Timed out waiting for generation.");
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

      // Preflight: image/video prompts on text models (and reverse) stop here
      try {
        if (typeof a.check_modality_match === "function") {
          const compat = await a.check_modality_match(prompt);
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
      beginBusy("Generating", "Calling Gemini / backend…", {
        delayMs: 0,
        cancellable: true,
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
          creationDescription
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
          ? "Generating for selected title…"
          : "Job started — loading model / generating…"
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
    raf: 0,
  };

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
    if ($("#btn-edit-save-as")) $("#btn-edit-save-as").hidden = !imageEdit.standalone;
    const hint = $("#image-edit-hint");
    if (hint) {
      hint.textContent = imageEdit.standalone
        ? "Load an image to begin. At 0° rotation, drag to set a crop. Save writes Archives; Save As… exports a file."
        : "At 0° rotation, drag on the image to set a crop (yellow box; outside dims). Clear Crop to reset. Apply saves to this creation.";
    }
  }

  function prepareEmptyImageEditor() {
    imageEdit.sourceImg = null;
    imageEdit.creationId = null;
    imageEdit.standalone = true;
    imageEdit.crop = null;
    imageEdit.cropDrag = null;
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

  async function loadImageIntoEditorFromActive() {
    if (!state.active || creationModality(state.active) !== "image") {
      showToast("Open an image in the Viewer first, or Load Image…");
      return;
    }
    await useCreationAsBasis(state.active);
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
  function imageEditClientToSourcePixels(clientX, clientY) {
    const canvas = $("#image-edit-canvas");
    const img = imageEdit.sourceImg;
    if (!canvas || !img) return null;
    const rect = canvas.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return null;
    const sw = img.naturalWidth || img.width || canvas.width;
    const sh = img.naturalHeight || img.height || canvas.height;
    const nx = (clientX - rect.left) / rect.width;
    const ny = (clientY - rect.top) / rect.height;
    if (nx < 0 || ny < 0 || nx > 1 || ny > 1) return null;
    return {
      x: Math.min(sw, Math.max(0, nx * sw)),
      y: Math.min(sh, Math.max(0, ny * sh)),
      sw: sw,
      sh: sh,
    };
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

  async function openImageEditor(creation, opts) {
    opts = opts || {};
    if (!creation || creationModality(creation) !== "image") {
      showToast("Edit is available for image creations.");
      return;
    }
    if (!window.R98ImageEdit) {
      showToast("Image edit module failed to load.");
      return;
    }
    const a = api();
    if (!a) {
      showToast("Python bridge required to edit images.");
      return;
    }
    const payload = await a.get_media_payload(creation);
    if (!payload || !payload.ok || !payload.dataUrl) {
      showToast((payload && payload.error) || "Could not load image.");
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
    imageEdit.standalone = typeof opts.standalone === "boolean" ? opts.standalone : true;
    imageEdit.crop = null;
    imageEdit.cropDrag = null;
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
  }

  function resetImageEditor() {
    if (!window.R98ImageEdit) return;
    imageEdit.filters = Object.assign({}, window.R98ImageEdit.DEFAULT_FILTERS);
    imageEdit.crop = null;
    imageEdit.rotation = 0;
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
      const pt = imageEditClientToSourcePixels(e.clientX, e.clientY);
      if (!pt) return;
      imageEdit.cropDrag = {
        x0: pt.x,
        y0: pt.y,
        pointerId: e.pointerId,
      };
      // Tiny seed rect so overlay appears immediately
      imageEdit.crop = { x: pt.x, y: pt.y, w: 1, h: 1 };
      updateCropBoxOverlay();
      stage.setPointerCapture(e.pointerId);
      e.preventDefault();
    });

    stage.addEventListener("pointermove", (e) => {
      if (!imageEdit.cropDrag || e.pointerId !== imageEdit.cropDrag.pointerId) return;
      const canvasEl = $("#image-edit-canvas");
      if (!canvasEl || !imageEdit.sourceImg) return;
      const rect = canvasEl.getBoundingClientRect();
      const sw =
        imageEdit.sourceImg.naturalWidth ||
        imageEdit.sourceImg.width ||
        canvasEl.width;
      const sh =
        imageEdit.sourceImg.naturalHeight ||
        imageEdit.sourceImg.height ||
        canvasEl.height;
      // Clamp to canvas bounds while dragging (unlike pointerdown miss)
      const nx = Math.min(1, Math.max(0, (e.clientX - rect.left) / Math.max(1, rect.width)));
      const ny = Math.min(1, Math.max(0, (e.clientY - rect.top) / Math.max(1, rect.height)));
      const x1 = nx * sw;
      const y1 = ny * sh;
      const x0 = imageEdit.cropDrag.x0;
      const y0 = imageEdit.cropDrag.y0;
      imageEdit.crop = {
        x: Math.min(x0, x1),
        y: Math.min(y0, y1),
        w: Math.max(1, Math.abs(x1 - x0)),
        h: Math.max(1, Math.abs(y1 - y0)),
      };
      updateCropBoxOverlay();
    });

    const endDrag = (e) => {
      if (!imageEdit.cropDrag || e.pointerId !== imageEdit.cropDrag.pointerId) return;
      imageEdit.cropDrag = null;
      try {
        stage.releasePointerCapture(e.pointerId);
      } catch (_) {
        /* ignore */
      }
      // Drop accidental clicks (no real drag)
      if (
        imageEdit.crop &&
        (imageEdit.crop.w < 2 || imageEdit.crop.h < 2)
      ) {
        imageEdit.crop = null;
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
        openImageEditor(state.active, { standalone: false });
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
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
      // Some WebView hosts fire change more reliably than input on ranges
      el.addEventListener("change", () => {
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
    });
    ["edit-grayscale", "edit-threshold", "edit-sharpen", "edit-bg-remove", "edit-bg-edges"].forEach(
      (id) => {
        const el = $("#" + id);
        if (!el) return;
        el.addEventListener("change", () => {
          syncBgRemoveRows();
          scheduleImageEditPreview();
        });
      }
    );
    if ($("#btn-edit-rot-cw")) {
      $("#btn-edit-rot-cw").addEventListener("click", () => {
        const cur = Number($("#edit-rotation").value) || 0;
        $("#edit-rotation").value = String((cur + 90) % 360);
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
    }
    if ($("#btn-edit-rot-ccw")) {
      $("#btn-edit-rot-ccw").addEventListener("click", () => {
        const cur = Number($("#edit-rotation").value) || 0;
        $("#edit-rotation").value = String((cur + 270) % 360);
        syncImageEditValueLabels();
        scheduleImageEditPreview();
      });
    }
    if ($("#btn-edit-crop-clear")) {
      $("#btn-edit-crop-clear").addEventListener("click", () => {
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
        closeImageEditor();
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
    raf: 0,
    showFilterPreview: false,
  };

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
    if ($("#btn-vedit-save-as")) $("#btn-vedit-save-as").hidden = !videoEdit.standalone;
    const hint = $("#video-edit-hint");
    if (hint) {
      hint.textContent = videoEdit.standalone
        ? "Load a video to begin. Filters preview on the current frame. Save writes Archives; Save As… exports MP4 (ffmpeg required)."
        : "Filters preview on the current frame. Apply rebuilds the video with your segment order and filters (requires ffmpeg on PATH). Drag a paused frame (0°) to crop. Timeline starts at 0.00s.";
    }
  }

  function prepareEmptyVideoEditor() {
    resetVideoEditRuntime();
    videoEdit.standalone = true;
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

  async function loadVideoIntoEditorFromActive() {
    if (!state.active || creationModality(state.active) !== "video") {
      showToast("Open a video in the Viewer first, or Load Video…");
      return;
    }
    await useCreationAsBasis(state.active);
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
  }

  function resetVideoEditRuntime() {
    clearVideoFilterPreview();
    const player = $("#video-edit-player");
    if (player) {
      player.pause();
      player.onloadedmetadata = null;
      player.ontimeupdate = null;
      player.onpause = null;
      player.onseeked = null;
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
    if (window.R98ImageEdit) {
      writeVideoEditFiltersToUi(window.R98ImageEdit.DEFAULT_FILTERS);
    }
    if ($("#vedit-rotation")) $("#vedit-rotation").value = 0;
    syncVideoEditValueLabels();
    const track = $("#vedit-timeline-track");
    if (track) track.innerHTML = "";
    const summary = $("#vedit-segments-summary");
    if (summary) summary.textContent = "No segments";
  }

  function closeVideoEditor() {
    closeWindow("video-edit");
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

  /** During playback, stay inside segments in edit order (skip deletes / honor reorder). */
  function advanceEditedPlayback() {
    const player = $("#video-edit-player");
    if (!player || player.paused || !videoEdit.segments.length) return;
    const segs = videoEdit.segments;
    let idx = videoEdit.playSegIdx;
    if (idx < 0 || idx >= segs.length) {
      idx = findSegmentIndexAtTime(player.currentTime);
      if (idx < 0) idx = 0;
      videoEdit.playSegIdx = idx;
    }
    const seg = segs[idx];
    const t = player.currentTime;
    if (t < seg.start - 0.02) {
      player.currentTime = seg.start;
      return;
    }
    if (t >= seg.end - 0.04) {
      const next = idx + 1;
      if (next >= segs.length) {
        player.pause();
        videoEdit.playSegIdx = 0;
        if ($("#btn-vedit-pause")) $("#btn-vedit-pause").textContent = "Play";
        scheduleVideoFilterPreview();
        return;
      }
      videoEdit.playSegIdx = next;
      player.currentTime = segs[next].start;
    }
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
    const apiEdit = window.R98ImageEdit;
    const player = $("#video-edit-player");
    const canvas = $("#video-edit-preview-canvas");
    const stage = $("#video-edit-stage");
    if (!apiEdit || !player || !canvas || !stage || !videoEdit.creationId) return;

    const filters = readVideoEditFiltersFromUi();
    videoEdit.rotation = Number($("#vedit-rotation") && $("#vedit-rotation").value) || 0;
    const active =
      apiEdit.hasActiveFilters(filters) ||
      !!videoEdit.crop ||
      !!videoEdit.rotation;

    if (!active || player.readyState < 2) {
      videoEdit.showFilterPreview = false;
      stage.classList.remove("previewing-filters");
      canvas.hidden = true;
      updateVideoCropOverlay();
      return;
    }

    // Grab current frame → apply image pipeline for approximate preview
    const vw = player.videoWidth || 0;
    const vh = player.videoHeight || 0;
    if (vw < 2 || vh < 2) return;

    const frame = document.createElement("canvas");
    frame.width = vw;
    frame.height = vh;
    const fctx = frame.getContext("2d");
    try {
      fctx.drawImage(player, 0, 0, vw, vh);
    } catch (_) {
      return;
    }

    const img = new Image();
    img.onload = () => {
      const cropPx = videoEdit.crop
        ? {
            x: videoEdit.crop.x * vw,
            y: videoEdit.crop.y * vh,
            w: videoEdit.crop.w * vw,
            h: videoEdit.crop.h * vh,
          }
        : null;
      // Preview at 0° uses overlay for crop; bake crop only when rotated
      const previewCrop = videoEdit.rotation ? cropPx : null;
      const out = apiEdit.renderEditedCanvas(
        img,
        filters,
        previewCrop,
        videoEdit.rotation
      );
      canvas.width = out.width;
      canvas.height = out.height;
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(out, 0, 0);
      canvas.hidden = false;
      videoEdit.showFilterPreview = true;
      stage.classList.add("previewing-filters");
      updateVideoCropOverlay();
    };
    img.src = frame.toDataURL("image/jpeg", 0.85);
  }

  function updateVideoCropOverlay() {
    const box = $("#video-edit-crop-box");
    const stage = $("#video-edit-stage");
    const player = $("#video-edit-player");
    const canvas = $("#video-edit-preview-canvas");
    if (!box || !stage) return;
    const crop = videoEdit.crop;
    if (!crop || videoEdit.rotation) {
      box.hidden = true;
      return;
    }
    const target =
      videoEdit.showFilterPreview && canvas && !canvas.hidden ? canvas : player;
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
      return;
    }
    const a = api();
    if (!a) {
      showToast("Python bridge required to edit videos.");
      return;
    }
    const status = await a.ffmpeg_status();
    if (!status || !status.ok) {
      showToast(
        (status && status.error) ||
          "ffmpeg not found. Install ffmpeg and add it to PATH."
      );
      return;
    }

    const payload = await a.get_media_payload(creation);
    if (!payload || !payload.ok || !payload.fileUrl) {
      showToast((payload && payload.error) || "Could not load video.");
      return;
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
      };
      player.ontimeupdate = () => updateVideoEditTimeLabel();
      player.onpause = () => scheduleVideoFilterPreview();
      player.onseeked = () => scheduleVideoFilterPreview();
    }

    renderVideoSegments();
    setVideoEditLoadedLabel(creation);
    syncVideoEditChrome();
    openWindow("video-edit");
    scheduleVideoFilterPreview();
    beep(700, 0.04);
  }

  function resetVideoEditor() {
    writeVideoEditFiltersToUi(
      (window.R98ImageEdit && window.R98ImageEdit.DEFAULT_FILTERS) || {}
    );
    videoEdit.crop = null;
    videoEdit.rotation = 0;
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
      const target =
        videoEdit.showFilterPreview && $("#video-edit-preview-canvas")
          ? $("#video-edit-preview-canvas")
          : player;
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
      const target =
        videoEdit.showFilterPreview && $("#video-edit-preview-canvas")
          ? $("#video-edit-preview-canvas")
          : player;
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
      scheduleVideoFilterPreview();
    };
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);
  }

  function wireVideoEditEvents() {
    if ($("#btn-edit-video")) {
      $("#btn-edit-video").addEventListener("click", () => {
        openVideoEditor(state.active, { standalone: false });
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
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
      el.addEventListener("change", () => {
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
    });
    ["vedit-grayscale", "vedit-sharpen"].forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      el.addEventListener("change", () => scheduleVideoFilterPreview());
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
    if ($("#btn-vedit-pause")) {
      $("#btn-vedit-pause").addEventListener("click", () => {
        const player = $("#video-edit-player");
        if (!player) return;
        if (player.paused) {
          let idx = findSegmentIndexAtTime(player.currentTime);
          if (idx < 0 && videoEdit.segments.length) {
            idx = 0;
            player.currentTime = videoEdit.segments[0].start;
          }
          videoEdit.playSegIdx = Math.max(0, idx);
          player.play();
          $("#btn-vedit-pause").textContent = "Pause";
        } else {
          player.pause();
          $("#btn-vedit-pause").textContent = "Play";
          scheduleVideoFilterPreview();
        }
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
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
    }
    if ($("#btn-vedit-rot-ccw")) {
      $("#btn-vedit-rot-ccw").addEventListener("click", () => {
        const cur = Number($("#vedit-rotation").value) || 0;
        $("#vedit-rotation").value = String((cur + 270) % 360);
        syncVideoEditValueLabels();
        scheduleVideoFilterPreview();
      });
    }
    if ($("#btn-vedit-crop-clear")) {
      $("#btn-vedit-crop-clear").addEventListener("click", () => {
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
      $("#btn-vedit-cancel").addEventListener("click", () => closeVideoEditor());
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
        if (a === "close") closeWindow(id);
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
    if ($("#btn-iedit-from-active")) {
      $("#btn-iedit-from-active").addEventListener("click", () =>
        loadImageIntoEditorFromActive()
      );
    }
    if ($("#btn-vedit-load")) {
      $("#btn-vedit-load").addEventListener("click", () =>
        loadVideoIntoEditorFromFile()
      );
    }
    if ($("#btn-vedit-from-active")) {
      $("#btn-vedit-from-active").addEventListener("click", () =>
        loadVideoIntoEditorFromActive()
      );
    }

    if ($("#busy-cancel")) {
      $("#busy-cancel").addEventListener("click", () => {
        requestCancelBusyJob();
      });
    }

    $("#archive-search").addEventListener("input", renderArchives);

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
        studioLoadMediaFile("image")
      );
    }
    if ($("#btn-import-video")) {
      $("#btn-import-video").addEventListener("click", () =>
        studioLoadMediaFile("video")
      );
    }

    $("#btn-export-txt").addEventListener("click", async () => {
      if (!state.active) return;
      if (creationModality(state.active) !== "text") {
        showToast("TXT export is for text creations only.");
        return;
      }
      const a = api();
      if (!a) return;
      try {
        const txt = await a.export_creation_txt(state.active);
        const name = exportBaseName(state.active) + ".txt";
        await a.save_file_dialog(name, txt);
      } catch (err) {
        showToast(String(err));
      }
    });

    $("#btn-export-json").addEventListener("click", async () => {
      if (!state.active) return;
      const a = api();
      if (!a) return;
      const name = exportBaseName(state.active) + ".json";
      await a.save_file_dialog(name, JSON.stringify(state.active, null, 2));
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

    $("#theme-override").addEventListener("change", () => {
      if (state.active) renderDocument(state.active);
    });

    if ($("#model-repo")) {
      $("#model-repo").addEventListener("change", () => {
        updateStudioBackendLabel({
          config: {
            backend: {
              provider:
                ($("#backend-provider") && $("#backend-provider").value) ||
                "huggingface",
            },
            gemini: currentGeminiUiConfig(),
            openrouter: {
              model:
                ($("#openrouter-model") && $("#openrouter-model").value) || "",
            },
            model: { repo_id: $("#model-repo").value },
          },
        });
      });
    }

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
              openrouter: {
                model:
                  ($("#openrouter-model") && $("#openrouter-model").value) || "",
              },
              model: {
                repo_id: ($("#model-repo") && $("#model-repo").value) || "",
              },
            },
          });
        });
      }
    );

    if ($("#openrouter-model")) {
      $("#openrouter-model").addEventListener("change", () => {
        updateStudioBackendLabel({
          config: {
            backend: {
              provider:
                ($("#backend-provider") && $("#backend-provider").value) ||
                "openrouter",
            },
            gemini: currentGeminiUiConfig(),
            openrouter: { model: $("#openrouter-model").value },
            model: {
              repo_id: ($("#model-repo") && $("#model-repo").value) || "",
            },
          },
        });
      });
    }

    if ($("#backend-provider")) {
      $("#backend-provider").addEventListener("change", () => {
        syncBackendPanels();
        updateApiKeyIndicators();
        updateStudioBackendLabel({
          config: {
            backend: { provider: $("#backend-provider").value },
            gemini: currentGeminiUiConfig(),
            openrouter: {
              model: ($("#openrouter-model") && $("#openrouter-model").value) || "",
            },
            model: { repo_id: ($("#model-repo") && $("#model-repo").value) || "" },
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
    [
      "custom-desktop-color",
      "custom-window-color",
      "custom-title-color",
      "custom-text-color",
      "custom-ui-font",
    ].forEach((id) => {
      const el = $("#" + id);
      if (!el) return;
      const evt = id === "custom-ui-font" ? "change" : "input";
      el.addEventListener(evt, () => {
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
    applyAppTheme(state.appTheme || "light");
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
