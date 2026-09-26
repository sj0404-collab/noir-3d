import { Environment, Lightformer } from '@react-three/drei'
import { Grid, OrbitControls, Stage } from '@react-three/drei'
import { useSearchParams } from '../useSearchParams'
import { NoirStreet } from './NoirStreet'
import { CameraRig } from './CameraRig'
import { ProceduralEnv } from './ProceduralEnv'
import { RenderProbe } from './RenderProbe'
import { Detective } from './Detective'
import { Turntable } from './Turntable'

const q = new URLSearchParams(location.search)
const MODE = q.get('scene') ?? 'street'

export function Scene() {
  const model = MODE === 'model' || q.has('model')

  if (model) {
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
          shadow-mapSize={[1536, 1536]}
          shadow-camera-near={0.5}
          shadow-camera-far={20}
          shadow-camera-left={-3}
          shadow-camera-right={3}
          shadow-camera-top={3}
          shadow-camera-bottom={-3}
          shadow-bias={-0.0004}
          shadow-normalBias={0.02}
        />
        {/* ключ сбоку, чтобы читался объём */}
        <directionalLight position={[4, 2.5, -3]} intensity={0.9} color="#ffb877" />
        <directionalLight position={[0, 1.2, -5]} intensity={0.7} color="#5ad6ff" />

        <group position={[0, 0, 0]}>
          <Detective
            clip={q.get('clip') ?? 'Idle'}
            time={parseFloat(q.get('t') ?? '0')}
            rotationY={parseFloat(q.get('ry') ?? '0')}
            scale={parseFloat(q.get('scale') ?? '1')}
          />
        </group>

        {/* пол сеткой для ощущения масштаба */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, 0, 0]}>
          <circleGeometry args={[3, 64]} />
          <meshStandardMaterial color="#14161d" roughness={0.85} metalness={0.05} />
        </mesh>
        <Grid
          args={[6, 6]}
          cellSize={0.25}
          cellColor="#2a3040"
          sectionSize={1}
          sectionColor="#3d4759"
          fadeDistance={7}
          position={[0, 0.002, 0]}
        />

        <Turntable />
        <CameraRig />
        <ProceduralEnv intensity={1.0} />
        <RenderProbe probe={q.has('probe')} />
      </>
    )
  }

  return (
    <>
      {/* ночная палитра Ноктиса: холодный лунный ключ + тёплые уличные фонари */}
      <color attach="background" args={['#0a0f1c']} />
      <fogExp2 attach="fog" args={['#131a2b', 0.0115]} />

      <ambientLight intensity={0.5} color="#6d8cc4" />
      <hemisphereLight args={['#8fb0e8', '#1a1c24', 0.55]} />
      <directionalLight
        castShadow
        position={[-14, 22, -10]}
        intensity={1.5}
        color="#b6cbf2"
        shadow-mapSize={[1536, 1536]}
        shadow-camera-near={1}
        shadow-camera-far={90}
        shadow-camera-left={-32}
        shadow-camera-right={32}
        shadow-camera-top={32}
        shadow-camera-bottom={-32}
        shadow-bias={-0.0006}
        shadow-normalBias={0.03}
      />

      <NoirStreet />
      {q.has('herob') && (
        <Detective
          clip={q.get('clip') ?? 'Idle'}
          time={parseFloat(q.get('t') ?? '0')}
          position={[1.2, 0.18, 2]}
          rotationY={parseFloat(q.get('ry') ?? '0')}
        />
      )}
      <CameraRig />
      <ProceduralEnv intensity={1.1} />
      <RenderProbe probe={q.has('probe')} />
      <EnvFallback />
    </>
  )
}

function EnvFallback() {
  void Environment
  void Lightformer
  void OrbitControls
  void Stage
  void useSearchParams
  return null
}
