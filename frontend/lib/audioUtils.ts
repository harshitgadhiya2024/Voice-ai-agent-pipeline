/**
 * PCM helpers and resampling utilities (browser).
 */

/** Float32 [-1, 1] -> 16-bit signed PCM little-endian. */
export function float32ToInt16(input: Float32Array): Int16Array {
  const out = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    let s = input[i];
    if (s > 1) s = 1;
    else if (s < -1) s = -1;
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}

/** 16-bit signed PCM -> Float32 [-1, 1]. */
export function int16ToFloat32(input: Int16Array): Float32Array {
  const out = new Float32Array(input.length);
  for (let i = 0; i < input.length; i++) {
    out[i] = input[i] / 0x8000;
  }
  return out;
}

/**
 * Linear resample a Float32 buffer from `srcRate` to `dstRate`.
 * Cheap & good enough for voice; we usually go 48000 -> 16000.
 */
export function resampleFloat32(
  input: Float32Array,
  srcRate: number,
  dstRate: number,
): Float32Array {
  if (srcRate === dstRate) return input;
  const ratio = srcRate / dstRate;
  const newLen = Math.floor(input.length / ratio);
  const out = new Float32Array(newLen);
  let pos = 0;
  for (let i = 0; i < newLen; i++) {
    const idx = i * ratio;
    const i0 = Math.floor(idx);
    const i1 = Math.min(i0 + 1, input.length - 1);
    const frac = idx - i0;
    out[pos++] = input[i0] * (1 - frac) + input[i1] * frac;
  }
  return out;
}

/** Concatenate Float32Arrays. */
export function concatFloat32(chunks: Float32Array[]): Float32Array {
  let total = 0;
  for (const c of chunks) total += c.length;
  const out = new Float32Array(total);
  let off = 0;
  for (const c of chunks) {
    out.set(c, off);
    off += c.length;
  }
  return out;
}

/** Pack a Float32Array into an ArrayBuffer of 16-bit PCM little-endian. */
export function float32ToPCM16Buffer(input: Float32Array): ArrayBuffer {
  const i16 = float32ToInt16(input);
  // Int16Array is platform endian; force little-endian for safety.
  const buf = new ArrayBuffer(i16.length * 2);
  const view = new DataView(buf);
  for (let i = 0; i < i16.length; i++) {
    view.setInt16(i * 2, i16[i], true);
  }
  return buf;
}

/** Decode 16-bit PCM little-endian ArrayBuffer -> Float32Array. */
export function pcm16BufferToFloat32(buffer: ArrayBuffer): Float32Array {
  const view = new DataView(buffer);
  const samples = buffer.byteLength / 2;
  const out = new Float32Array(samples);
  for (let i = 0; i < samples; i++) {
    out[i] = view.getInt16(i * 2, true) / 0x8000;
  }
  return out;
}
