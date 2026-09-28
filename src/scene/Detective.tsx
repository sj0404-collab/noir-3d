import { useGLTF } from '@react-three/drei'
import { GltfModel } from './GltfModel'

/**
 * Персонаж из Blender (glTF со скелетом и клипами).
 * Управляется параметрами URL для покадрового рендера:
 *   ?scene=model&clip=Walk&t=0.35   — поставить позу на 35% клипа
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
  return (
    <GltfModel
      src="/models/detective.glb"
      clip={clip}
      time={time}
      position={position}
      rotationY={rotationY}
      scale={scale}
    />
  )
}

useGLTF.preload('/models/detective.glb')
