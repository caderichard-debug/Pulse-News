import sharp from "sharp";
import fs from "fs";

const sizes = [16, 48, 128];
if (!fs.existsSync("icons")) fs.mkdirSync("icons");

for (const size of sizes) {
  await sharp("pulse-icon.png")
    .resize(size, size)
    .toFile(`icons/icon${size}.png`);
  console.log(`✅ Generated icon${size}.png`);
}