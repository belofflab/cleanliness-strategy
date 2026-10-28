// Рендер HTML-клипов в MP4: кадр за кадром (Web Animations перематываются на точное время), затем ffmpeg.
// Использование: node marketing/tools/render_clips.js [номер ...]   — без аргументов рендерит все клипы.
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const { chromium } = require("playwright");

const FPS = 30;
const SRC = path.join(__dirname, "..", "video", "src");
const OUT = path.join(__dirname, "..", "video", "mp4");

(async () => {
  const only = process.argv.slice(2).map(Number);
  const files = fs.readdirSync(SRC).filter(f => f.endsWith(".html"))
    .filter(f => !only.length || only.includes(parseInt(f, 10))).sort();
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const file of files) {
    await page.goto("file://" + path.join(SRC, file), { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    const dur = await page.evaluate(() => Number(document.body.dataset.duration));
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "clip-"));
    const frames = Math.round(dur * FPS);
    for (let i = 0; i < frames; i++) {
      await page.evaluate(t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; }), (i * 1000) / FPS);
      await page.screenshot({ path: path.join(tmp, String(i).padStart(5, "0") + ".jpg"), type: "jpeg", quality: 92 });
    }
    const out = path.join(OUT, file.replace(".html", ".mp4"));
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", path.join(tmp, "%05d.jpg"),
      "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]);
    fs.rmSync(tmp, { recursive: true, force: true });
    console.log(`${file} → ${path.basename(out)} (${frames} кадров)`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
