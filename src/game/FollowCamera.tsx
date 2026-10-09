import { useFrame, useThree } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import { input } from './input'
import { playerState } from './playerState'

const DIST = 6.4
const HEIGHT = 3.1
const LOOK_Y = 1.15

/** ?camdebug=1 — проекция игрока в document.title (для headless-проверки кадра). */
const DEBUG = new URLSearchParams(location.search).has('camdebug')

/** Камера от третьего лица: висит за спиной, слушается поворота пальцем. */
export function FollowCamera() {
  const camera = useThree((s) => s.camera)
  const desired = useRef(new THREE.Vector3())
  const target = useMemo(() => new THREE.Vector3(), [])
  const look = useRef(new THREE.Vector3())

  useFrame((_, dt) => {
    const yaw = input.cameraYaw
    const fx = Math.sin(yaw)
    const fz = Math.cos(yaw)
    target.set(playerState.pos.x, 0, playerState.pos.z)
    desired.current.set(
      target.x - fx * DIST,
      HEIGHT,
      target.z - fz * DIST,
    )
    const k = 1 - Math.pow(0.0016, Math.min(dt, 0.05))
    camera.position.lerp(desired.current, k)
    look.current.set(target.x, LOOK_Y, target.z)
    camera.lookAt(look.current)

    if (DEBUG) {
      const p = desired.current
        .set(playerState.pos.x, 1.0, playerState.pos.z)
        .project(camera)
      document.title = `GAME px=${playerState.pos.x.toFixed(2)} pz=${playerState.pos.z.toFixed(
        2,
      )} spd=${playerState.speed.toFixed(2)} ndc=${p.x.toFixed(2)},${p.y.toFixed(2)},${p.z.toFixed(2)}`
    }
  })

  return null
}
