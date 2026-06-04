#!/usr/bin/env node
/**
 * Copies runtime assets needed by @ricky0123/vad-web + onnxruntime-web into
 * `public/` so they are served as static files by Next.js.
 *
 * Why this is needed:
 *  - onnxruntime-web loads its WASM glue (`ort-wasm-simd-threaded.*.mjs`)
 *    via dynamic `import()` at runtime. When bundled by Next.js webpack,
 *    the relative import resolves to `/_next/static/chunks/...` which
 *    doesn't exist → 404 → VAD never initialises.
 *  - The VAD AudioWorklet must be served from a public URL since worklets
 *    can't be bundled into the main JS graph.
 *  - The Silero model isn't shipped in the npm package; we fetch it once
 *    from the official CDN and cache it in `public/`.
 *
 * Run automatically before dev/build via npm scripts.
 */
import fs from "node:fs";
import path from "node:path";
import https from "node:https";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const publicDir = path.join(root, "public");
const ortDir = path.join(root, "node_modules", "onnxruntime-web", "dist");
const vadDir = path.join(root, "node_modules", "@ricky0123", "vad-web", "dist");

fs.mkdirSync(publicDir, { recursive: true });

function copyIfChanged(src, dst) {
  if (!fs.existsSync(src)) return false;
  const srcStat = fs.statSync(src);
  if (fs.existsSync(dst)) {
    const dstStat = fs.statSync(dst);
    if (dstStat.size === srcStat.size && dstStat.mtimeMs >= srcStat.mtimeMs) {
      return false;
    }
  }
  fs.copyFileSync(src, dst);
  console.log(`  copied ${path.basename(src)}`);
  return true;
}

function copyGlob(srcDir, pattern, dstDir) {
  if (!fs.existsSync(srcDir)) {
    console.warn(`  (skipped: ${srcDir} not found)`);
    return 0;
  }
  const entries = fs.readdirSync(srcDir);
  let n = 0;
  for (const name of entries) {
    if (!pattern.test(name)) continue;
    if (copyIfChanged(path.join(srcDir, name), path.join(dstDir, name))) n++;
  }
  return n;
}

async function downloadIfMissing(url, dst) {
  if (fs.existsSync(dst) && fs.statSync(dst).size > 0) return false;
  console.log(`  downloading ${path.basename(dst)} ...`);
  await new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dst);
    const request = (u) => {
      https
        .get(u, (res) => {
          if (
            res.statusCode &&
            res.statusCode >= 300 &&
            res.statusCode < 400 &&
            res.headers.location
          ) {
            request(res.headers.location);
            return;
          }
          if (res.statusCode !== 200) {
            reject(
              new Error(
                `Failed to download ${u}: HTTP ${res.statusCode}`,
              ),
            );
            return;
          }
          res.pipe(file);
          file.on("finish", () => file.close(resolve));
        })
        .on("error", reject);
    };
    request(url);
  });
  console.log(`  saved ${path.basename(dst)}`);
  return true;
}

console.log("[vad-assets] syncing public/ ...");

// 1) ONNX Runtime Web — WASM loader glue + actual WASM binaries.
const ortCopied = copyGlob(
  ortDir,
  /^ort-wasm-simd-threaded\.(?:[a-z]+\.)?(?:mjs|wasm)$/,
  publicDir,
);

// 2) VAD audio worklet.
const vadCopied = copyIfChanged(
  path.join(vadDir, "vad.worklet.bundle.min.js"),
  path.join(publicDir, "vad.worklet.bundle.min.js"),
)
  ? 1
  : 0;

// 3) Silero VAD ONNX model — not shipped in the npm package.
//    Pulled once from the official CDN.
const SILERO_MODEL_URL =
  "https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.19/dist/silero_vad.onnx";
try {
  await downloadIfMissing(
    SILERO_MODEL_URL,
    path.join(publicDir, "silero_vad.onnx"),
  );
} catch (e) {
  console.warn(`  WARN could not fetch silero_vad.onnx: ${e.message}`);
  console.warn("  VAD will still work if the file is present in public/.");
}

console.log(
  `[vad-assets] done (ORT files: ${ortCopied} updated, VAD worklet: ${vadCopied} updated)`,
);
