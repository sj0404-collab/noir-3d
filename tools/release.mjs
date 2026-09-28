#!/usr/bin/env node
/**
 * Правило репозитория: после КАЖДОГО пуша — коммит + GitHub Release.
 * Скрипт bumps версию в package.json, коммитит её, ставит тег vX.Y.Z,
 * пушит и создаёт релиз с ассетами из ../tmp/shots (если есть).
 *
 * usage: node tools/release.mjs "<сообщение релиза>" [patch|minor|major] [--dry]
 */
import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync, readdirSync, existsSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'

const [message, level = 'patch', ...flags] = process.argv.slice(2)
const dry = flags.includes('--dry')
const repoRoot = resolve(import.meta.dirname, '..')
const pkgPath = join(repoRoot, 'package.json')

if (!message) {
  console.error('нужно сообщение релиза: node tools/release.mjs "текст" [patch|minor|major]')
  process.exit(2)
}
if (!['patch', 'minor', 'major'].includes(level)) {
  console.error(`неизвестный уровень бампа: ${level}`)
  process.exit(2)
}

const git = (args, opts = {}) =>
  execFileSync('git', args, { cwd: repoRoot, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...opts })

const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'))
const [ma, mi, pa] = pkg.version.split('.').map(Number)
const next = {
  patch: [ma, mi, pa + 1],
  minor: [ma, mi + 1, 0],
  major: [ma + 1, 0, 0],
}[level].join('.')
const tag = `v${next}`

// 1. в репозитории не должно остаться незакоммиченных исходников
const dirty = git(['status', '--porcelain']).trim()
if (dirty) {
  console.error('есть незакоммиченные изменения — сначала коммит + push:\n' + dirty)
  process.exit(1)
}
if (git(['rev-list', '--count', `HEAD..origin/${currentBranch()}`]).trim() !== '0') {
  console.error('ветка не запушена: сначала git push origin ' + currentBranch())
  process.exit(1)
}

// 2. сборка должна проходить до релиза
console.log('· npm run build')
git(['--version']) // sanity
execFileSync('npm', ['run', 'build'], { cwd: repoRoot, stdio: 'inherit' })

// 3. версия + коммит
pkg.version = next
writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n')
const files = ['package.json', ...(existsSync(join(repoRoot, 'package-lock.json')) ? ['package-lock.json'] : [])]
git(['add', ...files])
git(['commit', '-m', `chore(release): ${tag} — ${message}`])

// 4. тег + пуш
git(['tag', '-a', tag, '-m', message])
if (dry) {
  console.log(`[dry] тег ${tag} создан локально, пуш и релиз пропущены`)
  process.exit(0)
}
git(['push', 'origin', currentBranch()])
git(['push', 'origin', tag])

// 5. релиз с ассетами
const shotsDir = resolve(repoRoot, '../tmp/shots')
const assets = existsSync(shotsDir)
  ? readdirSync(shotsDir)
      .filter((f) => /\.(png|mp4|webm|gif)$/i.test(f))
      .map((f) => join(shotsDir, f))
      .filter((f) => statSync(f).size > 1024)
  : []

const body = [
  message,
  '',
  `### Что нового в ${tag}`,
  '',
  'Скриншоты и модели лежат в ассетах релиза и в репозитории (`public/models`).',
  '',
  'Пересобрать локально: `npm ci && npm run models && npm run build`.',
  '',
  `Коммит: ${git(['rev-parse', '--short', 'HEAD']).trim()}`,
].join('\n')

const args = ['release', 'create', tag, '--title', `${tag} — ${message}`, '--notes', body]
for (const a of assets) args.push(a)
execFileSync('gh', args, { cwd: repoRoot, stdio: 'inherit' })
console.log(`[OK] релиз ${tag} создан, ассетов: ${assets.length}`)

function currentBranch() {
  return git(['rev-parse', '--abbrev-ref', 'HEAD']).trim()
}
