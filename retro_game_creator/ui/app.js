/* global pywebview, RGC_CATALOG */

(function () {
  "use strict";

  const state = {
    creations: [],
    active: null,
    focused: "form",
    open: { form: true, viewer: true, library: false, control: false },
    minimized: { form: false, viewer: false, library: false, control: false },
    generating: false,
    soundEnabled: true,
    crtEnabled: false,
    uiScale: 1,
    config: null,
    viewerTab: "doc",
    speechPlaying: false,
    controlTab: "ai",
    presets: [],
    defaultPreset: "",
    defaultTheme: "auto",
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

  // Back-compat aliases for older saved UI selections
  THEMES.amiga = THEMES.workbench;
  THEMES.dos = THEMES["dos-vga"];
  THEMES.xbox = THEMES["xbox-original"];


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

  function showToast(msg) {
    const el = $("#error-toast");
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => {
      el.hidden = true;
    }, 5000);
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
  };

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

  function _showBusyNow(title, message, percent) {
    const overlay = $("#busy-overlay");
    if (!overlay) return;
    $("#busy-title").textContent = title || "Please wait…";
    $("#busy-message").textContent = message || "Working…";
    overlay.hidden = false;
    busy.visible = true;
    if (!busy.startedAt) busy.startedAt = Date.now();
    if (!busy.elapsedTimer) {
      updateBusyElapsed();
      busy.elapsedTimer = setInterval(updateBusyElapsed, 500);
    }
    setBusyPercent(percent);
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
   */
  function beginBusy(title, message, opts) {
    opts = opts || {};
    const delayMs = opts.delayMs != null ? opts.delayMs : 1500;
    busy.title = title || "Please wait…";
    clearTimeout(busy.showTimer);
    setProgress(message || title || "Working…");

    if (delayMs <= 0) {
      _showBusyNow(busy.title, message, opts.percent);
      return;
    }

    // If already visible, just update
    if (busy.visible) {
      $("#busy-title").textContent = busy.title;
      $("#busy-message").textContent = message || "Working…";
      if ("percent" in opts) setBusyPercent(opts.percent);
      return;
    }

    busy.startedAt = Date.now();
    busy.showTimer = setTimeout(() => {
      _showBusyNow(busy.title, message, opts.percent);
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
    const overlay = $("#busy-overlay");
    if (overlay) overlay.hidden = true;
    setProgress(finalMessage || "Ready");
  }

  function syncPlatformSelect() {
    const input = $("#platform-input");
    const sel = $("#platform-select");
    if (!input || !sel) return;
    const val = input.value;
    const match = Array.from(sel.options).some((o) => o.value === val);
    sel.value = match ? val : "";
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
  }

  function closeWindow(id) {
    if (id === "viewer") stopSpeech();
    state.open[id] = false;
    state.minimized[id] = false;
    const el = document.getElementById("win-" + id);
    if (el) {
      el.hidden = true;
      el.classList.remove("minimized");
    }
    renderTaskbar();
    beep(440, 0.04);
  }

  function minimizeWindow(id) {
    state.minimized[id] = true;
    const el = document.getElementById("win-" + id);
    if (el) el.classList.add("minimized");
    renderTaskbar();
    beep(520, 0.03);
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

  function renderTaskbar() {
    const host = $("#taskbar-windows");
    if (!host) return;
    host.innerHTML = "";
    const titles = {
      form: "Creation Studio",
      viewer: state.active ? "Viewer — " + state.active.game : "Viewer",
      library: "Retro Archives",
      control: "Control Panel",
    };
    ["form", "viewer", "library", "control"].forEach((id) => {
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

  function renderDocTab(creation, theme) {
    const meta = creation.meta || {};
    let html = "";
    html +=
      '<div class="doc-header" style="background:' +
      escapeHtml(theme.headerBg || "#000080") +
      ';color:#fff;padding:8px 10px;margin:-12px -12px 12px;">';
    html += "<h2>" + escapeHtml(creation.game) + "</h2>";
    html +=
      "<div>" +
      escapeHtml(creation.creationType) +
      " — " +
      escapeHtml(creation.platform) +
      "</div></div>";

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
    html += "<p>" + escapeHtml(creation.overview || "") + "</p>";

    (creation.sections || []).forEach((sec) => {
      html += '<div class="doc-section">';
      html +=
        '<h3 style="color:' +
        escapeHtml(theme.accentColor || "#000080") +
        '">' +
        escapeHtml(sec.title || "Section") +
        "</h3>";
      html += "<p>" + escapeHtml(sec.content || "") + "</p>";
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
        '<p class="muted">Open a document from Archives or generate a new one.</p>';
      $("#viewer-title").textContent = "Viewer";
      $("#viewer-status").textContent = "No document loaded";
      if (paletteEl) paletteEl.textContent = "Palette: —";
      if (boxArtEl) boxArtEl.textContent = "";
      if (groundingTab) groundingTab.textContent = "Sources (0)";
      renderTaskbar();
      return;
    }

    const theme = resolveTheme(creation);
    const sources = creation.groundingSources || [];
    if (groundingTab) groundingTab.textContent = "Sources (" + sources.length + ")";

    const autoOpt = $("#theme-override option[value='auto']");
    if (autoOpt) {
      autoOpt.textContent =
        "Auto: " + ((creation.theme && creation.theme.themeName) || "Box Art Theme");
    }
    if (boxArtEl) {
      const style =
        (creation.theme && creation.theme.boxArtStyle) || theme.boxArtStyle || "";
      boxArtEl.textContent = style ? "Box art: " + style : "";
      boxArtEl.title = style;
    }

    $("#viewer-title").textContent = "Viewer — " + (creation.game || "Untitled");
    const model = (creation._model && creation._model.repo_id) || "local model";
    const created = formatCreatedAt(creation.createdAt);
    $("#viewer-status").textContent =
      creation.creationType +
      " · " +
      (creation.platform || "") +
      " · " +
      model +
      (created ? " · " + created : "");
    if (paletteEl) paletteEl.textContent = "Palette: " + (theme.themeName || "Custom");

    const tab = state.viewerTab || "doc";
    canvas.classList.toggle("tab-ascii", tab === "ascii");

    if (tab === "ascii") {
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
    lines.push("=".repeat(70));
    lines.push("   OFFICIAL RETRO GAME ARCHIVE - " + String(c.game || "").toUpperCase());
    lines.push(
      "   PLATFORM: " +
        (c.platform || "") +
        " | YEAR: " +
        (meta.releaseYear || "N/A")
    );
    lines.push("   CREATION: " + String(c.creationType || "").toUpperCase());
    lines.push("=".repeat(70));
    lines.push("");
    lines.push("DEVELOPER: " + (meta.developer || "N/A"));
    lines.push("PUBLISHER: " + (meta.publisher || "N/A"));
    lines.push("DESIGNER : " + (meta.designer || "N/A"));
    lines.push("SYSTEM   : " + (meta.systemRequirements || c.platform || "N/A"));
    lines.push("");
    lines.push("-".repeat(70));
    lines.push("OVERVIEW:");
    lines.push(c.overview || "");
    lines.push("-".repeat(70));
    lines.push("");
    (c.sections || []).forEach((s, idx) => {
      lines.push("[SECTION " + (idx + 1) + ": " + String(s.title || "").toUpperCase() + "]");
      lines.push(s.content || "");
      lines.push("");
      if (s.keyValues && s.keyValues.length) {
        lines.push("COMMAND REFERENCE / CONTROLS:");
        s.keyValues.forEach((kv) => {
          const label = String(kv.label || "").padEnd(24, " ");
          lines.push("  * " + label + " : " + (kv.value || ""));
        });
        lines.push("");
      }
    });
    lines.push("=".repeat(70));
    if (c.accuracyNote) {
      lines.push("VERIFIED CROSS-CHECK SOURCE NOTE:");
      lines.push(c.accuracyNote);
      lines.push("=".repeat(70));
    }
    return lines.join("\n");
  }

  function exportBaseName(creation) {
    return (creation.game || "document")
      .replace(/[^\w\-]+/g, "_")
      .replace(/_+/g, "_");
  }

  async function withUnconstrainedCanvas(fn) {
    const targetEl = $("#doc-canvas");
    if (!targetEl || !window.htmlToImage) {
      throw new Error("Document canvas or html-to-image is unavailable");
    }
    const origMaxHeight = targetEl.style.maxHeight;
    const origOverflow = targetEl.style.overflow;
    const origHeight = targetEl.style.height;
    targetEl.style.maxHeight = "none";
    targetEl.style.overflow = "visible";
    targetEl.style.height = "auto";

    const fullWidth = Math.max(targetEl.scrollWidth, targetEl.offsetWidth, 800);
    const fullHeight = Math.max(targetEl.scrollHeight, targetEl.offsetHeight);
    const opts = {
      pixelRatio: 2,
      cacheBust: true,
      backgroundColor: "#ffffff",
      width: fullWidth,
      height: fullHeight,
      style: {
        maxHeight: "none",
        overflow: "visible",
        height: "auto",
      },
    };

    try {
      return await fn(targetEl, opts);
    } finally {
      targetEl.style.maxHeight = origMaxHeight;
      targetEl.style.overflow = origOverflow;
      targetEl.style.height = origHeight;
    }
  }

  async function exportDocumentImage(format) {
    if (!state.active) return;
    const a = api();
    if (!a) return;
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
          (c.platform || "").toLowerCase().includes(q)
      )
      .forEach((c) => {
        const li = document.createElement("li");
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.className = "arch-open";
        openBtn.textContent =
          c.game +
          " — " +
          c.creationType +
          " (" +
          c.platform +
          ")" +
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
            renderDocument(state.creations[0] || null);
          }
          renderArchives();
          beep(300, 0.08);
        });
        li.appendChild(openBtn);
        li.appendChild(del);
        list.appendChild(li);
      });
  }

  function syncBackendPanels() {
    const provider = ($("#backend-provider") && $("#backend-provider").value) || "gemini";
    const gemini = $("#gemini-settings");
    const hf = $("#hf-settings");
    if (gemini) gemini.hidden = provider !== "gemini";
    if (hf) hf.hidden = provider !== "huggingface";
  }

  function fillControlPanel(boot) {
    const model = (boot.config && boot.config.model) || {};
    const gemini = (boot.config && boot.config.gemini) || {};
    const backend = (boot.config && boot.config.backend) || {};
    const ui = (boot.config && boot.config.ui) || {};
    const gen = (boot.config && boot.config.generation) || {};

    if ($("#backend-provider")) {
      $("#backend-provider").value = backend.provider || "gemini";
    }

    if ($("#gemini-model")) {
      $("#gemini-model").value = gemini.model || "gemini-2.5-flash";
    }
    if ($("#gemini-temp")) {
      $("#gemini-temp").value = gemini.temperature ?? 0.4;
    }
    if ($("#gemini-search")) {
      $("#gemini-search").checked = gemini.google_search !== false;
    }
    if ($("#gemini-key-status")) {
      $("#gemini-key-status").textContent = gemini.api_key_set
        ? "API key is set (env or saved). Leave the field blank to keep it."
        : "No API key detected yet.";
    }

    const gSug = $("#gemini-suggested");
    if (gSug) {
      gSug.innerHTML = '<option value="">— pick a suggested Gemini model —</option>';
      (boot.suggestedGeminiModels || []).forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.repo_id;
        opt.textContent = m.label + (m.notes ? " — " + m.notes : "");
        gSug.appendChild(opt);
      });
    }

    if ($("#model-repo")) {
      $("#model-repo").value = model.repo_id || "microsoft/Phi-3.5-mini-instruct";
    }
    if ($("#model-device")) $("#model-device").value = model.device || "auto";
    if ($("#model-dtype")) $("#model-dtype").value = model.torch_dtype || "auto";
    if ($("#model-tokens")) $("#model-tokens").value = model.max_new_tokens || 2048;
    if ($("#model-temp")) $("#model-temp").value = model.temperature ?? 0.4;
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

    fillDefaultPresetSelect(boot.presets || state.presets);
    fillDefaultThemeSelect();
    state.defaultPreset = ui.default_preset || "";
    state.defaultTheme = ui.default_theme || "auto";
    if ($("#default-preset")) $("#default-preset").value = state.defaultPreset || "";
    if ($("#default-theme")) {
      const themeSel = $("#default-theme");
      if (![...themeSel.options].some((o) => o.value === state.defaultTheme)) {
        state.defaultTheme = "auto";
      }
      themeSel.value = state.defaultTheme;
    }
    // Sync theme/status only — don't overwrite studio fields mid-session
    applyGameDefaults({ applyPresetFields: false, applyTheme: true });

    const sug = $("#model-suggested");
    if (sug) {
      sug.innerHTML = '<option value="">— pick a suggested HF model —</option>';
      (boot.suggestedModels || []).forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.repo_id;
        opt.textContent = m.label + (m.notes ? " — " + m.notes : "");
        sug.appendChild(opt);
      });
    }

    syncBackendPanels();
    updateModelStatusLine(boot.modelStatus);
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
      const repo =
        (boot && boot.config && boot.config.model && boot.config.model.repo_id) ||
        ($("#model-repo") && $("#model-repo").value) ||
        "local HF";
      modelField.textContent = "Backend: Hugging Face · " + repo;
    } else {
      const model =
        (boot && boot.config && boot.config.gemini && boot.config.gemini.model) ||
        ($("#gemini-model") && $("#gemini-model").value) ||
        "gemini-2.5-flash";
      modelField.textContent = "Backend: Gemini · " + model;
    }
  }

  function updateModelStatusLine(status) {
    const s = status || {};
    const provider = s.provider || (($("#backend-provider") && $("#backend-provider").value) || "gemini");
    const line =
      (provider === "gemini" ? "Gemini" : "HF") +
      ": " +
      (s.state || "idle") +
      (s.loaded_repo ? " · " + s.loaded_repo : "") +
      (s.device ? " @ " + s.device : "") +
      (s.detail ? " — " + s.detail : "");
    const el = $("#model-status-line");
    if (el) el.textContent = line;
  }

  function collectSettings(reload) {
    const provider = ($("#backend-provider") && $("#backend-provider").value) || "gemini";
    return {
      reload_model: !!reload,
      backend: { provider: provider },
      gemini: {
        model: ($("#gemini-model") && $("#gemini-model").value.trim()) || "gemini-2.5-flash",
        api_key: ($("#gemini-key") && $("#gemini-key").value.trim()) || "",
        google_search: $("#gemini-search") ? $("#gemini-search").checked : true,
        temperature: $("#gemini-temp") ? Number($("#gemini-temp").value) || 0 : 0.4,
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
        default_preset: ($("#default-preset") && $("#default-preset").value) || null,
        default_theme: ($("#default-theme") && $("#default-theme").value) || "auto",
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
  }

  function setControlTab(tab) {
    const allowed = { ai: true, display: true, defaults: true };
    state.controlTab = allowed[tab] ? tab : "ai";
    document.querySelectorAll(".control-tab").forEach((btn) => {
      btn.classList.toggle(
        "active",
        btn.getAttribute("data-control-tab") === state.controlTab
      );
    });
    document.querySelectorAll(".control-pane").forEach((pane) => {
      const id = pane.getAttribute("data-control-pane");
      pane.hidden = id !== state.controlTab;
    });
  }

  function applyDisplaySettingsFromControls() {
    state.soundEnabled = $("#opt-sound").checked;
    state.crtEnabled = $("#opt-crt").checked;
    $("#crt-overlay").hidden = !state.crtEnabled;
    applyUiScale(readUiScaleFromControl());
  }

  function fillDefaultPresetSelect(presets) {
    const sel = $("#default-preset");
    if (!sel) return;
    const list = presets || state.presets || [];
    const prev = sel.value || state.defaultPreset || "";
    sel.innerHTML = '<option value="">— none (keep studio fields as-is) —</option>';
    list.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.game;
      opt.textContent = p.game + " (" + p.platform + ")";
      sel.appendChild(opt);
    });
    if (prev && [...sel.options].some((o) => o.value === prev)) {
      sel.value = prev;
    }
  }

  function fillDefaultThemeSelect() {
    const src = $("#theme-override");
    const dst = $("#default-theme");
    if (!src || !dst) return;
    const prev = dst.value || state.defaultTheme || "auto";
    dst.innerHTML = src.innerHTML;
    if (prev && [...dst.options].some((o) => o.value === prev)) {
      dst.value = prev;
    } else {
      dst.value = "auto";
    }
  }

  function findPresetByGame(game) {
    if (!game) return null;
    return (state.presets || []).find((p) => p.game === game) || null;
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
    const presetKey =
      ($("#default-preset") && $("#default-preset").value) || state.defaultPreset || "";
    const themeKey =
      ($("#default-theme") && $("#default-theme").value) || state.defaultTheme || "auto";

    state.defaultPreset = presetKey;
    state.defaultTheme = themeKey || "auto";

    if (opts.applyPresetFields !== false && presetKey) {
      const preset = findPresetByGame(presetKey);
      if (preset) applyPreset(preset, true);
    }

    if (opts.applyTheme !== false) {
      if ($("#theme-override")) {
        $("#theme-override").value = state.defaultTheme;
      }
      if (state.active) renderDocument(state.active);
    }

    updateStudioThemeField();
  }

  function applyPreset(p, silent) {
    if (!p) return;
    $("#game-input").value = p.game;
    $("#platform-input").value = p.platform;
    $("#creation-type").value = p.suggestedCreation;
    syncPlatformSelect();
    if (!silent) beep(800, 0.03);
  }

  function fillCatalogs(boot) {
    const platforms =
      (boot && boot.platforms) ||
      (window.RGC_CATALOG && window.RGC_CATALOG.platforms) ||
      [];
    const creationTypes =
      (boot && boot.creationTypes) ||
      (window.RGC_CATALOG && window.RGC_CATALOG.creationTypes) ||
      [];
    const presets =
      (boot && boot.presets) ||
      (window.RGC_CATALOG && window.RGC_CATALOG.presets) ||
      [];
    state.presets = presets;

    const platformSelect = $("#platform-select");
    if (platformSelect) {
      platformSelect.innerHTML = '<option value="">-- Presets --</option>';
      platforms.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p;
        opt.textContent = p;
        platformSelect.appendChild(opt);
      });
      syncPlatformSelect();
    }

    const sel = $("#creation-type");
    if (sel) {
      const previous = sel.value;
      sel.innerHTML = "";
      creationTypes.forEach((t) => {
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = t.label;
        sel.appendChild(opt);
      });
      if (previous && Array.from(sel.options).some((o) => o.value === previous)) {
        sel.value = previous;
      } else if (creationTypes.length) {
        sel.value = creationTypes[0].id;
      }
    }

    fillDefaultPresetSelect(presets);
    fillDefaultThemeSelect();
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
    updateModelStatusLine({
      state: "busy",
      detail: message,
    });
  };

  function applyGenerationResult(creation) {
    if (!creation) return;
    // Idempotent — poll and evaluate_js may both fire
    if (state._lastHandledId === creation.id) return;
    state._lastHandledId = creation.id;

    state.generating = false;
    $("#btn-generate").disabled = false;
    endBusy("Ready");
    state.creations = [creation].concat(
      state.creations.filter((c) => c.id !== creation.id)
    );
    renderArchives();
    renderDocument(creation);
    openWindow("viewer");
    openWindow("library");
    focusWindow("viewer");
    beep(880, 0.08, "triangle");
    beep(1175, 0.1, "triangle");
  }

  function applyGenerationError(err) {
    state.generating = false;
    $("#btn-generate").disabled = false;
    endBusy("Ready");
    showToast(String(err));
    beep(200, 0.2, "sawtooth");
  }

  /**
   * Poll Python get_job until done/error. This is the reliable completion path
   * on Windows WebView2 where evaluate_js from worker threads often fails.
   */
  async function pollJob(jobId, kind) {
    const a = api();
    if (!a || !jobId) return;
    const started = Date.now();
    const maxMs = kind === "preload" ? 60 * 60 * 1000 : 60 * 60 * 1000;

    while (Date.now() - started < maxMs) {
      let job;
      try {
        job = await a.get_job(jobId);
      } catch (err) {
        applyGenerationError("Lost connection to Python bridge: " + err);
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
          endBusy("Ready");
          if (job.result && job.result.modelStatus) {
            updateModelStatusLine(job.result.modelStatus);
          } else {
            try {
              updateModelStatusLine(await a.get_model_status());
            } catch (_) {
              /* ignore */
            }
          }
          showToast("Model ready");
        }
        return;
      }

      if (job.status === "error" || job.status === "missing") {
        if (kind === "generate") {
          applyGenerationError(job.error || "Generation failed");
        } else {
          endBusy("Ready");
          showToast(job.error || "Model load failed");
        }
        return;
      }

      await sleep(500);
    }

    if (kind === "generate") {
      applyGenerationError("Timed out waiting for generation.");
    } else {
      endBusy("Ready");
      showToast("Timed out waiting for model load.");
    }
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
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

  window.__onModelStatus = async function () {
    // Don't endBusy here if a generate job is still running
    if (state.generating) {
      const a = api();
      if (!a) return;
      try {
        updateModelStatusLine(await a.get_model_status());
      } catch (_) {
        /* ignore */
      }
      return;
    }
    endBusy("Ready");
    const a = api();
    if (!a) return;
    try {
      const status = await a.get_model_status();
      updateModelStatusLine(status);
    } catch (_) {
      /* ignore */
    }
  };

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

    const platformSelect = $("#platform-select");
    if (platformSelect) {
      platformSelect.addEventListener("change", () => {
        if (platformSelect.value) {
          $("#platform-input").value = platformSelect.value;
          beep(700, 0.03);
        }
      });
    }
    $("#platform-input").addEventListener("input", syncPlatformSelect);

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

    let startGenerationLock = false;
    async function startGeneration() {
      if (startGenerationLock || state.generating) {
        showToast("A generation is already running…");
        return;
      }
      startGenerationLock = true;

      try {
        const a = api();
        if (!a) {
          showToast("Python bridge not ready. Launch via: python -m retro_game_creator");
          return;
        }

        if (!$("#creation-type").options.length) {
          fillCatalogs(null);
        }

        const game = $("#game-input").value.trim();
        const platform = $("#platform-input").value.trim();
        const creationType = $("#creation-type").value;
        if (!game || !platform || !creationType) {
          showToast("Game, platform, and creation type are required.");
          return;
        }

        state.generating = true;
        $("#btn-generate").disabled = true;
        beginBusy("Generating document", "Calling Gemini / backend…", {
        delayMs: 0,
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
          res = await a.create_creation(game, platform, creationType);
        } catch (err) {
          applyGenerationError(err);
          return;
        }

        if (!res || !res.ok) {
          applyGenerationError((res && res.error) || "Generation failed to start");
          return;
        }
        if (!res.job_id) {
          applyGenerationError("Backend did not return a job id.");
          return;
        }
        updateBusy("Job started — loading model / generating…");
        pollJob(res.job_id, "generate");
      } finally {
        startGenerationLock = false;
      }
    }

    $("#btn-preload").addEventListener("click", async () => {
      const a = api();
      if (!a) {
        showToast("Python bridge not ready.");
        return;
      }
      beginBusy("Checking backend", "…", { delayMs: 0 });
      try {
        const res = await a.preload_model();
        if (!res || !res.ok) {
          endBusy("Ready");
          showToast((res && res.error) || "Backend check failed");
          return;
        }
        if (res.job_id) {
          pollJob(res.job_id, "preload");
        } else {
          endBusy("Ready");
          if (res.modelStatus) updateModelStatusLine(res.modelStatus);
          showToast(res.message || "Backend ready");
        }
      } catch (err) {
        endBusy("Ready");
        showToast(String(err));
      }
    });

    $("#archive-search").addEventListener("input", renderArchives);

    $("#btn-export-all").addEventListener("click", async () => {
      const a = api();
      if (!a) return;
      const json = await a.export_creations_json();
      const date = new Date().toISOString().slice(0, 10);
      await a.save_file_dialog("retro_game_archives_" + date + ".json", json);
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

    $("#btn-export-txt").addEventListener("click", async () => {
      if (!state.active) return;
      const a = api();
      if (!a) return;
      const txt = await a.export_creation_txt(state.active);
      const name =
        (state.active.game || "document").replace(/[^\w\-]+/g, "_") + ".txt";
      await a.save_file_dialog(name, txt);
    });

    $("#btn-export-json").addEventListener("click", async () => {
      if (!state.active) return;
      const a = api();
      if (!a) return;
      const name =
        (state.active.game || "document").replace(/[^\w\-]+/g, "_") + ".json";
      await a.save_file_dialog(name, JSON.stringify(state.active, null, 2));
    });

    $("#btn-export-png").addEventListener("click", () => {
      exportDocumentImage("png");
    });

    $("#btn-export-pdf").addEventListener("click", () => {
      exportDocumentImage("pdf");
    });

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

    $("#model-suggested").addEventListener("change", () => {
      const v = $("#model-suggested").value;
      if (v) $("#model-repo").value = v;
    });

    if ($("#gemini-suggested")) {
      $("#gemini-suggested").addEventListener("change", () => {
        const v = $("#gemini-suggested").value;
        if (v) $("#gemini-model").value = v;
      });
    }

    if ($("#backend-provider")) {
      $("#backend-provider").addEventListener("change", () => {
        syncBackendPanels();
        updateStudioBackendLabel({
          config: {
            backend: { provider: $("#backend-provider").value },
            gemini: { model: $("#gemini-model").value },
            model: { repo_id: $("#model-repo").value },
          },
        });
      });
    }

    $("#btn-save-model").addEventListener("click", async () => {
      const a = api();
      if (!a) return;
      const res = await a.save_settings(collectSettings(true));
      applyDisplaySettingsFromControls();
      if (res.config) {
        // Reflect masked key status
        fillControlPanel({
          config: res.config,
          suggestedModels: [],
          suggestedGeminiModels: [],
          modelStatus: res.modelStatus,
        });
        // Re-fetch full bootstrap catalogs for suggested lists if emptied
        try {
          const boot = await a.get_bootstrap();
          fillControlPanel(boot);
        } catch (_) {
          updateModelStatusLine(res.modelStatus);
        }
      } else {
        updateModelStatusLine(res.modelStatus);
      }
      showToast(res.message || "Saved");
      beep(750, 0.05);
    });

    $("#btn-save-settings").addEventListener("click", async () => {
      const a = api();
      if (!a) return;
      applyDisplaySettingsFromControls();
      const res = await a.save_settings(collectSettings(false));
      showToast(res.message || "Display & sound saved");
      beep(750, 0.05);
    });

    if ($("#btn-save-defaults")) {
      $("#btn-save-defaults").addEventListener("click", async () => {
        const a = api();
        if (!a) return;
        applyGameDefaults({ applyPresetFields: true, applyTheme: true });
        const res = await a.save_settings(collectSettings(false));
        showToast(res.message || "Game defaults saved");
        beep(750, 0.05);
      });
    }

    if ($("#default-preset")) {
      $("#default-preset").addEventListener("change", () => {
        applyGameDefaults({ applyPresetFields: true, applyTheme: false });
        beep(700, 0.03);
      });
    }
    if ($("#default-theme")) {
      $("#default-theme").addEventListener("change", () => {
        applyGameDefaults({ applyPresetFields: false, applyTheme: true });
        beep(700, 0.03);
      });
    }

    document.querySelectorAll(".control-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        setControlTab(btn.getAttribute("data-control-tab"));
        beep(650, 0.03);
      });
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
  }

  async function init() {
    // Catalogs first — never depend on Python for dropdowns
    fillCatalogs(null);
    wireEvents();
    enableWindowDragging();
    tickClock();
    setInterval(tickClock, 15000);
    focusWindow("form");
    renderTaskbar();

    const a = await waitForApi();
    if (!a) {
      showToast(
        "Running without Python bridge — open via: python -m retro_game_creator"
      );
      return;
    }

    try {
      const boot = await a.get_bootstrap();
      state.config = boot.config;
      state.creations = boot.creations || [];
      fillCatalogs(boot);
      fillControlPanel(boot);
      applyGameDefaults({ applyPresetFields: true, applyTheme: true });
      renderArchives();
      if (state.creations.length) renderDocument(state.creations[0]);
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
