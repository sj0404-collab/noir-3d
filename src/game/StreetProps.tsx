import { useMemo } from 'react'

type Item = {
  kind: 'bin' | 'crate' | 'hydrant' | 'box'
  x: number
  z: number
  rot: number
  s: number
}

function seedTable(seed: number, n: number, pads: { x: number; z: number }[]) {
  let s = seed
  const rnd = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    return s / 0x7fffffff
  }
  const kinds: Item['kind'][] = ['bin', 'crate', 'box', 'hydrant', 'crate', 'bin', 'box']
  const out: Item[] = []
  for (let i = 0; i < n; i++) {
    const side = rnd() > 0.5 ? 1 : -1
    const nearCurb = rnd() > 0.5
    out.push({
      kind: kinds[i % kinds.length],
      x: side * (nearCurb ? 7.0 + rnd() * 1.4 : 9.2 + rnd() * 2.2),
      z: pads[i % pads.length].z,
      rot: rnd() * Math.PI * 2,
      s: 0.85 + rnd() * 0.5,
    })
  }
  return out
}

/** Набор уличной мелочи на тротуарах: баки, ящики, гидрант. Без новых лайтов. */
export function StreetProps() {
  const pads = useMemo(
    () => [
      { x: 1, z: -20 },
      { x: 1, z: -13 },
      { x: 1, z: -6 },
      { x: 1, z: 2 },
      { x: 1, z: 9 },
      { x: 1, z: 16 },
    ],
    [],
  )

  const props = useMemo(() => seedTable(99, 16, pads), [pads])
  const hydrants = props.filter((p) => p.kind === 'hydrant')
  const bins = props.filter((p) => p.kind === 'bin')
  const crates = props.filter((p) => p.kind === 'crate' || p.kind === 'box')

  const list = (items: Item[], color: string) =>
    items.map((p, i) => (
      <mesh
        key={`${i}-${p.kind}`}
        position={[p.x, 0.02, p.z]}
        rotation={[0, p.rot, 0]}
        scale={p.s}
        castShadow
      >
        <boxGeometry args={[0.24, 0.34, 0.24]} />
        <meshStandardMaterial color={color} roughness={0.9} metalness={0.05} />
      </mesh>
    ))

  return (
    <group>
      {list(bins, '#2a2e38')}
      {list(crates, '#4a3620')}
      {hydrants.map((p, i) => (
        <group
          key={`h${i}`}
          position={[p.x, 0.02, p.z]}
          rotation={[0, p.rot, 0]}
          scale={p.s}
        >
          <mesh castShadow>
            <cylinderGeometry args={[0.09, 0.09, 0.34, 12]} />
            <meshStandardMaterial color="#8d2b1d" roughness={0.6} metalness={0.3} />
          </mesh>
          <mesh position={[0, 0.17, 0]} castShadow>
            <cylinderGeometry args={[0.055, 0.055, 0.12, 10]} />
            <meshStandardMaterial color="#8d2b1d" roughness={0.6} metalness={0.3} />
          </mesh>
        </group>
      ))}
    </group>
  )
}