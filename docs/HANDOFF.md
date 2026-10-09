# Нуар-Дет 3D — передача состояния

Репозиторий: `https://github.com/sj0404-collab/noir-3d` (ветка `master`).
Проект — детективная игра в ночном Ноктисе на React Three Fiber (React 19, TS,
Vite, three 0.186). Отдаётся как веб-игра и как Android-приложение через
Capacitor 6 (пакет `com.sj0404.noirdet`, «Нуар-Дет», landscape).

---

## 1. Что уже работает

| Часть | Состояние |
|---|---|
| Каркас Vite + React 19 + TS + R3F + drei + postprocessing | `npm run build` проходит, `npm run lint` без ошибок |
| **Игра** (`src/game/`, `src/ui/`) | тайтл → игра → победа/поражение, сбор 5 улик, таймер 4:00 |
| Управление | виртуальный стик, свайп-поворот камеры, кнопка «ОСМОТРЕТЬ», WASD/пробел/Esc |
| Камера от третьего лица (`FollowCamera`) | висит за спиной, поворачивается пальцем |
| Ночной нуар-участок (`src/scene/NoirStreet.tsx`) | PBR + мягкие тени + мокрый асфальт |
| IBL-окружение (`src/scene/ProceduralEnv.tsx`) | PMREM-бейк, сброс render target |
| Пост-обработка | `Post` (стенды) и облегчённый `GamePost` (игра) |
| Персонаж, транспорт, окружение (glTF из `tools/`) | 26 костей, 6 клипов; седан/трамвай; киты улицы |
| **Android (Capacitor)** | `android/` собран, APK собирается через `npm run apk` |
| Скриншоты (`npm run shots`) | 12 кадров (2 игровых + 10 стендов), 0 пустых |

## 2. Игровой слой (кратко)

- **Состояние** — `src/game/state.ts`: мини-стор на `useSyncExternalStore`
  (`phase`, собранные улики, таймер, спикер). React дёргается только на
  события; таймер обновляет UI раз в секунду, остальное живёт в refs.
- **Игрок** — `src/game/Player.tsx`: `SkeletonUtils.clone`, клипы
  `Idle/Walk/Run` смешиваются по весам демпфером (`MathUtils.damp`), а
  `timeScale` Walk/Run подогнан под реальный шаг (1.5 м/цикл, 2.4 м/цикл) —
  иначе ноги «скользят» по асфальту. Модель смотрит по **+Z** (Blender -Y →
  glTF +Z), поэтому `rotation.y = atan2(dir.x, dir.z)`.
- **Камера** — `src/game/FollowCamera.tsx`: позиция — демпфер (`damp`, λ=5.2),
  взгляд упреждает движение (`look = pos + v·0.32`, ограниченный 1.4 м) —
  поэтому не «прыгает» на стыках и уводе стика.
- **Живой мир** — `src/game/StreetLife.tsx` (трамвай на цикле Run, две машины
  Drive/Siren, прохожие-клоны детектива), `src/game/StreetProps.tsx`
  (детерминированные баки/ящики/гидрант у тротуаров) и `src/game/Rain.tsx`
  (точки дождя, добавка-шейдер, за ~1500 частиц, без лайтов). Ничего нового
  не светит — лайты на мобиле дорогие.
- **Ввод** — `src/game/input.ts` (стик/клавиши/поворот камеры) и
  `src/ui/Joystick.tsx` (свой DOM, без ре-рендеров).
- **Логика** — `src/game/GameLogic.tsx`: таймер, ближайшая улика, финал у
  машины. Позиция игрока — в `src/game/playerState.ts`.
- Осторожно с осями стрейфа: `right = forward × up = (-fz, 0, fx)`; перепутать
  — стик будет уводить вбок зеркально.

## 3. Android

```bash
npm run icons    # bash tools/make_icons.sh — иконки через ImageMagick
npm run apk      # npm run build && cap sync android && cd android && ./gradlew assembleDebug
```

- `capacitor.config.ts`: `appId com.sj0404.noirdet`, `appName Noir-Det`, `webDir dist`.
- Отображаемое имя «Нуар-Дет» — в `android/app/src/main/res/values/strings.xml`.
- `AndroidManifest.xml`: `screenOrientation="sensorLandscape"`,
  `hardwareAccelerated` и `largeHeap` у приложения.
- `android/local.properties` (в git не идёт) указывает на
  `/usr/local/lib/android/sdk`; сборка идёт wrapper-ом Gradle 8.2.1 + JDK 17.
