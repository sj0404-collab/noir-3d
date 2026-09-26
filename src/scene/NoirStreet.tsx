import { useMemo } from 'react'
import * as THREE from 'three'

const ASPHALT = '#101319'
const KERB = '#22242b'
const WET = '#0e1016'

/** Процедурные PBR-текстуры: асфальт, тротуар, кирпич — без внешних ассетов. */
function useNoiseTexture(size = 512, octaves = 5) {
  return useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = size
    const ctx = canvas.getContext('2d')!
    const img = ctx.createImageData(size, size)

    // value noise со сглаживанием
    const perm = new Uint8Array(512)
    for (let i = 0; i < 256; i++) perm[i] = i
    for (let i = 255; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[perm[i], perm[j]] = [perm[j], perm[i]]
    }
    for (let i = 0; i < 256; i++) perm[i + 256] = perm[i]

    const fade = (t: number) => t * t * t * (t * (t * 6 - 15) + 10)
    const lerp = (a: number, b: number, t: number) => a + (b - a) * t
    const grad = (h: number, x: number, y: number) => {
      const u = h & 1 ? x : y
      const v = h & 2 ? x : y
      return (h & 4 ? -u : u) + (h & 8 ? -v : v)
    }
    const noise2 = (x: number, y: number) => {
      const X = Math.floor(x) & 255
      const Y = Math.floor(y) & 255
      x -= Math.floor(x)
      y -= Math.floor(y)
      const u = fade(x)
      const v = fade(y)
      const A = perm[X] + Y
      const B = perm[X + 1] + Y
      return lerp(
        lerp(grad(perm[A], x, y), grad(perm[B], x - 1, y), u),
        lerp(grad(perm[A + 1], x, y - 1), grad(perm[B + 1], x - 1, y - 1), u),
        v,
      )
    }

    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        let amp = 1
        let freq = 4 / size
        let sum = 0
        for (let o = 0; o < octaves; o++) {
          sum += noise2(x * freq, y * freq) * amp
          amp *= 0.5
          freq *= 2
        }
        const n = (sum * 0.5 + 0.5) * 255
        const i = (y * size + x) * 4
        img.data[i] = img.data[i + 1] = img.data[i + 2] = n
        img.data[i + 3] = 255
      }
    }
    ctx.putImageData(img, 0, 0)

    const tex = new THREE.CanvasTexture(canvas)
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping
    tex.colorSpace = THREE.NoColorSpace
    tex.anisotropy = 8
    return tex
  }, [size, octaves])
}

function useRoughnessFromNoise(noiseTex: THREE.Texture, contrast = 0.55, bias = 0.25) {
  return useMemo(() => {
    const src = noiseTex.image as HTMLCanvasElement
    const size = src.width
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = size
    const ctx = canvas.getContext('2d')!
    ctx.drawImage(src, 0, 0)
    const img = ctx.getImageData(0, 0, size, size)
    for (let i = 0; i < img.data.length; i += 4) {
      const n = img.data[i] / 255
      const r = THREE.MathUtils.clamp(bias + (n - 0.5) * contrast + 0.35, 0, 1)
      const v = r * 255
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v
    }
    ctx.putImageData(img, 0, 0)
    const tex = new THREE.CanvasTexture(canvas)
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping
    return tex
  }, [noiseTex, contrast, bias])
}

