// Рендер SVG → PNG (прозрачный фон) и векторный PDF через Chromium (Playwright).
// Использование: node render.js manifest.json
// manifest: [{ "svg": "путь.svg", "png": [{ "file": "x.png", "width": 2000, "bg": "#fff" }],
//              "pdf": { "file": "x.pdf", "width_mm": 100 } }]
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const manifest = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const item of manifest) {
    const svg = fs.readFileSync(item.svg, "utf8");
    const vb = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
    const ratio = vb[3] / vb[2];
    for (const png of item.png || []) {
      const w = png.width, h = Math.round(w * ratio);
      await page.setViewportSize({ width: w, height: h });
      const bg = png.bg ? `background:${png.bg};` : "background:transparent;";
      const sized = svg.replace(/<svg([^>]*?)\swidth="[^"]+"\sheight="[^"]+"/, `<svg$1 width="${w}" height="${h}"`);
      await page.setContent(`<html><body style="margin:0;${bg}">${sized}</body></html>`);
      fs.mkdirSync(path.dirname(png.file), { recursive: true });
      await page.screenshot({ path: png.file, omitBackground: !png.bg, clip: { x: 0, y: 0, width: w, height: h } });
    }
    if (item.pdf) {
      const wmm = item.pdf.width_mm, hmm = +(wmm * ratio).toFixed(2);
      const sized = svg.replace(/<svg([^>]*?)\swidth="[^"]+"\sheight="[^"]+"/, `<svg$1 width="${wmm}mm" height="${hmm}mm"`);
      await page.setContent(`<html><head><style>@page{size:${wmm}mm ${hmm}mm;margin:0}html,body{margin:0}svg{display:block}</style></head><body>${sized}</body></html>`);
      fs.mkdirSync(path.dirname(item.pdf.file), { recursive: true });
      await page.pdf({ path: item.pdf.file, width: `${wmm}mm`, height: `${hmm}mm`, printBackground: true, pageRanges: "1" });
    }
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
