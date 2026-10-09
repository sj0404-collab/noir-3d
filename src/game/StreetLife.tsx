import { useAnimations, useGLTF } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js'

const TRAM = '/models/tram.glb'
const CAR = '/models/car.glb'
const DETECTIVE = '/models/detective.glb'
const Z_MIN = -44
const Z_MAX = 44

function useSeeded(seed: number) {
  return useMemo(() => {
    let s = seed
    return () => {
      s = (s * 1103515245 + 12345) & 0x7fffffff
      return s / 0x7fffffff
    }
  }, [seed])
}

/** Трамвай патрулирует улицу: без теней и лишних лайтов, но с анимацией хода. */
function Tram() {
  const { scene, animations } = useGLTF(TRAM)
  const { actions } = useAnimations(animations, scene)
  const ref = useRef<THREE.Group>(null)
  const z = useRef(-40)

  useEffect(() => {
    const a = actions.Run
    if (a) {
      a.reset()
      a.play()
      a.timeScale = 1
    }
    scene.traverse((o) => {
      o.castShadow = false
      o.receiveShadow = false
      o.frustumCulled = true
    })
  }, [actions, scene])

  useFrame((_, dt) => {
    z.current += 6.2 * Math.min(dt, 0.05)
    if (z.current > Z_MAX) z.current = Z_MIN
    const g = ref.current
    if (g) {
      g.position.set(0, 0.02, z.current)
      g.rotation.y = 0
    }
  })

  return (
    <group ref={ref} position={[0, 0.02, -40]}>
      <primitive object={scene} />
    </group>
  )
}

/** Служебная машина, которая едет по своей полосе. */
function Sedan({
  x,
  dir,
  speed,
  z0,
  siren,
}: {
  x: number
  dir: -1 | 1
  speed: number
  z0: number
  siren?: boolean
}) {
  const { scene, animations } = useGLTF(CAR)
  const { actions } = useAnimations(animations, scene)
  const ref = useRef<THREE.Group>(null)
  const z = useRef(z0)

  useEffect(() => {
    const a = actions[siren ? 'Siren' : 'Drive']
    if (a) {
      a.reset()
      a.play()
      a.timeScale = 1
    }
    scene.traverse((o) => {
      o.castShadow = false
      o.receiveShadow = false
      o.frustumCulled = true
    })
  }, [actions, scene, siren])

  useFrame((_, dt) => {
    z.current += dir * speed * Math.min(dt, 0.05)
    if (z.current > Z_MAX) z.current = Z_MIN
    if (z.current < Z_MIN) z.current = Z_MAX
    const g = ref.current
    if (g) {
      g.position.set(x, 0.02, z.current)
      g.rotation.y = dir > 0 ? 0 : Math.PI
    }
  })

  return (
    <group ref={ref} position={[x, 0.02, z0]}>
      <primitive object={scene} />
    </group>
  )
}

/** Прохожий: клон детектива с циклом Idle или Walk. */
function Pedestrian({
  x,
  dir = 1,
  speed = 1.2,
  z0,
  clip = 'Walk',
}: {
  x: number
  dir?: -1 | 1
  speed?: number
  z0: number
  clip?: 'Idle' | 'Walk' | 'Scan' | 'Point'
}) {
  const { scene, animations } = useGLTF(DETECTIVE)
  const clone = useMemo(() => cloneSkeleton(scene), [scene])
  const { actions } = useAnimations(animations, clone)
  const ref = useRef<THREE.Group>(null)
  const z = useRef(z0)

  useEffect(() => {
    const a = actions[clip]
    if (a) {
      a.reset()
      a.play()
      a.timeScale = 1.05
    }
    clone.traverse((o) => {
      o.castShadow = false
      o.frustumCulled = true
    })
  }, [actions, clip, clone])

  useFrame((_, dt) => {
    z.current += dir * speed * Math.min(dt, 0.05)
    if (z.current > Z_MAX) z.current = Z_MIN
    if (z.current < Z_MIN) z.current = Z_MAX
    const g = ref.current
    if (g) {
      g.position.set(x, 0.02, z.current)
      g.rotation.y = dir > 0 ? 0 : Math.PI
    }
  })

  return (
    <group ref={ref} position={[x, 0.02, z0]}>
      <primitive object={clone} />
    </group>
  )
}

/** Оживляет улицу: трамвай, две машины, прохожие. */
export function StreetLife() {
  const rnd = useSeeded(7)

  // статичные «зрители» на тротуарах — где именно стоять
  const bystanders = useMemo(
    () =>
      [0, 1, 2].map((i) => ({
        x: (rnd() > 0.5 ? 1 : -1) * (5.4 + rnd() * 1.6),
        z: -16 + (i * 14) + rnd() * 4,
        clip: (rnd() > 0.5 ? 'Scan' : 'Idle') as 'Scan' | 'Idle',
      })),
    [rnd],
  )

  const walkers = useMemo(
    () => [
      { x: 6.4, dir: -1 as const, z0: -20 },
      { x: -6.8, dir: 1 as const, z0: 30 },
    ],
    [],
  )

  return (
    <group>
      <Tram />
      <Sedan x={-2.7} dir={-1} speed={7.5} z0={26} />
      <Sedan x={2.7} dir={1} speed={6.2} z0={-30} siren />
      {walkers.map((w, i) => (
        <Pedestrian key={`w${i}`} x={w.x} dir={w.dir} z0={w.z0} />
      ))}
      {bystanders.map((b, i) => (
        <Pedestrian key={`b${i}`} x={b.x} z0={b.z} clip={b.clip} speed={0} />
      ))}
    </group>
  )
}