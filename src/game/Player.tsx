import { useGLTF, useAnimations } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js'
import { input, stickToWorld } from './input'
import { playerState, BOUNDS, WALK_SPEED, RUN_SPEED } from './playerState'
import { getState } from './state'

const DETECTIVE = '/models/detective.glb'

/**
 * timeScale клипов подогнан под реальный шаг детектива, чтобы ноги не
 * «скользили» по асфальту: Walk 1.5 м/цикл, Run 2.4 м/цикл.
 * Клипы: Walk 1.067 c (30 fps × 32), Run 0.8 c (24 кадра).
 */
const WALK_TIME_SCALE = 1.067 / (1.5 / WALK_SPEED)
const RUN_TIME_SCALE = 0.8 / (2.4 / RUN_SPEED)

/**
 * Управляемый детектив: скелет клонируется через SkeletonUtils, клипы
 * Idle/Walk/Run смешиваются по весам от скорости. Модель смотрит по +Z,
 * поэтому rotation.y = atan2(dir.x, dir.z).
 */
export function Player() {
  const { scene, animations } = useGLTF(DETECTIVE)
  const clone = useMemo(() => cloneSkeleton(scene), [scene])
  const { actions } = useAnimations(animations, clone)

  const group = useRef<THREE.Group>(null)
  const weights = useRef<Record<string, number>>({ Idle: 1, Walk: 0, Run: 0 })
  const target = useRef('Idle')
  const dir = useMemo(() => new THREE.Vector3(), [])

  useEffect(() => {
    for (const n of ['Idle', 'Walk', 'Run']) {
      const a = actions[n]
      if (a) {
        a.reset()
        a.setLoop(THREE.LoopRepeat, Infinity)
        a.setEffectiveWeight(n === 'Idle' ? 1 : 0)
        a.play()
      }
    }
  }, [actions])

  useFrame((_, dt) => {
    const g = group.current
    if (!g) return
    const step = Math.min(dt, 0.05)
    const playing = getState().phase === 'playing'

    const mag = playing ? Math.min(1, Math.hypot(input.mx, input.my)) : 0
    const running = mag > 0.82
    let speed = 0

    if (mag > 0.1) {
      stickToWorld(dir).normalize()
      speed = running ? RUN_SPEED : WALK_SPEED
      playerState.pos.addScaledVector(dir, speed * step)
      playerState.pos.x = THREE.MathUtils.clamp(playerState.pos.x, BOUNDS.minX, BOUNDS.maxX)
      playerState.pos.z = THREE.MathUtils.clamp(playerState.pos.z, BOUNDS.minZ, BOUNDS.maxZ)

      const want = Math.atan2(dir.x, dir.z)
      let diff = want - playerState.yaw
      diff = Math.atan2(Math.sin(diff), Math.cos(diff))
      playerState.yaw += diff * Math.min(1, step * 12)
    }

    playerState.speed = speed
    playerState.running = running

    // веса анимаций: демпфер вместо скачков — рука/нога не «бьётся» на стыке клипов
    const want = speed === 0 ? 'Idle' : running ? 'Run' : 'Walk'
    target.current = want
    for (const n of ['Idle', 'Walk', 'Run']) {
      const a = actions[n]
      if (!a) continue
      const cur = weights.current[n] ?? 0
      weights.current[n] = THREE.MathUtils.damp(cur, Number(n === want), 9, step)
      a.setEffectiveWeight(weights.current[n])
      if (n !== 'Idle') a.timeScale = running ? RUN_TIME_SCALE : WALK_TIME_SCALE
    }

    g.position.copy(playerState.pos)
    g.rotation.y = playerState.yaw
  })

  return (
    <group ref={group} position={playerState.pos} rotation={[0, playerState.yaw, 0]}>
      <primitive object={clone} />
    </group>
  )
}

useGLTF.preload(DETECTIVE)
