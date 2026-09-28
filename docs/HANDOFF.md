# Нуар-Дет 3D — передача состояния

Дата: 28.09.2026. Репозиторий: `https://github.com/sj0404-collab/noir-3d`
(ветка `master`, релиз `v0.1.0`, push без незакоммиченного хвоста).

Проект — перенос «Нуар-Дета» с three.js на React Three Fiber с приоритетом
качества картинки (PBR, мягкие тени, IBL, пост-обработка) вместо текущего
toon-шейдера. Масштаб — один город Ноктис, стиль сохранён.

---

## 1. Что уже работает

| Часть | Состояние |
|---|---|
| Каркас Vite + React 19 + TS + R3F + drei + postprocessing | собрано, `npm run build` проходит |
| Ночной нуар-участок (`src/scene/NoirStreet.tsx`) | рендерится, PBR + тени + мокрый асфальт |
| IBL-окружение (`src/scene/ProceduralEnv.tsx`) | PMREM-бейк, работает |
| Пост-обработка (`src/scene/Post.tsx`) | bloom, хром. аберрация, зерно, виньетка, ACES, SMAA |
| Персонаж (`tools/make_detective.py` → `detective.glb`) | v4: аниме-пропорции, 26 костей, 6 бесшовных клипов |
| Транспорт (`tools/make_vehicles.py`) | седан и трамвай, колёса на костях, 4 клипа, циклы бесшовные |
| Окружение (`tools/make_env.py` → `street_kit.glb`) | 2 фасада + 11 предметов реквизита + флаг на ветру (клип `Wind`) |
| Стенды: `scene=model` (персонаж), `scene=props` (car/tram/kit) | общий `Studio` + автокадрирование по габаритам |
| Скриншоты (`npm run shots` → `../tmp/shots`) | 10 кадров, детерминированно, проверка «пустого» PNG |
| Коммиты | всё запушено в `master`, тег `v0.1.0` |

## 2. Инструменты

```bash
# Blender 4.2.9 LTS — портативный, распакован в tmp (см. MANIFEST.md)
ls ../tmp/blender-4.2.9-linux-x64/blender        # может потерять +x и lib/ после
chmod +x ../tmp/blender-4.2.9-linux-x64/blender  # восстановления раннера —
tar -xJf ../tmp/dl/blender.tar.xz -C ../tmp      # тогда распаковать заново
../tmp/blender-4.2.9-linux-x64/blender --version

chromium --version      # системный, для headless WebGL (SwiftShader)
ffpeg -version          # В ЭТОМ ОКРУЖЕНИИ НЕТ — ставить для видео/контакт-листа
```

`blender` ищется автоматически: `$BLENDER` → `../tmp/blender-*/blender` →
`/opt/tools/blender/blender` → `PATH`.

## 3. Команды

```bash
cd /home/runner/hub-work/noir-3d/code
npm ci

npm run build        # tsc -b && vite build
npm run lint         # oxlint (0 ошибок, ~10 warnings в src/scene — см. п. 6)
npm run models       # пересборка всех .glb из tools/make_*.py (~40 c на каждый)
npm run models -- --only make_env          # один генератор
npm run loops        # бесшовность циклов во всех .glb (check_loops.py)
npm run shots        # 10 кадров в ../tmp/shots + проверка на пустые
npm run shots -- car # только кадры по фильтру
npm run release -- "сообщение" minor        # bump + тег + GitHub Release
```

Ручной кадр (для отладки ракурса):

```bash
cd dist && setsid nohup python3 -m http.server 4173 --bind 127.0.0.1 &
cd .. && node tools/capture.mjs "http://127.0.0.1:4173/?scene=props&prop=tram&clip=Run" out.png 1024 640 300000
node tools/png.mjs out.png    # mean/stddev: кадр живой или пустой
```

Параметры URL: `az/el/dist/tx/ty/tz/fov` — камера (`CameraRig`), `spin` —
turntable (`Turntable`, перебивает `CameraRig`), `scene=model` — стенд
персонажа, `scene=props&prop=car|tram|kit` — стенд моделей,
`clip=Idle|Walk|Run|Turn|Point|Scan|Drive|Siren|Wind` + `t=0..1` — поза,
`ry`, `scale`, `herob=1` — поставить персонажа в улицу, `dpr`,
`probe=1` — диагностика в `document.title`, `nopost=1`, `flatroad=1`,
`loop=demand`.

## 4. Модели

Всё генерируется из `tools/` общей библиотекой `noirlib.py` (палитра, риг,
запекание бесшовных циклов, экспорт glTF/blend). Пересборка детерминирована:
одинаковый код → одинаковые байты, можно сравнивать `git diff` по бинарям.

| Модель | Файл | Клипы | Проверка циклов |
|---|---|---|---|
| Детектив | `detective.glb` | Idle 96, Walk 32, Run 24, Turn 40, Point 24, Scan 48 | 6/6 бесшовные |
| Седан | `car.glb` | Drive 48, Idle 48, Siren 24 | 3/3 бесшовные |
| Трамвай | `tram.glb` | Run 60 | 1/1 бесшовный |
| Улица | `street_kit.glb` | Wind 48 | 1/1 бесшовный |

Персонаж прошёл путь v1 → v2 → v3 → v4:

- **v1** (капсулы) — «картошка на ножках», пропорции ~5 голов;
- **v2** (конусы + воксельный ремеш всего тела) — **провалился**: ремеш с
  вокселем 0.022 запаял руки в торс, полы пальто проглотили ноги;
- **v3** — ремеш по группам конечностей, суставы разделены, ~8 голов;
  не бесшовные `Walk`/`Run`;
