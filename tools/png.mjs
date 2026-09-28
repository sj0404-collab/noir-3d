#!/usr/bin/env node
/**
 * Статистика по PNG без внешних зависимостей: нужен способ отличить
 * «кадр есть» от «буфер пустой». `readPixels` из дефолтного WebGL-буфера
 * без preserveDrawingBuffer всегда даёт нули, а `gl.info.render.calls` после
 * пост-обработки показывает только финальный полноэкранный пасс (1 call,
 * 1 triangle) — обе проверки врут. Поэтому декодируем сам скриншот.
 *
 * usage: node tools/png.mjs <file.png> [file2.png ...]
 *        import { readPngStats } from './png.mjs'
 */
import { readFileSync } from 'node:fs'
import { inflateSync } from 'node:zlib'

const SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
const CHANNELS = { 0: 1, 2: 3, 4: 2, 6: 4 }

/** Возвращает { width, height, mean, stddev, black } — mean/stddev по яркости. */
export function readPngStats(path) {
  const buf = readFileSync(path)
  if (!buf.subarray(0, 8).equals(SIGNATURE)) throw new Error(`${path}: не PNG`)

  let width = 0
  let height = 0
  let depth = 0
  let type = 0
  let interlace = 0
  const idat = []

  let off = 8
  while (off + 8 <= buf.length) {
    const len = buf.readUInt32BE(off)
    const kind = buf.toString('ascii', off + 4, off + 8)
    const body = buf.subarray(off + 8, off + 8 + len)
    if (kind === 'IHDR') {
      width = body.readUInt32BE(0)
      height = body.readUInt32BE(4)
      depth = body[8]
      type = body[9]
      interlace = body[12]
    } else if (kind === 'IDAT') {
      idat.push(body)
    } else if (kind === 'IEND') {
      break
    }
    off += 12 + len
  }
  if (depth !== 8) throw new Error(`${path}: битность ${depth} не поддерживается`)
  if (interlace !== 0) throw new Error(`${path}: interlaced PNG не поддерживается`)
  const ch = CHANNELS[type]
  if (!ch) throw new Error(`${path}: тип цвета ${type} не поддерживается`)

  const raw = inflateSync(Buffer.concat(idat))
  const stride = width * ch
  const px = Buffer.alloc(height * stride)
  const line = Buffer.alloc(stride)
  const prev = Buffer.alloc(stride)

  let p = 0
  for (let y = 0; y < height; y++) {
    const filter = raw[p++]
    raw.copy(line, 0, p, p + stride)
    p += stride
    unfilter(filter, line, prev, ch)
    line.copy(px, y * stride)
    line.copy(prev)
  }

  // яркость по subsample, чтобы не жечь CPU на кадрах 1600x900
  const step = Math.max(1, Math.floor((width * height) / 60000))
  let sum = 0
  let sum2 = 0
  let n = 0
  let black = 0
  for (let i = 0; i < width * height; i += step) {
    const o = i * ch
    const luma = 0.2126 * px[o] + 0.7152 * px[o + Math.min(1, ch - 1)] + 0.0722 * px[o + Math.min(2, ch - 1)]
    sum += luma
    sum2 += luma * luma
    if (luma < 0.6) black++
    n++
  }
  const mean = sum / n
  return {
    width,
    height,
    mean,
    stddev: Math.sqrt(Math.max(0, sum2 / n - mean * mean)),
    black: black / n,
  }
}

function unfilter(filter, line, prev, bpp) {
  for (let i = 0; i < line.length; i++) {
    const a = i >= bpp ? line[i - bpp] : 0
    const b = prev[i]
    const c = i >= bpp ? prev[i - bpp] : 0
    switch (filter) {
      case 0:
        break
      case 1:
        line[i] = (line[i] + a) & 0xff
        break
      case 2:
        line[i] = (line[i] + b) & 0xff
        break
      case 3:
        line[i] = (line[i] + ((a + b) >> 1)) & 0xff
        break
      case 4: {
        const p = a + b - c
        const pa = Math.abs(p - a)
        const pb = Math.abs(p - b)
        const pc = Math.abs(p - c)
        const pr = pa <= pb && pa <= pc ? a : pb <= pc ? b : c
        line[i] = (line[i] + pr) & 0xff
        break
      }
      default:
        throw new Error(`неизвестный PNG-фильтр ${filter}`)
    }
  }
}

if (process.argv[1] === import.meta.filename) {
  for (const f of process.argv.slice(2)) {
    const s = readPngStats(f)
    const empty = s.stddev < 1.2 && s.mean < 6
    console.log(
      `${f} ${s.width}x${s.height} mean=${s.mean.toFixed(2)} stddev=${s.stddev.toFixed(2)} ` +
        `black=${(s.black * 100).toFixed(1)}% ${empty ? 'ПУСТО' : 'ok'}`,
    )
    process.exitCode = empty ? 1 : 0
  }
}
