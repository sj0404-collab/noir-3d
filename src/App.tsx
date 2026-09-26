import { Canvas } from '@react-three/fiber'
import { NoToneMapping } from 'three'
import { Suspense } from 'react'
import { Scene } from './scene/Scene'
import { Post } from './scene/Post'

const q = new URLSearchParams(location.search)
const num = (k: string, d: number) => {
  const v = parseFloat(q.get(k) ?? '')
  return Number.isFinite(v) ? v : d
}

export default function App() {
  // В headless-прогоне dpr>1 даёт слишком тяжёлый кадр для CPU-рендерера,
  // поэтому dpr задаётся параметром (?dpr=), по умолчанию 1.
  const dpr = num('dpr', 1)
  const loop = (q.get('loop') ?? 'always') as 'always' | 'demand' | 'never'

  return (
    <Canvas
      dpr={dpr}
      shadows="soft"
      frameloop={loop}
      gl={{
        antialias: false,
        powerPreference: 'high-performance',
        toneMapping: NoToneMapping,
      }}
      camera={{ position: [3.2, 1.7, 4.2], fov: 42, near: 0.1, far: 300 }}
    >
      <Suspense fallback={null}>
        <Scene />
        {!q.has('nopost') && <Post />}
      </Suspense>
    </Canvas>
  )
}
