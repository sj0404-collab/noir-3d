import { useGLTF, useAnimations } from '@react-three/drei'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'


/**
 * Персонаж из Blender (glTF со скелетом и клипами).
 * Управляется параметрами URL для покадрового рендера:
 *   ?model=1&clip=Walk&t=0.35   — поставить позу на 35% клипа
 */
export function Detective({
  clip = 'Idle',
  time = 0,
  position = [0, 0, 0],
  rotationY = 0,
  scale = 1,
}: {
  clip?: string
  time?: number
  position?: [number, number, number]
  rotationY?: number
  scale?: number
}) {
  const { scene, animations } = useGLTF('/models/detective.glb')
  const { actions, names } = useAnimations(animations, scene)
  const group = useRef<THREE.Group>(null)

  const cloned = useMemo(() => {
    const s = scene.clone(true)
    s.traverse((o) => {
      const m = o as THREE.Mesh
      if (m.isMesh) {
        m.castShadow = true
        m.receiveShadow = true
        m.frustumCulled = false
        const mats = Array.isArray(m.material) ? m.material : [m.material]
        mats.forEach((mat) => {
          const mm = mat as THREE.MeshStandardMaterial
          if (mm && 'roughness' in mm) {
            mm.envMapIntensity = 0.9
          }
        })
      }
    })
    return s
  }, [scene])

  useEffect(() => {
    const act = actions[clip] ?? actions[names[0]]
    if (!act) return
    act.reset()
    act.setLoop(THREE.LoopRepeat, Infinity)
    act.play()
    act.paused = true
    act.time = time
  }, [actions, names, clip, time, cloned])

  // держим точку по времени параметра (детерминированно для рендера)
  useFrame(() => {
    const act = actions[clip]
    if (act) {
      act.paused = true
      act.time = time
    }
  })

  return (
    <group ref={group} position={position} rotation={[0, rotationY, 0]} scale={scale}>
      <primitive object={cloned} />
    </group>
  )
}

useGLTF.preload('/models/detective.glb')
