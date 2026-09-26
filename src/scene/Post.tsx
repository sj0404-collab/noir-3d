import {
  Bloom,
  ChromaticAberration,
  EffectComposer,
  Noise,
  SMAA,
  ToneMapping,
  Vignette,
} from '@react-three/postprocessing'
import { BlendFunction, ToneMappingMode } from 'postprocessing'
import { Vector2 } from 'three'

export function Post() {
  return (
    <EffectComposer multisampling={4} enableNormalPass>
      <Bloom
        intensity={0.85}
        luminanceThreshold={0.62}
        luminanceSmoothing={0.28}
        mipmapBlur
        radius={0.72}
      />
      <ChromaticAberration
        blendFunction={BlendFunction.NORMAL}
        offset={new Vector2(0.0006, 0.0009)}
        radialModulation
        modulationOffset={0.28}
      />
      <Noise premultiply blendFunction={BlendFunction.SOFT_LIGHT} opacity={0.32} />
      <Vignette eskil={false} offset={0.22} darkness={0.82} />
      <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
      <SMAA />
    </EffectComposer>
  )
}
