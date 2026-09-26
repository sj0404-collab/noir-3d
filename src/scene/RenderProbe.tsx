import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useRef } from 'react'

/**
 * Ставит window.__ready после нескольких стабильных кадров — сигнал для
 * headless-захвата (tools/capture.mjs), чтобы снимать уже дорисованный кадр.
 * Опционально пишет диагностику в document.title.
 */
export function RenderProbe({
  warmupFrames = 3,
  onReady,
  probe = false,
}: {
  warmupFrames?: number
  onReady?: () => void
  probe?: boolean
}) {
  const gl = useThree((s) => s.gl)
  const size = useThree((s) => s.size)
  const count = useRef(0)
  const announced = useRef(false)
  const done = useRef(false)

  useEffect(() => {
    if (probe) {
      document.title = `PROBE init size=${size.width}x${size.height} buf=${gl.domElement.width}x${gl.domElement.height}`
    }
  }, [gl, size.width, size.height, probe])

  useFrame(() => {
    if (announced.current) return
    count.current += 1
    if (count.current < warmupFrames) return
    announced.current = true

    if (probe) {
      const ctx = gl.getContext()
      const w = gl.domElement.width
      const h = gl.domElement.height
      const px = new Uint8Array(4)
      try {
        ctx.readPixels(Math.floor(w / 2), Math.floor(h / 2), 1, 1, ctx.RGBA, ctx.UNSIGNED_BYTE, px)
        document.title = `PROBE canvas=${gl.domElement.clientWidth}x${gl.domElement.clientHeight} buf=${w}x${h} center=${px[0]},${px[1]},${px[2]} calls=${gl.info.render.calls} tris=${gl.info.render.triangles}`
      } catch (e) {
        document.title = `PROBE readPixels fail ${String(e).slice(0, 140)}`
      }
    }

    // сигнал готовности после реального кадра
    requestAnimationFrame(() => {
      setTimeout(() => {
        ;(window as unknown as { __ready?: boolean }).__ready = true
        onReady?.()
      }, 60)
    })
  })

  void done
  return null
}