- APK: `android/app/build/outputs/apk/debug/app-debug.apk` (~8 МБ). Подпись —
  debug-ключ; release-подпись CI тянет из ветки, если положить
  `android/keystore.properties` + `android/keystore/release.p12`.
- В `.github/workflows/build-hub-snapshot.yml` шаг подписи уже ищет эти пути.

## 4. Инструменты и команды

```bash
npm run dev / build / lint / preview
npm run models [-- --only make_env]   # .glb из tools/make_*.py (Blender)
npm run loops                         # бесшовность клипов во всех .glb
npm run shots [-- game]               # 12 кадров в ../tmp/shots + проверка на пустые
npm run icons / sync / apk
npm run release -- "сообщение" minor  # bump + тег + GitHub Release
```

Ручной кадр (диагностика ракурса):

```bash
cd dist && setsid nohup python3 -m http.server 4173 --bind 127.0.0.1 >/dev/null 2>&1 &
cd .. && node tools/capture.mjs "http://127.0.0.1:4173/?scene=game&autostart=1&dpr=1" out.png 960 540 300000
node tools/png.mjs out.png    # mean/stddev: кадр живой или пустой
```

Параметры URL стендов: `az/el/dist/tx/ty/tz/fov`, `spin`, `scene=street|model|props`,
`prop=car|tram|kit`, `clip=Idle|Walk|Run|Turn|Point|Scan|Drive|Siren|Wind`, `t`,
`ry`, `scale`, `herob=1`, `dpr`, `probe=1`, `nopost=1`, `flatroad=1`, `loop=demand`.
Игровые отладочные: `scene=game`, `autostart=1`, `px=&pz=` (спавн), `camdebug=1`
(проекция игрока в `document.title`).

## 5. Грабли, на которые уже наступали (не повторять)

- **`readPixels` из дефолтного буфера даёт нули** без `preserveDrawingBuffer`, а
  `gl.info.render.calls` после пост-обработки врёт (1 call, 12 tris). Кадр
  проверять по PNG: `tools/png.mjs`.
- **`<Environment>` из drei в headless оставляет render target привязанным** —
  сцена уходит в cubemap. Отсюда `ProceduralEnv` со сбросом `gl.setRenderTarget(null)`.
- **`useFrame` с priority > 0 отключает авто-рендер** в R3F (так работает
  `EffectComposer`) — диагностический `RenderProbe` с priority гасил сцену.
- **`Turntable` и `CameraRig` дрались за камеру** — при `?spin=` CameraRig уступает.
- **Тяжёлые кадры:** MSAA ×4 + SMAA + bloom = 2–4 мин на SwiftShader. В игре
  `GamePost` без MSAA-буфера; `dpr` в headless строго 1.
- **Двойной tone-mapping** даёт маджентовые окна. В `App.tsx` `NoToneMapping`,
  ACES только в посте.
- **Сервер поднимать через `setsid nohup`**, иначе умирает вместе с shell агента.
- `PCFSoftShadowMap` в three 0.186 удалён (только warning).
- **Capacitor + `location.search`:** в APK query пустой, поэтому дефолт — игра
  (`scene=game`). Не полагаться на query в игровом пути.
- **Оси стрейфа легко перепутать** (см. п. 2) — проверять `camdebug`-логами.
- Стенды `scene=street|model|props` должны указываться явно: раньше отсутствие
  `scene` означало улицу, теперь — игру.
- `tools/shots.mjs` держит свой сервер на порту 4173 — перед запуском убрать
  ручной `python3 -m http.server` (иначе `EADDRINUSE`).

## 6. Что делать дальше

1. **Контент дела:** диалоги с подозреваемыми, несколько дел, разные улики.
2. **Враг/напряжение:** свет фонаря-конуса, преследование, шум.
3. **Город:** перевести улицу на `street_kit.glb` (`<Clone>` + LOD), толпа,
   транспорт по маршруту, ветер на флагах.
4. **Мобильная полировка:** качество по FPS (динамический dpr), вибро, звук.
5. **Release-подпись APK** и публикация артефакта в GitHub Release.

## 7. Контекст

- `/home/runner/hub-work/noir-3d/code` — проект (git, `sj0404-collab/noir-3d`).
- `/home/runner/hub-work/noir-3d/tmp` — только временное: `shots/`, APK, Blender.
- Blender ищется сам: `$BLENDER` → `../tmp/blender-*/blender` → `/opt/tools/blender/blender` → `PATH`.
