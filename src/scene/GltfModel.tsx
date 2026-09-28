import { useGLTF, useAnimations } from '@react-three/drei'
import { useEffect, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

/**
 * Ригнутая glTF-модель с детерминированной позой: клип ставится на паузу и
 * держится на времени из параметров URL, чтобы кадры рендерились покадрово
 * (видео клипов не «плывут» между прогонами).
 *
 *   ?clip=Walk&t=0.35
 *
 * Геометрия клонируется, чтобы несколько копий модели в одной сцене не делили
 * скелет: анимации ведутся на клоне, тени и frustum выставляются явно.
 */
export function GltfModel({
  src,
  clip = 'Idle',
  time = 0,
  position = [0, 0, 0],
  rotationY = 0,
  scale = 1,
  envMapIntensity = 0.9,
}: {
  src: string
  clip?: string
  time?: number
  position?: [number, number, number]
  rotationY?: number
  scale?: number
  envMapIntensity?: number
}) {
  const { scene, animations } = useGLTF(src)
  const { actions, names } = useAnimations(animations, scene)

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
            mm.envMapIntensity = envMapIntensity
          }
        })
      }
    })
    return s
  }, [scene, envMapIntensity])

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
    <group position={position} rotation={[0, rotationY, 0]} scale={scale}>
      <primitive object={cloned} />
    </group>
  )
}
