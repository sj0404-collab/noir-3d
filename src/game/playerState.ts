import * as THREE from 'three'

/** Живое состояние игрока — читается камерой и логикой каждый кадр. */
export const playerState = {
  pos: new THREE.Vector3(0, 0.02, 6),
  yaw: Math.PI,
  speed: 0,
  running: false,
}

/** Границы переулка (проезжая часть между бордюрами). */
export const BOUNDS = { minX: -5.8, maxX: 5.8, minZ: -19.5, maxZ: 19.5 }

export const WALK_SPEED = 1.9
export const RUN_SPEED = 4.4

export function resetPlayer() {
  playerState.pos.set(0, 0.02, 6)
  playerState.yaw = Math.PI
  playerState.speed = 0
  playerState.running = false

  // отладочный спавн для скриншотов/тестов: ?px=&pz=
  const q = new URLSearchParams(location.search)
  const px = parseFloat(q.get('px') ?? '')
  const pz = parseFloat(q.get('pz') ?? '')
  if (Number.isFinite(px)) playerState.pos.x = px
  if (Number.isFinite(pz)) playerState.pos.z = pz
}
