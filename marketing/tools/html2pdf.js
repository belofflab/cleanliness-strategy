// HTML → PDF через Chromium. Использование: node html2pdf.js page.html out.pdf [A4|A4-landscape]
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const [, , html, out, format = "A4-landscape"] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + path.resolve(html), { waitUntil: "load" });
  await page.pdf({ path: out, format: "A4", landscape: format.endsWith("landscape"), printBackground: true,
                   margin: { top: "0", right: "0", bottom: "0", left: "0" } });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
