#!/usr/bin/env node
/**
 * Детерминированный захват кадров через Playwright + системный Chromium.
 * Ждёт сигнала `window.__ready` от сцены и только потом снимает кадр —
 * в отличие от `chromium --screenshot`, который может снять недоприсованный буфер.
 *
 * usage: node tools/capture.mjs <url> <out.png> [w] [h] [readyTimeoutMs]
 */
import { chromium } from 'playwright-core'

const [url, out, w = '1280', h = '720', readyTimeout = '90000'] = process.argv.slice(2)

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || '/usr/bin/chromium',
  args: [
    '--no-sandbox',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--disable-dev-shm-usage',
  ],
})

const page = await browser.newPage({
  viewport: { width: +w, height: +h },
  deviceScaleFactor: 1,
})

const logs = []
page.on('console', (m) => logs.push(`[${m.type()}] ${m.text()}`))
page.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}`))

await page.goto(url, { waitUntil: 'load', timeout: 60000 })

// сцена выставляет window.__ready после стабильных кадров
let ready = true
try {
  await page.waitForFunction('window.__ready === true', null, { timeout: +readyTimeout })
} catch {
  ready = false
}

await page.waitForTimeout(1200)

// SwiftShader рендерит медленно, поэтому кадр снимаем с большим таймаутом
await page.screenshot({ path: out, timeout: 180000, animations: 'allow' })
const title = await page.title()
await browser.close()

console.log(`OK ${out} ready=${ready} title=${JSON.stringify(title)}`)
if (logs.length) console.log('--- консоль страницы ---\n' + logs.slice(0, 20).join('\n'))
