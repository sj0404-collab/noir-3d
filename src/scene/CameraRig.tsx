import { useThree, useFrame } from '@react-three/fiber'
import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export type CamSpec = {
  az: number
  el: number
  dist: number
  target: [number, number, number]
  fov: number
}

/**
 * Камера, управляемая query-параметрами — чтобы рендерить кадры по сценарию:
 *   ?az=45&el=12&dist=9&ty=1.2&fov=40
 * Позволяет снимать одни и те же ракурсы детерминированно (для видео).
 */
function readSpec(): CamSpec {
  const q = new URLSearchParams(location.search)
  const n = (k: string, d: number) => {
    const v = parseFloat(q.get(k) ?? '')
    return Number.isFinite(v) ? v : d
  }
  return {
    az: n('az', 28),
    el: n('el', 10),
    dist: n('dist', 11),
    target: [n('tx', 0), n('ty', 1.4), n('tz', 0)],
    fov: n('fov', 42),
  }
}

export function useCamSpec() {
  return useRef<CamSpec>(readSpec())
}

export function CameraRig({ enabled = true }: { enabled?: boolean }) {
  const { camera } = useThree()
  const spec = useRef<CamSpec>(readSpec())
  const applied = useRef(false)

  useEffect(() => {
    const cam = camera as THREE.PerspectiveCamera
    cam.fov = spec.current.fov
    cam.updateProjectionMatrix()
  }, [camera])

  useFrame(({ gl }) => {
    if (!enabled || applied.current) return
    applied.current = true
    const { az, el, dist, target } = spec.current
    const a = THREE.MathUtils.degToRad(az)
    const e = THREE.MathUtils.degToRad(el)
    const x = target[0] + dist * Math.cos(e) * Math.sin(a)
    const y = target[1] + dist * Math.sin(e)
    const z = target[2] + dist * Math.cos(e) * Math.cos(a)
    camera.position.set(x, y, z)
    camera.lookAt(target[0], target[1], target[2])
    const d = new THREE.Vector3()
    camera.getWorldDirection(d)
    document.title = `CAM pos=${camera.position.toArray().map((n) => n.toFixed(1))} dir=${d
      .toArray()
      .map((n) => n.toFixed(2))} drawCalls=${gl.info.render.calls} tris=${gl.info.render.triangles}`
  })

  return null
}