/** Нормали из карты высот —Sobel, чтобы свет читался рельефом. */
function useNormalMapFromNoise(noiseTex: THREE.Texture, strength = 1.6) {
  return useMemo(() => {
    const src = noiseTex.image as HTMLCanvasElement
    const size = src.width
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = size
    const ctx = canvas.getContext('2d')!
    ctx.drawImage(src, 0, 0)
    const img = ctx.getImageData(0, 0, size, size)
    const h = new Float32Array(size * size)
    for (let i = 0, p = 0; i < img.data.length; i += 4, p++) {
      h[p] = img.data[i] / 255
    }
    const at = (x: number, y: number) => h[((y + size) % size) * size + ((x + size) % size)]
    const out = ctx.createImageData(size, size)
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const dx =
          at(x - 1, y - 1) + 2 * at(x - 1, y) + at(x - 1, y + 1) -
          (at(x + 1, y - 1) + 2 * at(x + 1, y) + at(x + 1, y + 1))
        const dy =
          at(x - 1, y - 1) + 2 * at(x, y - 1) + at(x + 1, y - 1) -
          (at(x - 1, y + 1) + 2 * at(x, y + 1) + at(x + 1, y + 1))
        let nx = dx * strength
        let ny = dy * strength
        const nz = 1
        const len = Math.hypot(nx, ny, nz)
        nx /= len
        ny /= len
        const i = (y * size + x) * 4
        out.data[i] = (nx * 0.5 + 0.5) * 255
        out.data[i + 1] = (ny * 0.5 + 0.5) * 255
        out.data[i + 2] = (nz / len) * 0.5 * 255 + 127.5
        out.data[i + 3] = 255
      }
    }
    ctx.putImageData(out, 0, 0)
    const tex = new THREE.CanvasTexture(canvas)
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping
    return tex
  }, [noiseTex, strength])
}

function Lantern({
  position,
  rotation = 0,
  shadow = false,
}: {
  position: [number, number, number]
  rotation?: number
  shadow?: boolean
}) {
  return (
    <group position={position} rotation={[0, rotation, 0]}>
      {/* столб */}
      <mesh castShadow position={[0, 2.2, 0]}>
        <cylinderGeometry args={[0.06, 0.09, 4.4, 12]} />
        <meshStandardMaterial color="#171a20" roughness={0.62} metalness={0.75} />
      </mesh>
      {/* основание */}
      <mesh castShadow position={[0, 0.14, 0]}>
        <cylinderGeometry args={[0.19, 0.24, 0.28, 14]} />
        <meshStandardMaterial color="#121419" roughness={0.7} metalness={0.6} />
      </mesh>
      {/* кронштейн */}
      <mesh castShadow position={[0.42, 4.32, 0]} rotation={[0, 0, -0.5]}>
        <boxGeometry args={[0.95, 0.06, 0.06]} />
        <meshStandardMaterial color="#171a20" roughness={0.6} metalness={0.75} />
      </mesh>
      {/* плафон */}
      <mesh position={[0.85, 4.12, 0]}>
        <sphereGeometry args={[0.17, 16, 12]} />
        <meshStandardMaterial
          color="#3a2c14"
          emissive="#ffb35c"
          emissiveIntensity={1.5}
          roughness={0.35}
          toneMapped={false}
        />
      </mesh>
      {/* абажур */}
      <mesh castShadow position={[0.85, 4.32, 0]}>
        <coneGeometry args={[0.28, 0.24, 14]} />
        <meshStandardMaterial color="#1b1e24" roughness={0.55} metalness={0.7} />
      </mesh>
      {/* тёплый свет */}
      <pointLight
        position={[0.85, 4.05, 0]}
        intensity={2.4}
        distance={10}
        decay={2}
        color="#ffb96b"
        castShadow={shadow}
        shadow-mapSize={[512, 512]}
        shadow-bias={-0.004}
      />
    </group>
  )
}

