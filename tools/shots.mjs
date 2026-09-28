#!/usr/bin/env node
/**
 * Скриншоты сцены в ../tmp/shots (см. MANIFEST.md — временное только туда).
 *
 * Поднимает статику dist/ на свободном порту и снимает фиксированный набор
 * ракурсов через tools/capture.mjs (Playwright + системный Chromium), чтобы
 * кадры были воспроизводимы. Сборка должна быть уже сделана: npm run build.
 *
 * usage: node tools/shots.mjs [--port 4173] [--out ../tmp/shots] [фильтр...]
 *   фильтр — подстрока имени кадра: node tools/shots.mjs car
 */
import { createServer } from 'node:http'
import { spawn } from 'node:child_process'
import { readFile, stat, mkdir, readdir } from 'node:fs/promises'
import { extname, join, relative, resolve } from 'node:path'
import { readPngStats } from './png.mjs'

const repoRoot = resolve(import.meta.dirname, '..')
const distDir = join(repoRoot, 'dist')

/** набор кадров: имя → { q: query, w, h } */
const SHOTS = [
  { name: 'street-wide', w: 1280, h: 720, q: 'az=18&el=8&dist=13&ty=1.5&dpr=1' },
  { name: 'street-deep', w: 1280, h: 720, q: 'az=64&el=3&dist=24&ty=2.2&dpr=1' },
  { name: 'street-herob', w: 1280, h: 720, q: 'az=-24&el=5&dist=7&ty=1.4&herob=1&clip=Idle&t=0.2&dpr=1' },
  { name: 'model-front', w: 640, h: 800, q: 'scene=model&clip=Idle&t=0&az=0&el=2&dist=3.2&ty=0.95&dpr=1' },
  { name: 'model-3q', w: 640, h: 800, q: 'scene=model&clip=Idle&t=0&az=35&el=6&dist=3.2&ty=0.95&dpr=1' },
  { name: 'model-walk', w: 640, h: 800, q: 'scene=model&clip=Walk&t=0.35&az=20&el=4&dist=3.2&ty=0.95&dpr=1' },
  { name: 'model-head', w: 720, h: 720, q: 'scene=model&clip=Idle&t=0&az=25&el=8&dist=1&ty=1.55&fov=32&dpr=1' },
  { name: 'car-drive', w: 1024, h: 640, q: 'scene=props&prop=car&clip=Drive&t=0.4&az=28&el=8&dpr=1' },
  { name: 'tram-run', w: 1024, h: 640, q: 'scene=props&prop=tram&clip=Run&t=0.25&az=24&el=6&dpr=1' },
  { name: 'kit-wide', w: 1024, h: 640, q: 'scene=props&prop=kit&clip=Wind&t=0.5&az=35&el=16&dpr=1' },
]

const MIN_BYTES = 20 * 1024

const argv = process.argv.slice(2)
let port = 4173
let outDir = resolve(repoRoot, '../tmp/shots')
const filters = []
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--port') port = Number(argv[++i])
  else if (argv[i] === '--out') outDir = resolve(repoRoot, argv[++i])
  else filters.push(argv[i])
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.glb': 'model/gltf-binary',
  '.gltf': 'model/gltf+json',
  '.bin': 'application/octet-stream',
  '.hdr': 'image/vnd.radiance',
  '.wasm': 'application/wasm',
}

/** статика dist/ — отдельный сервер, чтобы он умер вместе с этим скриптом */
function serveDist() {
  const server = createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? '/', 'http://127.0.0.1')
      let path = resolve(distDir, '.' + decodeURIComponent(url.pathname))
      if (!path.startsWith(distDir)) throw new Error('вне dist')
      let s = await stat(path).catch(() => null)
      if (s?.isDirectory()) {
        path = join(path, 'index.html')
        s = await stat(path).catch(() => null)
      }
      if (!s) {
        // SPA-роуты: всё неизвестное отдаём индексом
        path = join(distDir, 'index.html')
        s = await stat(path)
      }
      const body = await readFile(path)
      res.writeHead(200, {
        'content-type': MIME[extname(path)] ?? 'application/octet-stream',
        'content-length': body.length,
        'cache-control': 'no-store',
      })
      res.end(body)
    } catch (e) {
      res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' })
      res.end('404 ' + String(e))
    }
  })
  return new Promise((ok, fail) => {
    server.on('error', fail)
    server.listen(port, '127.0.0.1', () => ok(server))
  })
}

function capture(url, out, w, h) {
  return new Promise((ok) => {
    const p = spawn(
      process.execPath,
      [join(repoRoot, 'tools/capture.mjs'), url, out, String(w), String(h), '300000'],
      { cwd: repoRoot, stdio: ['ignore', 'pipe', 'pipe'] },
    )
    let buf = ''
    p.stdout.on('data', (d) => (buf += d))
    p.stderr.on('data', (d) => (buf += d))
    p.on('close', (code) => ok({ code, buf }))
  })
}

/** кадр считается пустым, если он почти одноцветный (см. tools/png.mjs) */
const isBlank = (s) => s.stddev < 1.2 && s.mean < 6

try {
  await stat(join(distDir, 'index.html'))
} catch {
  console.error('нет dist/index.html — сначала npm run build')
  process.exit(1)
}
await mkdir(outDir, { recursive: true })

const server = await serveDist()
const base = `http://127.0.0.1:${server.address().port}/`
console.log(`· статика: ${relative(repoRoot, distDir) || 'dist'} на ${base}`)
console.log(`· кадры: ${relative(repoRoot, outDir)}`)

const todo = filters.length ? SHOTS.filter((s) => filters.some((f) => s.name.includes(f))) : SHOTS
if (!todo.length) {
  console.error('по фильтру не нашлось кадров: ' + filters.join(', '))
  server.close()
  process.exit(2)
}

let failed = 0
let blank = 0
for (const shot of todo) {
  const out = join(outDir, shot.name + '.png')
  const t0 = Date.now()
  const { code, buf } = await capture(`${base}?${shot.q}`, out, shot.w, shot.h)
  const secs = ((Date.now() - t0) / 1000).toFixed(1)
  const title = /title="([^"]*)"/.exec(buf)?.[1] ?? ''
  const size = await stat(out).then((s) => s.size, () => 0)
  const notes = []
  if (code !== 0 || size < MIN_BYTES) {
    failed++
    notes.push(`FAIL(${code ?? 'нет файла'}, ${size} байт)`)
  } else {
    const s = readPngStats(out)
    if (isBlank(s)) {
      blank++
      failed++
      notes.push('ПУСТОЙ КАДР')
    }
    notes.push(`mean=${s.mean.toFixed(1)} stddev=${s.stddev.toFixed(1)}`)
    notes.push(`${(size / 1024).toFixed(0)} КБ`)
  }
  if (/ready=false/.test(buf)) notes.push('__ready не пришёл')
  console.log(`· ${shot.name.padEnd(12)} ${shot.w}x${shot.h} ${secs}s  ${notes.join(', ')}`)
  if (title) console.log(`  ${title}`)
}

server.close()
const files = (await readdir(outDir).catch(() => [])).filter((f) => f.endsWith('.png'))
console.log(`\n${files.length} PNG в ${relative(repoRoot, outDir)}; пустых: ${blank}; провалов: ${failed}`)
process.exit(failed ? 1 : 0)
