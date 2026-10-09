import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { CLUES, EXIT_POS, INTERACT_RADIUS, getState, setNearClue, tick, winGame } from './state'
import { playerState } from './playerState'

const cluePos = CLUES.map((c) => ({ id: c.id, v: new THREE.Vector3(c.pos[0], 0, c.pos[2]) }))
const exit = new THREE.Vector3(EXIT_POS[0], 0, EXIT_POS[2])
const tmp = new THREE.Vector3()

/**
 * Игровая логика без визуала: таймер, ближайшая улика, финал у машины.
 * Всё в useFrame, React трогаем только когда значение реально меняется.
 */
export function GameLogic() {
  useFrame((_, dt) => {
    tick(Math.min(dt, 0.05))
    const s = getState()
    if (s.phase !== 'playing') return

    let near: string | null = null
    let best = INTERACT_RADIUS
    for (const c of cluePos) {
      if (s.found[c.id]) continue
      tmp.set(playerState.pos.x - c.v.x, 0, playerState.pos.z - c.v.z)
      const d = tmp.length()
      if (d < best) {
        best = d
        near = c.id
      }
    }
    setNearClue(near)

    if (s.canReturn) {
      tmp.set(playerState.pos.x - exit.x, 0, playerState.pos.z - exit.z)
      if (tmp.length() < 3.2) winGame()
    }
  })
  return null
}
