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

/** Камера от третьего лица: демпфированный шлейф за игроком, взгляд чуть
 *  в сторону движения — ощущается тяжелее и плавнее, без рывков на стыках. */
export function FollowCamera() {
  const camera = useThree((s) => s.camera)
  const desired = useRef(new THREE.Vector3())
  const target = useMemo(() => new THREE.Vector3(), [])
  const look = useRef(new THREE.Vector3())
  const prev = useRef(new THREE.Vector3(playerState.pos.x, 0, playerState.pos.z))

  useFrame((_, dt) => {
    const yaw = input.cameraYaw
    const fx = Math.sin(yaw)
    const fz = Math.cos(yaw)
    const step = Math.min(dt, 0.05)
    target.set(playerState.pos.x, 0, playerState.pos.z)

    // скорости для упреждающего взгляда
    const vx = step > 0 ? (target.x - prev.current.x) / step : 0
    const vz = step > 0 ? (target.z - prev.current.z) / step : 0
    prev.current.copy(target)
    let lx = target.x + vx * 0.32
    let lz = target.z + vz * 0.32
    const vlen = Math.hypot(vx, vz)
    const maxLead = 1.4
    if (vlen * 0.32 > maxLead) {
      const s = maxLead / (vlen * 0.32)
      lx = target.x + (lx - target.x) * s
      lz = target.z + (lz - target.z) * s
    }
    look.current.set(lx, LOOK_Y, lz)

    desired.current.set(
      target.x - fx * DIST - vx * 0.18,
      HEIGHT,
      target.z - fz * DIST - vz * 0.18,
    )
    const d = 5.2
    camera.position.x = THREE.MathUtils.damp(camera.position.x, desired.current.x, d, step)
    camera.position.y = THREE.MathUtils.damp(camera.position.y, desired.current.y, d, step)
    camera.position.z = THREE.MathUtils.damp(camera.position.z, desired.current.z, d, step)
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
