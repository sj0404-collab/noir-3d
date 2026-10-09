import { useRef } from 'react'
import { setStick } from '../game/input'

const SIZE = 132
const THUMB = 56
const MAX = SIZE / 2 - THUMB / 2 - 6

/**
 * Виртуальный стик. Двигает собственный DOM вручную (без React-стейта),
 * чтобы рычаг не вызывал ре-рендер на каждое касание.
 */
export function Joystick() {
  const base = useRef<HTMLDivElement>(null)
  const thumb = useRef<HTMLDivElement>(null)

  const move = (clientX: number, clientY: number) => {
    const el = base.current
    const th = thumb.current
    if (!el || !th) return
    const r = el.getBoundingClientRect()
    let dx = clientX - (r.left + r.width / 2)
    let dy = clientY - (r.top + r.height / 2)
    const len = Math.hypot(dx, dy)
    if (len > MAX) {
      dx = (dx / len) * MAX
      dy = (dy / len) * MAX
    }
    th.style.transform = `translate(${dx}px, ${dy}px)`
    setStick(dx / MAX, -dy / MAX)
  }

  const reset = () => {
    if (thumb.current) thumb.current.style.transform = 'translate(0px, 0px)'
    setStick(0, 0)
  }

  return (
    <div
      ref={base}
      onPointerDown={(e) => {
        e.currentTarget.setPointerCapture(e.pointerId)
        move(e.clientX, e.clientY)
      }}
      onPointerMove={(e) => {
        if (e.buttons === 0 && !e.currentTarget.hasPointerCapture(e.pointerId)) return
        move(e.clientX, e.clientY)
      }}
      onPointerUp={reset}
      onPointerCancel={reset}
      style={{
        position: 'relative',
        width: SIZE,
        height: SIZE,
        borderRadius: '50%',
        background: 'radial-gradient(circle at 50% 50%, rgba(40,60,90,0.30), rgba(8,14,26,0.42))',
        border: '1.5px solid rgba(120,170,240,0.35)',
        boxShadow: '0 0 24px rgba(0,0,0,0.45) inset',
        touchAction: 'none',
        pointerEvents: 'auto',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: '50% auto auto 50%',
          width: THUMB,
          height: THUMB,
          marginLeft: -THUMB / 2,
          marginTop: -THUMB / 2,
        }}
      >
        <div
          ref={thumb}
          style={{
            width: THUMB,
            height: THUMB,
            borderRadius: '50%',
            background: 'radial-gradient(circle at 40% 35%, #cfe2ff, #5f7fb8 60%, #2b3d5e)',
            border: '1.5px solid rgba(190,215,255,0.7)',
            boxShadow: '0 4px 14px rgba(0,0,0,0.5)',
            willChange: 'transform',
          }}
        />
      </div>
    </div>
  )
}