function Facade({
  position,
  rotation,
  width = 14,
  height = 16,
  depth = 6,
  seed = 0,
}: {
  position: [number, number, number]
  rotation: number
  width?: number
  height?: number
  depth?: number
  seed?: number
}) {
  const windows = useMemo(() => {
    const cols = Math.floor(width / 2.4)
    const rows = Math.floor((height - 4) / 2.6)
    const out: { x: number; y: number; lit: number; warm: number }[] = []
    let s = seed * 9301 + 49297
    const rnd = () => {
      s = (s * 9301 + 49297) % 233280
      return s / 233280
    }
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        out.push({
          x: -width / 2 + 1.2 + c * 2.4,
          y: 4.4 + r * 2.6,
          lit: rnd(),
          warm: rnd(),
        })
      }
    }
    return out
  }, [width, height, seed])

  const brick = useNoiseTexture(256, 4)
  const brickN = useNormalMapFromNoise(brick, 1.1)
  useMemo(() => {
    brick.repeat.set(6, 8)
    brickN.repeat.set(6, 8)
  }, [brick, brickN])

  return (
    <group position={position} rotation={[0, rotation, 0]}>
      {/* корпус */}
      <mesh castShadow receiveShadow position={[0, height / 2, -depth / 2]}>
        <boxGeometry args={[width, height, depth]} />
        <meshStandardMaterial
          color="#241f2a"
          roughness={0.86}
          metalness={0.04}
          normalMap={brickN}
          normalScale={new THREE.Vector2(0.7, 0.7)}
        />
      </mesh>
      {/* цоколь */}
      <mesh castShadow receiveShadow position={[0, 1.5, 0.06]}>
        <boxGeometry args={[width + 0.3, 3, 0.2]} />
        <meshStandardMaterial color="#1b1a20" roughness={0.88} metalness={0.05} />
      </mesh>
      {/* карниз */}
      <mesh castShadow position={[0, height - 0.35, 0.1]}>
        <boxGeometry args={[width + 0.5, 0.5, 0.42]} />
        <meshStandardMaterial color="#221f2a" roughness={0.72} metalness={0.12} />
      </mesh>
      {/* окна */}
      {windows.map((w, i) => {
        const lit = w.lit > 0.5
        return (
          <group key={i} position={[w.x, w.y, 0.03]}>
            {/* рама */}
            <mesh position={[0, 0, 0.02]}>
              <boxGeometry args={[1.32, 1.86, 0.16]} />
              <meshStandardMaterial color="#0d0e12" roughness={0.6} metalness={0.3} />
            </mesh>
            {/* стекло */}
            <mesh position={[0, 0, 0.16]}>
              <planeGeometry args={[1.12, 1.66]} />
              <meshStandardMaterial
                color={lit ? '#6b5228' : '#111726'}
                emissive={lit ? '#ffb968' : '#0b1220'}
                emissiveIntensity={lit ? 1.15 + w.warm * 0.85 : 0.35}
                roughness={0.16}
                metalness={0.08}
                envMapIntensity={0.9}
              />
            </mesh>
            {/* подоконник */}
            <mesh castShadow position={[0, -1.02, 0.14]}>
              <boxGeometry args={[1.5, 0.1, 0.26]} />
              <meshStandardMaterial color="#1a1a20" roughness={0.8} />
            </mesh>
          </group>
        )
      })}
    </group>
  )
}

