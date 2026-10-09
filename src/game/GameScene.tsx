import { useEffect } from 'react'
import { NoirStreet } from '../scene/NoirStreet'
import { ProceduralEnv } from '../scene/ProceduralEnv'
import { Player } from './Player'
import { ClueMarks } from './ClueMarks'
import { GameLogic } from './GameLogic'
import { FollowCamera } from './FollowCamera'
import { ParkedCar } from './ParkedCar'
import { RenderProbe } from '../scene/RenderProbe'
import { startGame } from './state'
import { resetPlayer } from './playerState'

/** Для скриншотов и быстрого теста: ?autostart=1 сразу запускает дело. */
function AutoStart() {
  useEffect(() => {
    if (new URLSearchParams(location.search).has('autostart')) {
      resetPlayer()
      startGame()
    }
  }, [])
  return null
}

/** Игровая сцена: ночной переулок Ноктиса, детектив и дело о синем мотыльке. */
export function GameScene() {
  return (
    <>
      <color attach="background" args={['#0a0f1c']} />
      <fogExp2 attach="fog" args={['#101728', 0.014]} />

      <ambientLight intensity={0.55} color="#6d8cc4" />
      <hemisphereLight args={['#8fb0e8', '#1a1c24', 0.6]} />
      <directionalLight
        castShadow
        position={[-14, 22, -10]}
        intensity={1.5}
        color="#b6cbf2"
        shadow-mapSize={[1024, 1024]}
        shadow-camera-near={1}
        shadow-camera-far={80}
        shadow-camera-left={-26}
        shadow-camera-right={26}
        shadow-camera-top={26}
        shadow-camera-bottom={-26}
        shadow-bias={-0.0006}
        shadow-normalBias={0.03}
      />

      <NoirStreet />
      <Player />
      <ClueMarks />
      <ParkedCar />
      <GameLogic />
      <FollowCamera />
      <ProceduralEnv intensity={1.05} />
      <AutoStart />
      <RenderProbe />
    </>
  )
}
