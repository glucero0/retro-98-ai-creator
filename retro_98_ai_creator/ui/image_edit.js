/**
 * Image edit pipeline adapted from ReFrame (canvas 2D filters + rotate + crop).
 * Exposes window.R98ImageEdit for the Viewer Edit panel.
 */
(function (global) {
  "use strict";

  var DEFAULT_FILTERS = {
    brightness: 0,
    contrast: 0,
    grayscale: false,
    threshold: false,
    sharpen: false,
    saturation: 100,
    hueRotate: 0,
    invert: 0,
    sepia: 0,
    blur: 0,
    exposure: 0,
    gamma: 1,
    vignette: 0,
    tintRed: 0,
    tintGreen: 0,
    tintBlue: 0,
    bgRemove: false,
    bgRemoveTolerance: 35,
    bgRemoveFromEdges: false,
  };

  var TEXT_THRESHOLD_LEVEL = 210;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function normalizeFilters(settings) {
    var out = {};
    var key;
    for (key in DEFAULT_FILTERS) {
      if (Object.prototype.hasOwnProperty.call(DEFAULT_FILTERS, key)) {
        out[key] =
          settings && settings[key] !== undefined && settings[key] !== null
            ? settings[key]
            : DEFAULT_FILTERS[key];
      }
    }
    return out;
  }

  function hasActiveFilters(settings) {
    var s = normalizeFilters(settings);
    return (
      s.brightness !== 0 ||
      s.contrast !== 0 ||
      s.grayscale ||
      s.threshold ||
      s.sharpen ||
      s.saturation !== 100 ||
      s.hueRotate !== 0 ||
      s.invert !== 0 ||
      s.sepia !== 0 ||
      s.blur !== 0 ||
      s.exposure !== 0 ||
      s.gamma !== 1 ||
      s.vignette !== 0 ||
      s.tintRed !== 0 ||
      s.tintGreen !== 0 ||
      s.tintBlue !== 0 ||
      s.bgRemove
    );
  }

  function normalizeRotation(degrees) {
    var rounded = Math.round(Number(degrees) * 1000) / 1000;
    return ((rounded % 360) + 360) % 360;
  }

  function isRightAngleRotation(degrees) {
    var n = normalizeRotation(degrees);
    return n % 90 === 0;
  }

  function rotatedOutputSize(width, height, degrees) {
    var angle = normalizeRotation(degrees);
    if (angle === 0) return { width: width, height: height };
    if (isRightAngleRotation(angle)) {
      if (angle === 90 || angle === 270) return { width: height, height: width };
      return { width: width, height: height };
    }
    var rad = (angle * Math.PI) / 180;
    var sin = Math.abs(Math.sin(rad));
    var cos = Math.abs(Math.cos(rad));
    return {
      width: Math.max(1, Math.ceil(width * cos + height * sin)),
      height: Math.max(1, Math.ceil(width * sin + height * cos)),
    };
  }

  function rotateCanvasRightAngle(source, degrees) {
    var w = source.width;
    var h = source.height;
    var srcCtx = source.getContext("2d");
    var srcData = srcCtx.getImageData(0, 0, w, h);
    var outW = degrees === 90 || degrees === 270 ? h : w;
    var outH = degrees === 90 || degrees === 270 ? w : h;
    var outCanvas = document.createElement("canvas");
    outCanvas.width = outW;
    outCanvas.height = outH;
    var outCtx = outCanvas.getContext("2d");
    var outData = outCtx.createImageData(outW, outH);
    var sy, sx, dx, dy, si, di;

    for (sy = 0; sy < h; sy++) {
      for (sx = 0; sx < w; sx++) {
        if (degrees === 90) {
          dx = h - 1 - sy;
          dy = sx;
        } else if (degrees === 180) {
          dx = w - 1 - sx;
          dy = h - 1 - sy;
        } else if (degrees === 270) {
          dx = sy;
          dy = w - 1 - sx;
        } else {
          dx = sx;
          dy = sy;
        }
        si = (sy * w + sx) * 4;
        di = (dy * outW + dx) * 4;
        outData.data[di] = srcData.data[si];
        outData.data[di + 1] = srcData.data[si + 1];
        outData.data[di + 2] = srcData.data[si + 2];
        outData.data[di + 3] = srcData.data[si + 3];
      }
    }
    outCtx.putImageData(outData, 0, 0);
    return outCanvas;
  }

  function rotateCanvas(source, degrees) {
    var angle = normalizeRotation(degrees);
    if (angle === 0) return source;
    if (isRightAngleRotation(angle)) return rotateCanvasRightAngle(source, angle);

    var w = source.width;
    var h = source.height;
    var size = rotatedOutputSize(w, h, angle);
    var outCanvas = document.createElement("canvas");
    outCanvas.width = size.width;
    outCanvas.height = size.height;
    var ctx = outCanvas.getContext("2d");
    ctx.imageSmoothingEnabled = true;
    ctx.translate(size.width / 2, size.height / 2);
    ctx.rotate((angle * Math.PI) / 180);
    ctx.drawImage(source, -w / 2, -h / 2);
    return outCanvas;
  }

  function colorDistance(a, b) {
    return Math.sqrt(
      (a.r - b.r) * (a.r - b.r) +
        (a.g - b.g) * (a.g - b.g) +
        (a.b - b.b) * (a.b - b.b)
    );
  }

  function detectEdgeBackgroundColor(data, width, height) {
    var reds = [];
    var greens = [];
    var blues = [];
    function sample(x, y) {
      if (x < 0 || y < 0 || x >= width || y >= height) return;
      var i = (y * width + x) * 4;
      if (data[i + 3] < 16) return;
      reds.push(data[i]);
      greens.push(data[i + 1]);
      blues.push(data[i + 2]);
    }
    var x, y;
    for (x = 0; x < width; x++) {
      sample(x, 0);
      if (height > 1) sample(x, height - 1);
    }
    for (y = 1; y < height - 1; y++) {
      sample(0, y);
      if (width > 1) sample(width - 1, y);
    }
    function median(values) {
      if (!values.length) return 255;
      var sorted = values.slice().sort(function (a, b) {
        return a - b;
      });
      var mid = Math.floor(sorted.length / 2);
      return sorted.length % 2 === 0
        ? Math.round((sorted[mid - 1] + sorted[mid]) / 2)
        : sorted[mid];
    }
    return { r: median(reds), g: median(greens), b: median(blues) };
  }

  function applyBackgroundRemoval(ctx, width, height, settings) {
    var imageData = ctx.getImageData(0, 0, width, height);
    var data = imageData.data;
    var key = detectEdgeBackgroundColor(data, width, height);
    var threshold =
      (clamp(settings.bgRemoveTolerance, 0, 100) / 100) * Math.sqrt(3 * 255 * 255);
    var fromEdges = !!settings.bgRemoveFromEdges;
    var i, pixelIndex, matches;

    function pixelMatches(idx) {
      var j = idx * 4;
      if (data[j + 3] < 16) return false;
      return (
        colorDistance(
          { r: data[j], g: data[j + 1], b: data[j + 2] },
          key
        ) <= threshold
      );
    }

    if (fromEdges) {
      var visited = new Uint8Array(width * height);
      var queue = [];
      function addSeed(x, y) {
        var idx = y * width + x;
        if (visited[idx]) return;
        if (!pixelMatches(idx)) return;
        visited[idx] = 1;
        queue.push(idx);
      }
      for (x = 0; x < width; x++) {
        addSeed(x, 0);
        if (height > 1) addSeed(x, height - 1);
      }
      for (y = 1; y < height - 1; y++) {
        addSeed(0, y);
        if (width > 1) addSeed(width - 1, y);
      }
      var head;
      for (head = 0; head < queue.length; head++) {
        var idx = queue[head];
        var px = idx % width;
        var py = Math.floor(idx / width);
        data[idx * 4] = 0;
        data[idx * 4 + 1] = 0;
        data[idx * 4 + 2] = 0;
        data[idx * 4 + 3] = 0;
        if (px > 0) addSeed(px - 1, py);
        if (px < width - 1) addSeed(px + 1, py);
        if (py > 0) addSeed(px, py - 1);
        if (py < height - 1) addSeed(px, py + 1);
      }
    } else {
      for (pixelIndex = 0; pixelIndex < data.length / 4; pixelIndex++) {
        if (!pixelMatches(pixelIndex)) continue;
        i = pixelIndex * 4;
        data[i] = 0;
        data[i + 1] = 0;
        data[i + 2] = 0;
        data[i + 3] = 0;
      }
    }
    ctx.putImageData(imageData, 0, 0);
  }

  function applyPixelAdjustments(ctx, width, height, settings) {
    var needs =
      settings.brightness !== 0 ||
      settings.contrast !== 0 ||
      settings.grayscale ||
      settings.threshold ||
      settings.exposure !== 0 ||
      settings.gamma !== 1 ||
      settings.tintRed !== 0 ||
      settings.tintGreen !== 0 ||
      settings.tintBlue !== 0;
    if (!needs) return;

    var imageData = ctx.getImageData(0, 0, width, height);
    var data = imageData.data;
    var brightness = settings.brightness;
    var contrast = settings.contrast;
    var contrastFactor =
      contrast === 0 ? 1 : (259 * (contrast + 255)) / (255 * (259 - contrast));
    var exposureFactor = Math.pow(2, settings.exposure / 100);
    var gamma = settings.gamma;
    var tintR = settings.tintRed * 2.55;
    var tintG = settings.tintGreen * 2.55;
    var tintB = settings.tintBlue * 2.55;
    var i, a, r, g, b, gray, v;

    for (i = 0; i < data.length; i += 4) {
      a = data[i + 3];
      if (a < 16) continue;
      r = data[i];
      g = data[i + 1];
      b = data[i + 2];

      if (settings.exposure !== 0) {
        r = clamp(r * exposureFactor, 0, 255);
        g = clamp(g * exposureFactor, 0, 255);
        b = clamp(b * exposureFactor, 0, 255);
      }
      if (gamma !== 1) {
        r = clamp(Math.pow(r / 255, gamma) * 255, 0, 255);
        g = clamp(Math.pow(g / 255, gamma) * 255, 0, 255);
        b = clamp(Math.pow(b / 255, gamma) * 255, 0, 255);
      }
      if (tintR || tintG || tintB) {
        r = clamp(r + tintR, 0, 255);
        g = clamp(g + tintG, 0, 255);
        b = clamp(b + tintB, 0, 255);
      }
      r = clamp(r + brightness, 0, 255);
      g = clamp(g + brightness, 0, 255);
      b = clamp(b + brightness, 0, 255);
      if (contrast !== 0) {
        r = clamp(contrastFactor * (r - 128) + 128, 0, 255);
        g = clamp(contrastFactor * (g - 128) + 128, 0, 255);
        b = clamp(contrastFactor * (b - 128) + 128, 0, 255);
      }
      if (settings.grayscale || settings.threshold) {
        gray = 0.299 * r + 0.587 * g + 0.114 * b;
        if (settings.threshold) {
          v = gray >= TEXT_THRESHOLD_LEVEL ? 255 : 0;
          r = g = b = v;
        } else {
          r = g = b = gray;
        }
      }
      data[i] = r;
      data[i + 1] = g;
      data[i + 2] = b;
    }
    ctx.putImageData(imageData, 0, 0);
  }

  function applyStyleFilters(ctx, width, height, settings, blurOnly) {
    var parts = [];
    if (blurOnly) {
      if (settings.blur > 0) parts.push("blur(" + settings.blur + "px)");
    } else {
      if (settings.saturation !== 100) parts.push("saturate(" + settings.saturation + "%)");
      if (settings.hueRotate !== 0) parts.push("hue-rotate(" + settings.hueRotate + "deg)");
      if (settings.invert > 0) parts.push("invert(" + settings.invert + "%)");
      if (settings.sepia > 0) parts.push("sepia(" + settings.sepia + "%)");
    }
    if (!parts.length) return;

    var source = ctx.canvas;
    var temp = document.createElement("canvas");
    temp.width = width;
    temp.height = height;
    var tctx = temp.getContext("2d");
    tctx.filter = parts.join(" ");
    tctx.drawImage(source, 0, 0, width, height);
    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(temp, 0, 0, width, height);
  }

  function applyVignette(ctx, width, height, amount) {
    var imageData = ctx.getImageData(0, 0, width, height);
    var data = imageData.data;
    var strength = amount / 100;
    var cx = width / 2;
    var cy = height / 2;
    var maxDist = Math.hypot(cx, cy);
    var x, y, i, dist, factor;
    for (y = 0; y < height; y++) {
      for (x = 0; x < width; x++) {
        i = (y * width + x) * 4;
        if (data[i + 3] < 16) continue;
        dist = Math.hypot(x - cx, y - cy);
        factor = 1 - strength * Math.pow(dist / maxDist, 2);
        data[i] = clamp(data[i] * factor, 0, 255);
        data[i + 1] = clamp(data[i + 1] * factor, 0, 255);
        data[i + 2] = clamp(data[i + 2] * factor, 0, 255);
      }
    }
    ctx.putImageData(imageData, 0, 0);
  }

  function applySharpen(ctx, width, height) {
    if (width < 3 || height < 3) return;
    var source = ctx.getImageData(0, 0, width, height);
    var output = ctx.createImageData(width, height);
    output.data.set(source.data);
    var kernel = [0, -1, 0, -1, 5, -1, 0, -1, 0];
    var strength = 0.45;
    var y, x, c, sum, ki, ky, kx, px, original, sharpened, alphaIndex;
    for (y = 1; y < height - 1; y++) {
      for (x = 1; x < width - 1; x++) {
        alphaIndex = (y * width + x) * 4 + 3;
        if (source.data[alphaIndex] < 16) continue;
        for (c = 0; c < 3; c++) {
          sum = 0;
          ki = 0;
          for (ky = -1; ky <= 1; ky++) {
            for (kx = -1; kx <= 1; kx++) {
              px = ((y + ky) * width + (x + kx)) * 4 + c;
              sum += source.data[px] * kernel[ki];
              ki++;
            }
          }
          original = source.data[(y * width + x) * 4 + c];
          sharpened = clamp(original + (sum - original) * strength, 0, 255);
          output.data[(y * width + x) * 4 + c] = sharpened;
        }
      }
    }
    ctx.putImageData(output, 0, 0);
  }

  function applyFiltersToContext(ctx, width, height, settings) {
    var filters = normalizeFilters(settings);
    var withoutBg = Object.assign({}, filters, { bgRemove: false });
    if (hasActiveFilters(withoutBg)) {
      applyPixelAdjustments(ctx, width, height, filters);
      applyStyleFilters(ctx, width, height, filters, false);
      if (filters.sharpen) applySharpen(ctx, width, height);
      if (filters.vignette > 0) applyVignette(ctx, width, height, filters.vignette);
      if (filters.blur > 0) applyStyleFilters(ctx, width, height, filters, true);
    }
    if (filters.bgRemove) {
      applyBackgroundRemoval(ctx, width, height, filters);
    }
  }

  /**
   * Render edited image onto an output canvas.
   * crop: { x, y, w, h } in source image pixels (before rotate), or null for full image.
   * rotation: degrees clockwise applied after crop+filters.
   */
  function renderEditedCanvas(sourceImage, filters, crop, rotation) {
    var sx = 0;
    var sy = 0;
    var sw = sourceImage.naturalWidth || sourceImage.width;
    var sh = sourceImage.naturalHeight || sourceImage.height;
    if (crop && crop.w > 0 && crop.h > 0) {
      sx = clamp(Math.round(crop.x), 0, sw - 1);
      sy = clamp(Math.round(crop.y), 0, sh - 1);
      sw = clamp(Math.round(crop.w), 1, (sourceImage.naturalWidth || sourceImage.width) - sx);
      sh = clamp(Math.round(crop.h), 1, (sourceImage.naturalHeight || sourceImage.height) - sy);
    }

    var canvas = document.createElement("canvas");
    canvas.width = sw;
    canvas.height = sh;
    var ctx = canvas.getContext("2d");
    ctx.drawImage(sourceImage, sx, sy, sw, sh, 0, 0, sw, sh);
    applyFiltersToContext(ctx, sw, sh, filters || DEFAULT_FILTERS);
    return rotateCanvas(canvas, rotation || 0);
  }

  function canvasToDataUrl(canvas, mimeType) {
    mimeType = mimeType || "image/png";
    if (mimeType.indexOf("jpeg") >= 0 || mimeType.indexOf("jpg") >= 0) {
      return canvas.toDataURL("image/jpeg", 0.92);
    }
    return canvas.toDataURL("image/png");
  }

  global.R98ImageEdit = {
    DEFAULT_FILTERS: DEFAULT_FILTERS,
    normalizeFilters: normalizeFilters,
    hasActiveFilters: hasActiveFilters,
    normalizeRotation: normalizeRotation,
    renderEditedCanvas: renderEditedCanvas,
    canvasToDataUrl: canvasToDataUrl,
    applyFiltersToContext: applyFiltersToContext,
    rotateCanvas: rotateCanvas,
  };
})(window);
