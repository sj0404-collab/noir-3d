import { useFrame, useThree } from '@react-three/fiber'
import { useRef } from 'react'

/**
 * Вращение камеры вокруг модели для turntable-ракурсов.
 * Угол задаётся параметром ?spin=<градусы> — детерминированно, без анимации,
 * чтобы покадрово рендерить видео.
 */
export function Turntable({ enabled = true }: { enabled?: boolean }) {
  const { camera } = useThree()
  const applied = useRef(false)
  const q = new URLSearchParams(location.search)
  const spin = parseFloat(q.get('spin') ?? '0')

  useFrame(() => {
    if (!enabled || applied.current) return
    applied.current = true
    const a = (spin * Math.PI) / 180
    const dist = parseFloat(q.get('dist') ?? '3.2')
    const el = (parseFloat(q.get('el') ?? '6') * Math.PI) / 180
    const ty = parseFloat(q.get('ty') ?? '1.0')
    const x = Math.sin(a) * dist * Math.cos(el)
    const z = Math.cos(a) * dist * Math.cos(el)
    const y = ty + dist * Math.sin(el)
    camera.position.set(x, y, z)
    camera.lookAt(0, ty, 0)
  })

  return null
}
