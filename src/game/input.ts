import * as THREE from 'three'

/**
 * Разделяемое состояние управления. Живёт вне React: джойстик и клавиатура
 * пишут сюда, игрок читает в useFrame — без ре-рендеров на каждый кадр.
 */
export const input = {
  /** стик: -1..1, x — вправо, y — вперёд */
  mx: 0,
  my: 0,
  /** куда смотрит камера по горизонтали (рад) */
  cameraYaw: Math.PI,
  /** тащим палец/мышь — вращаем камеру */
  looking: false,
}

export function setStick(x: number, y: number) {
  input.mx = x
  input.my = y
}

const keys = new Set<string>()
let keyboardActive = false

export function applyKeys() {
  let x = 0
  let y = 0
  if (keys.has('KeyW') || keys.has('ArrowUp')) y += 1
  if (keys.has('KeyS') || keys.has('ArrowDown')) y -= 1
  if (keys.has('KeyA') || keys.has('ArrowLeft')) x -= 1
  if (keys.has('KeyD') || keys.has('ArrowRight')) x += 1
  // клавиатура приоритетнее, если зажата; иначе стик остаётся как есть
  if (x !== 0 || y !== 0) {
    const len = Math.hypot(x, y)
    setStick(x / len, y / len)
  } else if (!keyboardActive) {
    setStick(0, 0)
  }
}

/** Привязка клавиатуры (десктоп). Возвращает cleanup. */
export function bindKeyboard() {
  const down = (e: KeyboardEvent) => {
    keyboardActive = true
    keys.add(e.code)
    applyKeys()
  }
  const up = (e: KeyboardEvent) => {
    keys.delete(e.code)
    applyKeys()
    keyboardActive = keys.size > 0
  }
  window.addEventListener('keydown', down)
  window.addEventListener('keyup', up)
  return () => {
    window.removeEventListener('keydown', down)
    window.removeEventListener('keyup', up)
  }
}

const UP = new THREE.Vector3(0, 1, 0)

/** Превращает стик в мировой вектор движения относительно камеры. */
export function stickToWorld(out: THREE.Vector3) {
  const yaw = input.cameraYaw
  const fx = Math.sin(yaw)
  const fz = Math.cos(yaw)
  // forward = (fx, 0, fz); right = forward × up = (-fz, 0, fx)
  out.set(fx * input.my - fz * input.mx, 0, fz * input.my + fx * input.mx)
  return out
}

export { UP }
