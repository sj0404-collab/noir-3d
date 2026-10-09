import { useEffect, useRef, type CSSProperties, type ReactNode } from 'react'
import { CLUES, collectClue, pauseGame, resumeGame, startGame, useGame } from '../game/state'
import { bindKeyboard, input } from '../game/input'
import { resetPlayer } from '../game/playerState'
import { Joystick } from './Joystick'

const FONT =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'

function fmt(t: number) {
  const m = Math.floor(t / 60)
  const s = Math.floor(t % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

/** HTML-слой поверх 3D: заголовок, HUD, стик, меню. */
export function GameUI() {
  const g = useGame()
  const root = useRef<HTMLDivElement>(null)

  useEffect(() => bindKeyboard(), [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code === 'Space' && g.phase === 'playing' && g.nearClue) {
        e.preventDefault()
        collectClue(g.nearClue)
      }
      if (e.code === 'Escape') {
        if (g.phase === 'playing') pauseGame()
        else if (g.phase === 'paused') resumeGame()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [g.phase, g.nearClue])

  const start = () => {
    resetPlayer()
    startGame()
  }

  return (
    <div
      ref={root}
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        fontFamily: FONT,
        color: '#e8eef8',
        userSelect: 'none',
        WebkitUserSelect: 'none',
        WebkitTapHighlightColor: 'transparent',
        boxSizing: 'border-box',
        padding:
          'env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)',
      }}
      onContextMenu={(e) => e.preventDefault()}
    >
      <LookLayer />

      {g.phase === 'playing' && (
        <>
          <TopBar timeLeft={g.timeLeft} found={g.foundCount} objective={g.objective} onPause={pauseGame} />
          {g.speaker && <Caption name={g.speaker.name} line={g.speaker.line} />}
          <div style={{ position: 'absolute', left: 22, bottom: 22 }}>
            <Joystick />
          </div>
          <ActionButton g={g} />
        </>
      )}

      {g.phase === 'title' && (
        <Menu
          title="НУАР-ДЕТ"
          accent="#5ad6ff"
          subtitle="Ноктис, 23:40 · Дело о синем мотыльке"
          body={
            <>
              <p style={pStyle}>
                Найди {CLUES.length} улик на ночной улице, пока не вышло время, и вернись
                к полицейской машине. Стик слева — идти, свайп по экрану — повернуть камеру,
                кнопка справа — осмотреть.
              </p>
              <div style={keysStyle}>WASD / стрелки · пробел · Esc</div>
            </>
          }
          action="Начать дело"
          onAction={start}
        />
      )}

      {g.phase === 'paused' && (
        <Menu
          title="ПАУЗА"
          accent="#f2b229"
          subtitle="Ноктис ждёт"
          action="Продолжить"
          onAction={resumeGame}
          secondary="Начать заново"
          onSecondary={start}
        />
      )}

      {g.phase === 'won' && (
        <Menu
          title="ДЕЛО ЗАКРЫТО"
          accent="#3ad0a0"
          subtitle={`Дело о синем мотыльке · ${fmt(g.elapsed)}`}
          body={
            <p style={pStyle}>
              Ты собрал все улики и вернулся к машине. Имя убийцы — в значке 17-го участка.
              Хорошая работа, детектив.
            </p>
          }
          action="Новое дело"
          onAction={start}
        />
      )}

      {g.phase === 'lost' && (
        <Menu
          title="ВРЕМЯ ВЫШЛО"
          accent="#ff5f6d"
          subtitle="Полночь. Убийца растворился в дожде"
          body={
            <p style={pStyle}>
              Ты нашёл {g.foundCount} из {CLUES.length} улик. Ноктис не прощает медлительных.
            </p>
          }
          action="Попробовать снова"
          onAction={start}
        />
      )}
    </div>
  )
}

function LookLayer() {
  const dragging = useRef<{ id: number; x: number } | null>(null)
  return (
    <div
      style={{ position: 'absolute', inset: 0, pointerEvents: 'auto', touchAction: 'none' }}
      onPointerDown={(e) => {
        e.currentTarget.setPointerCapture(e.pointerId)
        dragging.current = { id: e.pointerId, x: e.clientX }
        input.looking = true
      }}
      onPointerMove={(e) => {
        const d = dragging.current
        if (!d || d.id !== e.pointerId) return
        input.cameraYaw -= (e.clientX - d.x) * 0.006
        d.x = e.clientX
      }}
      onPointerUp={() => {
        dragging.current = null
        input.looking = false
      }}
      onPointerCancel={() => {
        dragging.current = null
        input.looking = false
      }}
    />
  )
}

function TopBar({
  timeLeft,
  found,
  objective,
  onPause,
}: {
  timeLeft: number
  found: number
  objective: string
  onPause: () => void
}) {
  const danger = timeLeft < 30
  return (
    <div style={{ position: 'absolute', top: 16, left: 16, right: 16, display: 'flex', gap: 12 }}>
      <div
        style={{
          flex: '0 1 420px',
          background: 'rgba(8,14,26,0.62)',
          border: '1px solid rgba(120,170,240,0.28)',
          borderRadius: 14,
          padding: '10px 14px',
          backdropFilter: 'blur(6px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <span style={{ fontSize: 12, letterSpacing: 2, color: '#7fa8dc' }}>ДЕЛО О СИНЕМ МОТЫЛЬКЕ</span>
          <span style={{ marginLeft: 'auto', fontWeight: 700, color: danger ? '#ff6b72' : '#ffd27a', fontSize: 18 }}>
            {fmt(timeLeft)}
          </span>
        </div>
        <div style={{ marginTop: 4, fontSize: 14, opacity: 0.92 }}>{objective}</div>
        <div style={{ marginTop: 6, fontSize: 12, color: '#9fb6d6' }}>
          Улики: <b style={{ color: '#ffd23a' }}>{found}</b> / {CLUES.length}
        </div>
      </div>
      <button onPointerDown={(e) => e.stopPropagation()} onClick={onPause} style={iconBtn}>
        II
      </button>
    </div>
  )
}

function Caption({ name, line }: { name: string; line: string }) {
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        bottom: 26,
        transform: 'translateX(-50%)',
        width: 'min(680px, 78vw)',
        background: 'rgba(6,10,20,0.72)',
        border: '1px solid rgba(120,170,240,0.25)',
        borderLeft: '3px solid #5ad6ff',
        borderRadius: 10,
        padding: '10px 14px',
        backdropFilter: 'blur(6px)',
        textAlign: 'left',
      }}
    >
      <div style={{ fontSize: 12, letterSpacing: 1, color: '#5ad6ff', marginBottom: 3 }}>{name}</div>
      <div style={{ fontSize: 15, lineHeight: 1.35 }}>{line}</div>
    </div>
  )
}

