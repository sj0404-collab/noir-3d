import { useFrame } from '@react-three/fiber'
import { useMemo } from 'react'
import * as THREE from 'three'

const COUNT = 1500
const BOXY = 14
const AREA = { x: 22, z: 34 }
const FALL = 17
const WIND = 1.1

/** Дождь из точек вокруг игрока: обновляется на CPU, лишних лайтов нет.
 *  Точки растянуты по высоте — при быстром падении выглядят каплями-штрихами. */
export function Rain() {
  const geom = useMemo(() => {
    const pos = new Float32Array(COUNT * 3)
    const alpha = new Float32Array(COUNT)
    let seed = 17
    const rnd = () => {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff
      return seed / 0x7fffffff
    }
    for (let i = 0; i < COUNT; i++) {
      pos[i * 3] = (rnd() * 2 - 1) * AREA.x
      pos[i * 3 + 1] = rnd() * BOXY
      pos[i * 3 + 2] = (rnd() * 2 - 1) * AREA.z
      alpha[i] = 0.35 + rnd() * 0.4
    }
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    g.setAttribute('aAlpha', new THREE.BufferAttribute(alpha, 1))
    g.computeBoundingSphere()
    return g
  }, [])

  useFrame((_, dt) => {
    const step = Math.min(dt, 0.05)
    const attr = geom.getAttribute('position')
    const arr = attr.array as Float32Array
    const fall = FALL * step
    const wind = WIND * step
    for (let i = 0; i < COUNT; i++) {
      let y = arr[i * 3 + 1] - fall
      if (y < 0) y += BOXY
      arr[i * 3] -= wind
      if (arr[i * 3] < -AREA.x) arr[i * 3] += AREA.x * 2
      arr[i * 3 + 1] = y
    }
    attr.needsUpdate = true
    geom.computeBoundingSphere()
  })

  return (
    <points geometry={geom} frustumCulled={false}>
      <shaderMaterial
        depthWrite={false}
        transparent={true}
        blending={THREE.AdditiveBlending}
        vertexShader={`
          attribute float aAlpha;
          varying float vA;
          void main() {
            vA = aAlpha;
            vec4 mv = modelViewMatrix * vec4(position, 1.0);
            gl_PointSize = 220.0 / -mv.z;
            gl_Position = projectionMatrix * mv;
          }
        `}
        fragmentShader={`
          varying float vA;
          void main() {
            vec2 p = gl_PointCoord - vec2(0.5);
            float d = smoothstep(0.5, 0.16, length(p));
            gl_FragColor = vec4(vec3(0.62, 0.71, 0.85), d * vA);
          }
        `}
      />
    </points>
  )
}