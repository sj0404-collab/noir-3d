import { useSyncExternalStore } from 'react'

export type Phase = 'title' | 'playing' | 'paused' | 'won' | 'lost'

export type ClueDef = {
  id: string
  label: string
  detail: string
  /** позиция улики на улице */
  pos: [number, number, number]
}

/** Время дела в секундах: не успел — Ноктис тебя не простит. */
export const TOTAL_TIME = 240

/** Улики «Дела о синем мотыльке». Разбросаны по переулку. */
export const CLUES: ClueDef[] = [
  {
    id: 'body',
    label: 'Тело у стены',
    detail: 'Владелец клуба «Синий мотылёк». Удар в затылок, крови почти нет — убивал профессионал.',
    pos: [-3.2, 0.02, -6.5],
  },
  {
    id: 'revolver',
    label: 'Револьвер',
    detail: 'Оружие брошено у бордюра. Барабан на пять, стрелян один патрон. Ствол ещё тёплый.',
    pos: [4.7, 0.02, 1.5],
  },
  {
    id: 'letter',
    label: 'Письмо',
    detail: 'Мокрая записка: «в полночь у трамвая». Почерк ровный, женский. Чернила свежие.',
    pos: [-5.2, 0.02, 8.5],
  },
  {
    id: 'cigarette',
    label: 'Окурок',
    detail: 'Дорогие сигареты, пепел ещё тёплый. Здесь кто-то долго ждал и не нервничал.',
    pos: [5.2, 0.02, -12],
  },
  {
    id: 'badge',
    label: 'Значок',
    detail: 'Полицейский значок 17-го участка. Это не жертва. Это кто-то свой.',
    pos: [1.8, 0.02, 15],
  },
]

/** Куда вернуться после сбора улик. */
export const EXIT_POS: [number, number, number] = [3.6, 0.02, 18]

/** Радиус, с которого улику видно и можно осмотреть. */
export const INTERACT_RADIUS = 2.6

export type Speaker = { name: string; line: string }

export type GameState = {
  phase: Phase
  found: Record<string, boolean>
  foundCount: number
  objective: string
  speaker: Speaker | null
  timeLeft: number
  elapsed: number
  /** ближайшая неподобранная улика в радиусе осмотра */
  nearClue: string | null
  /** все улики собраны — пора к машине */
  canReturn: boolean
}

function initial(): GameState {
  return {
    phase: 'title',
    found: {},
    foundCount: 0,
    objective: 'Осмотри место преступления — найди 5 улик.',
    speaker: {
      name: 'Инспектор Харт',
      line: 'Ноктис, 23:40. Дождь смыл всё, кроме правды. Осмотрись и не тяни — до полуночи я должен знать имя.',
    },
    timeLeft: TOTAL_TIME,
    elapsed: 0,
    nearClue: null,
    canReturn: false,
  }
}

let state: GameState = initial()
const listeners = new Set<() => void>()
let lastSecond = TOTAL_TIME

function emit() {
  for (const l of listeners) l()
}

function set(patch: Partial<GameState>) {
  state = { ...state, ...patch }
  emit()
}

export function subscribe(fn: () => void) {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

export function getState() {
  return state
}

export function useGame() {
  return useSyncExternalStore(subscribe, getState)
}

export function startGame() {
  state = initial()
  state.phase = 'playing'
  lastSecond = TOTAL_TIME
  emit()
}

export function pauseGame() {
  if (state.phase === 'playing') set({ phase: 'paused' })
}

export function resumeGame() {
  if (state.phase === 'paused') set({ phase: 'playing' })
}

export function collectClue(id: string) {
  if (state.phase !== 'playing' || state.found[id]) return
  const clue = CLUES.find((c) => c.id === id)
  if (!clue) return
  const found = { ...state.found, [id]: true }
  const foundCount = Object.keys(found).length
  const all = foundCount >= CLUES.length
  set({
    found,
    foundCount,
    nearClue: null,
    canReturn: all,
    objective: all
      ? 'Все улики собраны. Вернись к полицейской машине и закрой дело.'
      : `Осмотри место преступления — найди улик: ${foundCount} из ${CLUES.length}.`,
    speaker: {
      name: 'Улика',
      line: `${clue.label}. ${clue.detail}`,
    },
  })
}

/** Обновляет ближайшую улику, не дёргая React на каждом кадре. */
export function setNearClue(id: string | null) {
  if (state.nearClue !== id) set({ nearClue: id })
}

/** Тикает таймер; React обновляется только раз в секунду. */
export function tick(dt: number) {
  if (state.phase !== 'playing') return
  const timeLeft = Math.max(0, state.timeLeft - dt)
  const elapsed = state.elapsed + dt
  if (timeLeft <= 0) {
    state = { ...state, timeLeft: 0, elapsed, phase: 'lost' }
    emit()
    return
  }
  const sec = Math.ceil(timeLeft)
  if (sec !== lastSecond) {
    lastSecond = sec
    set({ timeLeft, elapsed })
  } else {
    // без emit: ссылку не меняем, React не трогаем
    state.timeLeft = timeLeft
    state.elapsed = elapsed
  }
}

export function winGame() {
  if (state.phase === 'playing') set({ phase: 'won' })
}
