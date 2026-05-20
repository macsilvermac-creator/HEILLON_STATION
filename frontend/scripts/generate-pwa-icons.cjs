"use strict";

const fs = require("fs");
const path = require("path");
const { PNG } = require("pngjs");

function hexRgb(hex) {
  const h = hex.replace("#", "");
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

async function mk(w, outfile) {
  const png = new PNG({ width: w, height: w });

  const bg = hexRgb("#0A0F1E");
  const gold = hexRgb("#D4AF37");

  function set(px, py, c) {
    if (px < 0 || py < 0 || px >= w || py >= w) return;
    const idx = (w * py + px) << 2;
    png.data[idx] = c.r;
    png.data[idx + 1] = c.g;
    png.data[idx + 2] = c.b;
    png.data[idx + 3] = 255;
  }

  for (let y = 0; y < w; y++) {
    for (let x = 0; x < w; x++) {
      set(x, y, bg);
    }
  }

  const m = Math.max(14, Math.floor(w * 0.06));
  for (let y = m; y < w - m; y++) {
    for (let x = m; x < w - m; x++) {
      const d = Math.min(x - m, y - m, w - m - x, w - m - y);
      if (d < Math.max(3, Math.floor(w * 0.018))) set(x, y, gold);
    }
  }

  const cx = Math.floor(w / 2);
  const cy = Math.floor(w / 2);
  const barW = Math.floor(w * 0.42);
  const barTh = Math.max(24, Math.floor(w * 0.12));

  for (let y = cy - Math.floor(barTh / 2); y < cy + Math.floor(barTh / 2); y++) {
    for (let x = cx - Math.floor(barW / 2); x < cx + Math.floor(barW / 2); x++) {
      set(x, y, gold);
    }
  }

  await new Promise((resolve, reject) => {
    const stream = png.pack().pipe(fs.createWriteStream(outfile));
    stream.on("finish", resolve);
    stream.on("error", reject);
  });
}

async function main() {
  const dir = path.join(__dirname, "..", "public", "icons");
  fs.mkdirSync(dir, { recursive: true });
  await mk(192, path.join(dir, "icon-192.png"));
  await mk(512, path.join(dir, "icon-512.png"));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
