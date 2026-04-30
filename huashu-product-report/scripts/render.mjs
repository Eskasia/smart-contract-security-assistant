import { chromium } from "playwright";
import sharp from "sharp";
import { mkdir, readdir } from "node:fs/promises";
import path from "node:path";

const ROOT = path.resolve(".");
const slidesDir = path.join(ROOT, "slides");
const outDir = path.join(ROOT, "screenshots");
await mkdir(outDir, { recursive: true });

const files = (await readdir(slidesDir)).filter((file) => file.endsWith(".html")).sort();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
const errors = [];

page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});
page.on("pageerror", (err) => errors.push(err.message));

const screenshotPaths = [];
for (const [index, file] of files.entries()) {
  await page.goto(`file://${path.join(slidesDir, file)}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(120);
  const target = path.join(outDir, `slide-${String(index + 1).padStart(2, "0")}.png`);
  await page.screenshot({ path: target, fullPage: false });
  screenshotPaths.push(target);
  console.log(`[${index + 1}/${files.length}] ${file}`);
}
await browser.close();

const thumbW = 320;
const thumbH = 180;
const labelH = 26;
const cols = 4;
const rows = Math.ceil(screenshotPaths.length / cols);
const canvas = sharp({
  create: {
    width: cols * thumbW,
    height: rows * (thumbH + labelH),
    channels: 4,
    background: "#050707",
  },
});

const composites = [];
for (const [index, file] of screenshotPaths.entries()) {
  const left = (index % cols) * thumbW;
  const top = Math.floor(index / cols) * (thumbH + labelH);
  const thumb = await sharp(file).resize(thumbW, thumbH).png().toBuffer();
  const label = Buffer.from(
    `<svg width="${thumbW}" height="${labelH}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="#050707"/>
      <text x="8" y="18" font-family="Arial" font-size="14" fill="#F7F2DF">slide-${String(index + 1).padStart(2, "0")}</text>
    </svg>`,
  );
  composites.push({ input: thumb, left, top });
  composites.push({ input: label, left, top: top + thumbH });
}

await canvas.composite(composites).png().toFile(path.join(outDir, "contact-sheet.png"));

if (errors.length) {
  console.error(JSON.stringify({ status: "error", errors }, null, 2));
  process.exit(1);
}
console.log(JSON.stringify({ status: "ok", slides: files.length, contactSheet: "screenshots/contact-sheet.png" }));