export function NoirStreet() {
  const noise = useNoiseTexture(512, 5)
  const rough = useRoughnessFromNoise(noise, 0.32, 0.42)
  const normal = useNormalMapFromNoise(noise, 1.3)
  const wet = useNoiseTexture(256, 4)
  const wetRough = useRoughnessFromNoise(wet, 0.35, 0.02)

  useMemo(() => {
    noise.repeat.set(16, 16)
    rough.repeat.set(16, 16)
    normal.repeat.set(16, 16)
    wet.repeat.set(4, 4)
    wetRough.repeat.set(4, 4)
  }, [noise, rough, normal, wet, wetRough])

  return (
    <group>
      {/* асфальт */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[90, 90]} />
        {new URLSearchParams(location.search).has('flatroad') ? (
          <meshStandardMaterial color="#101010" roughness={1} metalness={0} envMapIntensity={0} />
        ) : (
          <meshStandardMaterial
            color={ASPHALT}
            roughness={0.99}
            metalness={0.0}
            normalMap={normal}
            normalScale={new THREE.Vector2(0.08, 0.08)}
            envMapIntensity={0.15}
          />
        )}
      </mesh>

      {/* мокрые лужи — зеркалят фонари, это даёт «нуар» */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[2.4, 0.012, 1.2]}>
        <circleGeometry args={[2.6, 32]} />
        <meshStandardMaterial
          color={WET}
          roughnessMap={wetRough}
          roughness={0.09}
          metalness={0.2}
          envMapIntensity={0.8}
        />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-3.6, 0.011, -2.2]}>
        <circleGeometry args={[1.7, 24]} />
        <meshStandardMaterial color={WET} roughness={0.1} metalness={0.22} envMapIntensity={0.9} />
      </mesh>

      {/* тротуары */}
      {[-1, 1].map((s) => (
        <mesh key={s} position={[s * 9, 0.09, 0]} receiveShadow>
          <boxGeometry args={[5, 0.18, 46]} />
          <meshStandardMaterial
            color={KERB}
            roughness={0.9}
            normalMap={normal}
            normalScale={new THREE.Vector2(0.18, 0.18)}
          />
        </mesh>
      ))}
      {/* бордюр */}
      {[-1, 1].map((s) => (
        <mesh key={`c${s}`} position={[s * 6.5, 0.13, 0]} castShadow receiveShadow>
          <boxGeometry args={[0.42, 0.26, 46]} />
          <meshStandardMaterial color="#2a2d35" roughness={0.72} />
        </mesh>
      ))}

      {/* фасады по обе стороны улицы */}
      <Facade position={[-13.5, 0, 0]} rotation={Math.PI / 2} seed={3} width={18} height={17} />
      <Facade position={[-13.5, 0, 22]} rotation={Math.PI / 2} seed={7} width={16} height={14} depth={5} />
      <Facade position={[-13.5, 0, -22]} rotation={Math.PI / 2} seed={11} width={16} height={19} depth={5} />
      <Facade position={[13.5, 0, 0]} rotation={-Math.PI / 2} seed={5} width={18} height={15} />
      <Facade position={[13.5, 0, 22]} rotation={-Math.PI / 2} seed={13} width={16} height={18} depth={5} />
      <Facade position={[13.5, 0, -22]} rotation={-Math.PI / 2} seed={17} width={16} height={13} depth={5} />

      {/* фонари вдоль улицы */}
      <Lantern position={[-5.6, 0.18, 6]} shadow />
      <Lantern position={[5.6, 0.18, -6]} />
      <Lantern position={[-5.6, 0.18, -14]} />
      <Lantern position={[5.6, 0.18, 14]} />

      {/* неоновая вывеска «Ноктис» — холодный акцент */}
      <group position={[-6.42, 5.4, 3.4]} rotation={[0, Math.PI / 2, 0]}>
        <mesh>
          <planeGeometry args={[3.2, 0.9]} />
          <meshStandardMaterial color="#04121a" roughness={0.4} metalness={0.4} />
        </mesh>
        <mesh position={[0, 0, 0.03]}>
          <planeGeometry args={[2.9, 0.66]} />
          <meshStandardMaterial
            color="#0b2b3a"
            emissive="#37e0ff"
            emissiveIntensity={2.1}
          />
        </mesh>
        <pointLight position={[0, 0, 1.2]} intensity={2.6} distance={9} decay={2} color="#5ad6ff" />
      </group>

      {/* фонарный столб вдали — глубина кадра */}
      <group position={[0, 0, 34]}>
        <mesh castShadow position={[0, 5, 0]}>
          <cylinderGeometry args={[0.14, 0.2, 10, 12]} />
          <meshStandardMaterial color="#14161b" roughness={0.7} metalness={0.5} />
        </mesh>
        <mesh position={[0, 10.1, 0]}>
          <boxGeometry args={[1.1, 0.18, 0.5]} />
          <meshStandardMaterial
            color="#2a2413"
            emissive="#ffc07a"
            emissiveIntensity={1.8}
          />
        </mesh>
        <pointLight position={[0, 9.8, 0]} intensity={4.5} distance={24} decay={2} color="#ffc487" />
      </group>
    </group>
  )
}
