import { Environment, Lightformer } from '@react-three/drei'
import { Grid, OrbitControls, Stage } from '@react-three/drei'
import { useSearchParams } from '../useSearchParams'
import { NoirStreet } from './NoirStreet'
import { CameraRig } from './CameraRig'
import { ProceduralEnv } from './ProceduralEnv'
import { RenderProbe } from './RenderProbe'
import { Detective } from './Detective'
import { Props } from './Props'
import { Studio } from './Studio'
import { Turntable } from './Turntable'

const q = new URLSearchParams(location.search)
const MODE = q.get('scene') ?? 'street'
const time = parseFloat(q.get('t') ?? '0')

export function Scene() {
  const model = MODE === 'model' || q.has('model')
  const props = MODE === 'props' || q.has('props')

  if (props) {
    return (
      <>
        <Props
          name={q.get('prop') ?? 'car'}
          clip={q.get('clip') ?? undefined}
          time={time}
          probe={q.has('probe')}
        />
        <Turntable />
        <EnvFallback />
      </>
    )
  }

  if (model) {
    return (
      <>
        <Studio />
        <Detective
          clip={q.get('clip') ?? 'Idle'}
          time={time}
          rotationY={parseFloat(q.get('ry') ?? '0')}
          scale={parseFloat(q.get('scale') ?? '1')}
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
          time={time}
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
  void Grid
  void OrbitControls
  void Stage
  void useSearchParams
  return null
}
