import { useGLTF } from '@react-three/drei'
import { useMemo } from 'react'
import * as THREE from 'three'
import { GltfModel } from './GltfModel'
import { Studio } from './Studio'
import { CameraRig } from './CameraRig'
import { ProceduralEnv } from './ProceduralEnv'
import { RenderProbe } from './RenderProbe'

/**
 * Стенд для моделей из tools/: транспорт и набор уличного реквизита.
 *
 *   ?scene=props&prop=car|tram|kit&clip=Drive&t=0.4
 *
 * Камера кадрирует модель автоматически по bounding box (в стенде масштаб
 * разный: седан 4.5 м, трамвай 14 м, кит — россыпь на 30 м), но любой
 * параметр камеры из URL всё равно главнее: ?dist=6&ty=1.0.
 */
const PROPS = {
  car: { src: '/models/car.glb', clips: ['Drive', 'Idle', 'Siren'], floor: 24, cell: 1 },
  tram: { src: '/models/tram.glb', clips: ['Run'], floor: 32, cell: 2 },
  kit: { src: '/models/street_kit.glb', clips: ['Wind'], floor: 48, cell: 2 },
} satisfies Record<string, { src: string; clips: string[]; floor: number; cell: number }>

export type PropName = keyof typeof PROPS

export function Props({
  name,
  clip,
  time = 0,
  probe = false,
}: {
  name: string
  clip?: string
  time?: number
  probe?: boolean
}) {
  const prop = PROPS[name as PropName] ?? PROPS.car
  const active = clip && prop.clips.includes(clip) ? clip : prop.clips[0]
  return (
    <>
      <Studio shadowRange={14} shadowMap={2048} floor={prop.floor} gridCell={prop.cell} />
      <Framed src={prop.src} clip={active} time={time} />
      <ProceduralEnv intensity={1.0} />
      <RenderProbe probe={probe} />
    </>
  )
}

function Framed({ src, clip, time }: { src: string; clip: string; time: number }) {
  // useGLTF кэширует загрузку, поэтому bbox берётся из того же объекта,
  // который потом клонирует GltfModel, — без второй загрузки.
  const { scene } = useGLTF(src)
  const frame = useMemo(() => {
    const box = new THREE.Box3().setFromObject(scene)
    const c = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())
    return { target: [c.x, c.y, c.z] as [number, number, number], radius: size.length() / 2 }
  }, [scene])

  return (
    <>
      <GltfModel src={src} clip={clip} time={time} />
      <CameraRig frame={frame} />
    </>
  )
}

for (const p of Object.values(PROPS)) useGLTF.preload(p.src)
