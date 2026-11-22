// Run once from the frontend folder:  node scripts/fetch-plant-images.mjs
// Downloads one photo per plant from Wikipedia into public/plants/ (needs Node 18+).
import { mkdir, writeFile, access } from "node:fs/promises";
import { PLANTS, slug } from "../src/plantData.js";

const OUT = new URL("../public/plants/", import.meta.url);
const HEADERS = { "User-Agent": "TripuraPlantGuide/0.1 (student project)" };
const pause = (ms) => new Promise((r) => setTimeout(r, ms));
const failed = [];

await mkdir(OUT, { recursive: true });

for (const p of PLANTS) {
  const file = new URL(`${slug(p.name)}.jpg`, OUT);
  try { await access(file); console.log("have   ", p.name); continue; } catch { /* not downloaded yet */ }

  try {
    const title = encodeURIComponent((p.wiki || p.name).replace(/ /g, "_"));
    const res = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${title}`, { headers: HEADERS });
    if (!res.ok) throw new Error(`page ${res.status}`);
    const thumb = (await res.json()).thumbnail?.source;
    if (!thumb) throw new Error("no photo on Wikipedia");

    let img = await fetch(thumb.replace(/\/\d+px-/, "/500px-"), { headers: HEADERS });
    if (!img.ok) img = await fetch(thumb, { headers: HEADERS });
    if (!img.ok) throw new Error(`image ${img.status}`);

    await writeFile(file, Buffer.from(await img.arrayBuffer()));
    console.log("saved  ", p.name);
  } catch (e) {
    failed.push(p.name);
    console.log("FAILED ", p.name, "-", e.message);
  }
  await pause(2000);
}

console.log(failed.length
  ? `\nAdd these by hand to public/plants/: ${failed.map((n) => slug(n) + ".jpg").join(", ")}`
  : "\nAll images saved.");