function ActionButton({ g }: { g: ReturnType<typeof useGame> }) {
  const near = g.nearClue ? CLUES.find((c) => c.id === g.nearClue) : null
  const show = !!near || g.canReturn
  return (
    <div
      style={{
        position: 'absolute',
        right: 26,
        bottom: 30,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 10,
      }}
    >
      {show && (
        <div
          style={{
            fontSize: 13,
            padding: '6px 12px',
            borderRadius: 20,
            background: 'rgba(8,14,26,0.7)',
            border: '1px solid rgba(120,170,240,0.3)',
          }}
        >
          {near ? near.label : 'Вернись к машине'}
        </div>
      )}
      {near && (
        <button
          onPointerDown={(e) => e.stopPropagation()}
          onClick={() => collectClue(near.id)}
          style={{
            pointerEvents: 'auto',
            width: 116,
            height: 116,
            borderRadius: '50%',
            border: '2px solid rgba(255,210,58,0.85)',
            background: 'radial-gradient(circle at 50% 40%, rgba(255,210,58,0.32), rgba(20,26,40,0.85))',
            color: '#ffe9a8',
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: 1,
            boxShadow: '0 0 30px rgba(255,190,40,0.35)',
            cursor: 'pointer',
          }}
        >
          ОСМОТРЕТЬ
        </button>
      )}
    </div>
  )
}

function Menu({
  title,
  subtitle,
  body,
  action,
  onAction,
  secondary,
  onSecondary,
  accent = '#5ad6ff',
}: {
  title: string
  subtitle?: string
  body?: ReactNode
  action: string
  onAction: () => void
  secondary?: string
  onSecondary?: () => void
  accent?: string
}) {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'auto',
        background: 'radial-gradient(ellipse at 50% 40%, rgba(10,16,30,0.62), rgba(3,5,10,0.9))',
      }}
    >
      <div style={{ width: 'min(560px, 88vw)', textAlign: 'center', padding: 24 }}>
        <div style={{ fontSize: 13, letterSpacing: 6, color: accent, marginBottom: 8 }}>
          НОКТИС · 3D
        </div>
        <h1 style={{ margin: 0, fontSize: 'clamp(30px, 7vw, 54px)', letterSpacing: 3, fontWeight: 800 }}>
          {title}
        </h1>
        {subtitle && <div style={{ marginTop: 8, color: '#9fb6d6', fontSize: 15 }}>{subtitle}</div>}
        {body && <div style={{ marginTop: 18 }}>{body}</div>}
        <button
          onPointerDown={(e) => e.stopPropagation()}
          onClick={onAction}
          style={{
            marginTop: 22,
            width: '100%',
            padding: '15px 24px',
            fontSize: 18,
            fontWeight: 700,
            letterSpacing: 1,
            color: '#04121c',
            background: `linear-gradient(180deg, #ffffff, ${accent})`,
            border: 'none',
            borderRadius: 12,
            cursor: 'pointer',
            boxShadow: `0 8px 30px ${accent}55`,
          }}
        >
          {action}
        </button>
        {secondary && (
          <button
            onPointerDown={(e) => e.stopPropagation()}
            onClick={onSecondary}
            style={{
              marginTop: 10,
              width: '100%',
              padding: '11px 24px',
              fontSize: 15,
              color: '#cfe0f4',
              background: 'rgba(120,170,240,0.12)',
              border: '1px solid rgba(120,170,240,0.35)',
              borderRadius: 12,
              cursor: 'pointer',
            }}
          >
            {secondary}
          </button>
        )}
      </div>
    </div>
  )
}

const pStyle: CSSProperties = {
  margin: '0 auto',
  maxWidth: 460,
  color: '#cddcf0',
  fontSize: 15,
  lineHeight: 1.5,
}

const keysStyle: CSSProperties = {
  marginTop: 14,
  fontSize: 12,
  color: '#7fa8dc',
  letterSpacing: 1,
}

const iconBtn: CSSProperties = {
  pointerEvents: 'auto',
  marginLeft: 'auto',
  width: 46,
  height: 46,
  borderRadius: 12,
  border: '1px solid rgba(120,170,240,0.35)',
  background: 'rgba(8,14,26,0.62)',
  color: '#cfe0f4',
  fontSize: 16,
  fontWeight: 700,
  cursor: 'pointer',
  backdropFilter: 'blur(6px)',
}
