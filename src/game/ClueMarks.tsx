import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { CLUES, useGame } from './state'

/**
 * Метки улик: жёлтый следственный конус и пульсирующее кольцо.
 * Подобранные улики гаснут, но остаются отметкой в деле.
 */
export function ClueMarks() {
  const { found, nearClue } = useGame()
  return (
    <group>
      {CLUES.map((c) => (
        <ClueMark
          key={c.id}
          pos={c.pos}
          taken={!!found[c.id]}
          active={nearClue === c.id}
        />
      ))}
    </group>
  )
}

function ClueMark({
  pos,
  taken,
  active,
}: {
  pos: [number, number, number]
  taken: boolean
  active: boolean
}) {
  const ring = useRef<THREE.Mesh>(null)
  const beam = useRef<THREE.Mesh>(null)
  const t = useRef(Math.random() * 6)

  useFrame((_, dt) => {
    t.current += dt
    const pulse = 1 + Math.sin(t.current * 3.4) * (active ? 0.18 : 0.08)
    if (ring.current) {
      ring.current.rotation.z += dt * 0.9
      ring.current.scale.setScalar(pulse)
    }
    if (beam.current) {
      const m = beam.current.material as THREE.MeshBasicMaterial
      m.opacity = (taken ? 0.06 : 0.28) + Math.sin(t.current * 2.2) * 0.05
    }
  })

  const color = taken ? '#3ad0a0' : active ? '#ffd23a' : '#f2b229'

  return (
    <group position={[pos[0], 0, pos[2]]}>
      {/* вертикальный луч — видно издалека */}
      <mesh ref={beam} position={[0, 1.4, 0]}>
        <cylinderGeometry args={[0.05, 0.14, 2.8, 8, 1, true]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.28}
          side={THREE.DoubleSide}
          depthWrite={false}
          toneMapped={false}
        />
      </mesh>
      {/* кольцо у земли */}
      <mesh ref={ring} position={[0, 0.04, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.34, 0.46, 28]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={taken ? 0.35 : 0.9}
          side={THREE.DoubleSide}
          depthWrite={false}
          toneMapped={false}
        />
      </mesh>
      {/* дужка-держатель как у жёлтого маркера места преступления */}
      <mesh position={[0, 0.28, 0]} rotation={[0, 0, 0]}>
        <coneGeometry args={[0.16, 0.5, 4]} />
        <meshStandardMaterial
          color="#e8b21f"
          emissive={taken ? '#1f6b52' : '#8a5a00'}
          emissiveIntensity={taken ? 0.4 : 1.2}
          roughness={0.5}
          metalness={0.1}
        />
      </mesh>
      <pointLight
        position={[0, 0.6, 0]}
        intensity={taken ? 0.15 : 1.1}
        distance={4}
        decay={2}
        color={color}
      />
    </group>
  )
}
