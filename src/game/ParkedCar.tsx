import { useAnimations, useGLTF } from '@react-three/drei'
import { useEffect } from 'react'
import * as THREE from 'three'
import { EXIT_POS } from './state'

const CAR = '/models/car.glb'

/**
 * Полицейский седан — точка возврата. Рендерим оригинальную сцену (один
 * экземпляр, клон не нужен), колёса и мигалка крутятся клипом Siren.
 */
export function ParkedCar() {
  const { scene, animations } = useGLTF(CAR)
  const { actions } = useAnimations(animations, scene)

  useEffect(() => {
    scene.traverse((o) => {
      const m = o as THREE.Mesh
      if (m.isMesh) {
        m.castShadow = true
        m.receiveShadow = true
        m.frustumCulled = false
      }
    })
    const a = actions.Siren ?? actions.Idle
    if (a) {
      a.reset()
      a.play()
    }
    return () => {
      a?.stop()
    }
  }, [scene, actions])

  return (
    <group position={[EXIT_POS[0] + 0.4, 0.02, EXIT_POS[2] - 0.5]} rotation={[0, 0.06, 0]}>
      <primitive object={scene} />
      <pointLight position={[0, 1.9, 0]} intensity={1.3} distance={6} decay={2} color="#4fb0ff" />
    </group>
  )
}

useGLTF.preload(CAR)