- **v4** (текущая) — общая библиотека `noirlib`, аниме-пропорции (голова ~6
  ростовых единиц, худые конечности, острые скулы, узкое пальто с разрезом),
  26 костей, все 6 клипов запечены в бесшовные циклы `noirlib.bake_loop`
  (проверено `npm run loops`: скачков на стыках 0).

Косметика, которую всё ещё стоит править (на геометрию не влияет): полы
пальто `CoatTail`, плоское лицо (челюсть/скулы), выпирающие локти, спрятанный
ремень.

## 5. Что делать дальше (в порядке приоритета)

1. **Отдать обещанное пользователю** — главный незакрытый вопрос:
   - контакт-лист 3×2 по модели (перед, 3/4, лево, право, зад, сверху) —
     `ffmpeg -i a.png -i b.png ... -filter_complex tile=3x2 out.png`
     (**ffmpeg в этом окружении нет**);
   - видео клипов (Idle/Walk/Run/Turn) mp4 H.264 + webm, 60 fps, без звука,
     из PNG-последовательности: `ffmpeg -framerate 60 -i frames/%04d.png ...`;
   - сводное видео «поворотный круг 360° + все анимации» — через `?spin=`.
2. **Перевести улицу на `street_kit.glb`**: сейчас `NoirStreet.tsx` собирает
   фасады процедурно, а готовые модели (`facade_a/b`, реквизит, флаги) в сцене
   не используются. Нужен `<Clone>` вместо ремеша и LOD на дальний план.
3. **Сцена до Genshin-уровня**: ветер-анимация флагов в сцене, толпа с LOD,
   транспорт в движении по маршруту.
4. **Карта порта фич** из three.js-версии (`nuar-det` v1.11.0) в R3F.
5. **Косметика персонажа** (п. 4) — после видео, видна на контакт-листе.

## 6. Грабли, на которые уже наступили (не повторять)

- **`readPixels` из дефолтного WebGL-буфера всегда даёт нули**, если нет
  `preserveDrawingBuffer`; после пост-обработки `gl.info.render.calls` тоже
  врёт (1 call, 1 triangle — это финальный полноэкранный пасс композитора).
  Проверять кадр надо по самому PNG: `tools/png.mjs` (mean/stddev, без
  зависимостей). `RenderProbe` с `probe=1` в `document.title` для этого
  годится только как диагностика, не как критерий.
- **`<Environment>` из drei в headless-прогоне оставляет render target
  привязанным** — сцена уходит в cubemap и кадр выходит пустым. Отсюда
  `ProceduralEnv` со сбросом `gl.setRenderTarget(null)`.
- **`useFrame` с `priority > 0` отключает авто-рендер** в R3F (так работает
  `EffectComposer`). Диагностический `RenderProbe` с priority 2/3 из-за этого
  гасил сцену.
- **`Turntable` и `CameraRig` дрались за камеру**: оба ставят позицию в
  `useFrame`, и `CameraRig` перебивал `?spin=`. Теперь при наличии `spin`
  CameraRig уступает.
- `chromium --screenshot` с `--virtual-time-budget` может снять
  **недоприсованный буфер** (получались пустые кадры). Надёжен только
  Playwright с ожиданием `window.__ready`.
- `page.screenshot()` по умолчанию таймаутится 30 c — на SwiftShader кадр не
  успевает; нужен `timeout: 180000`.
- **Кадр 1280×720 с пост-обработкой на SwiftShader — 2–4 минуты** (MSAA ×4 +
  SMAA + bloom). Три кадра прогрева `RenderProbe` могут не уложиться в
  дефолтные 90 c, поэтому `tools/shots.mjs` даёт capture 300 c, а стенды
  снимаются в 640–1024 px по ширине. Для видео это ~40 кадров на клип.
- Тяжёлые кадры: 5 теневых point-light'ов = 30 проходов кубических карт.
  Держать максимум один. `dpr` в headless — строго 1.
- Двойной tone-mapping (renderer + эффект пост-обработки) даёт цвета
  вроде маджентовых окон. В `App.tsx` стоит `NoToneMapping`, ACES живёт
  только в `Post`.
- Сервер надо поднимать через `setsid nohup ... &`, иначе он умирает вместе
  с shell-командой агента. В `tools/shots.mjs` сервер свой и гасится вместе
  со скриптом.
- `PCFSoftShadowMap` в three 0.186 удалён (предупреждение в консоли).
- **Раннер восстанавливает `../tmp` частично**: распакованный Blender может
  прийти без `lib/` и без бита `+x` — тогда `blender` не стартует
  (`libblender_cpu_check.so`), лечится перераспаковкой `tmp/dl/blender.tar.xz`.
- **Локальный `master` может быть сиротским**: восстановление состояния
  раннера иногда делает корневой коммит с тем же деревом, что и `origin/master`.
  Пушить нельзя (non-fast-forward) — лечится
  `git rebase --onto origin/master <сиротский-коммит> master`.

## 7. Контекст репозиториев

- `/home/runner/hub-work/noir-3d/code` — этот проект, запушен в
  `sj0404-collab/noir-3d` (`master`, релиз `v0.1.0`).
- `/home/runner/hub-work/noir-3d/tmp` — только временное: сборки, кеши,
  скриншоты, распакованный Blender. В git не попадает.
- `nuar-det/`, `code-v1.2.1-OLD/`, `wip-backup-20260926/` — клоны и бэкапы
  **прошлой машины, в этом окружении их нет**. Исходник фич для порта —
  `sj0404-collab/nuar-det` v1.11.0.
