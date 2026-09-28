import { Grid } from '@react-three/drei'

/**
 * Студийный стенд: холодный ключ + тёплая заливка сбоку, синяя контровая,
 * пол-сетка для ощущения масшташа. Общий для режимов `scene=model`
 * (персонаж) и `scene=props` (транспорт, окружение).
 */
export function Studio({
  shadowRange = 3,
  shadowMap = 1536,
  floor = 6,
  gridCell = 0.25,
}: {
  /** половина стороны теневой камеры, м */
  shadowRange?: number
  shadowMap?: number
  /** сторона пола-сетки в метрах, 0 — без пола */
  floor?: number
  gridCell?: number
}) {
  return (
    <>
      <color attach="background" args={['#0b0e15']} />
      <ambientLight intensity={0.6} color="#7f9ad0" />
      <hemisphereLight args={['#a8c0ea', '#20222c', 0.9]} />
      <directionalLight
        castShadow
        position={[-3, 5, 4]}
        intensity={2.2}
        color="#e8eeff"
        shadow-mapSize={[shadowMap, shadowMap]}
        shadow-camera-near={0.5}
        shadow-camera-far={shadowRange * 6}
        shadow-camera-left={-shadowRange}
        shadow-camera-right={shadowRange}
        shadow-camera-top={shadowRange}
        shadow-camera-bottom={-shadowRange}
        shadow-bias={-0.0004}
        shadow-normalBias={0.02}
      />
      {/* ключ сбоку, чтобы читался объём */}
      <directionalLight position={[4, 2.5, -3]} intensity={0.9} color="#ffb877" />
      <directionalLight position={[0, 1.2, -5]} intensity={0.7} color="#5ad6ff" />

      {floor > 0 && (
        <>
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, 0, 0]}>
            <circleGeometry args={[floor / 2, 64]} />
            <meshStandardMaterial color="#14161d" roughness={0.85} metalness={0.05} />
          </mesh>
          <Grid
            args={[floor, floor]}
            cellSize={gridCell}
            cellColor="#2a3040"
            sectionSize={gridCell * 4}
            sectionColor="#3d4759"
            fadeDistance={floor * 1.2}
            position={[0, 0.002, 0]}
          />
        </>
      )}
    </>
  )
}
