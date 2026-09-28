# Рабочий процесс: коммит → пуш → релиз

## Главное правило

> **После КАЖДОГО пуша обязательно: коммит всех изменений → GitHub Release
> с тегом и ассетами.**

Пуш без релиза считается незавершённой работой. Порядок строго такой:

| Шаг | Команда | Что делает |
|---|---|---|
| 1. Проверка | `npm run lint && npm run build` | линтер и продакшен-сборка должны проходить |
| 2. Модели | `npm run models` | пересборка всех `.glb` из `tools/make_*.py` |
| 2a. Циклы | `npm run loops` | бесшовность клипов во всех `.glb` (0 скачков на стыках) |
| 3. Кадры | `npm run shots` | скриншоты улицы/персонажа/транспорта в `../tmp/shots` |
| 4. Коммит | `git add -A && git commit -m "..."` | одно логическое изменение — один коммит (Conventional Commits) |
| 5. Пуш | `git push origin master` | изменения попадают в `sj0404-collab/noir-3d` |
| 6. Тег + релиз | `npm run release -- "сообщение" "patch\|minor\|major"` | bumps `package.json`, ставит тег `vX.Y.Z`, собирает релиз с ассетами |
| 7. Проверка | `gh release view` | релиз виден на GitHub, ассеты скачиваются |

`npm run release` сам пушит тег и создаёт релиз, поэтому шаги 5 и 6 — одна команда:

```bash
npm run build && npm run lint          # 1
npm run models                          # 2
npm run loops                           # 2a
npm run shots                           # 3
git add -A && git commit -m "feat(env): модульные фасады и флаги на ветру"
git push origin master                  # 5
npm run release -- "Модульные фасады + флаги на ветру" minor   # 6
```

## Версионирование

Семантическая версия, тег `vX.Y.Z` в `master`:

- **major** — смена арт-дирекции: стилистика, шейдеры, палитра, общая конструкция сцены;
- **minor** — новые модели, клипы анимаций, окружение, транспорт, новые URL-параметры;
- **patch** — правки геометрии, бесшовность циклов, текстуры, тулза, документация.

Правило выбора: изменился арт-директ → major; появилась новая модель/анимация → minor;
починили → patch. Сомневаешься — бери `minor`.

## Что идёт в релиз

- **Ассеты:** скриншоты (`../tmp/shots/*.png`) и, если собраны, видео клипов.
- **Тело релиза:** короткий список — что добавлено, что изменилось, что сломано
  (если ничего не сломано — так и написать), номер версии моделей.
- **Чек-лист перед `npm run release`:**
  - [ ] `npm run build` проходит
  - [ ] `npm run lint` без ошибок
  - [ ] `public/models/*.glb` новее исходников `tools/make_*.py`
  - [ ] `npm run loops` — 0 скачков на стыках циклов
  - [ ] скриншоты сняты и не пустые: `npm run shots` печатает `mean/stddev`
    по каждому кадру (проверка идёт по самим PNG через `tools/png.mjs` —
    `readPixels` и `gl.info.render.calls` после пост-обработки врут)
  - [ ] `docs/HANDOFF.md` обновлён под текущее состояние

## Модели и ассеты

Генераторы лежат в `tools/`, общая библиотека — `tools/noirlib.py`:

| Генератор | Что делает | Ассеты |
|---|---|---|
| `tools/make_detective.py` | детектив: аниме-пропорции, риг, клипы `Idle/Walk/Run/Turn/Point/Scan` | `public/models/detective.glb` |
| `tools/make_vehicles.py` | транспорт: седан и трамвай, риг колёс, клипы езды | `public/models/car.glb`, `tram.glb` |
| `tools/make_env.py` | окружение: модульные фасады, уличный реквизит, флаги на ветру | `public/models/street_kit.glb` |

Пересборка всех моделей разом:

```bash
npm run models                 # blender ищется сам: $BLENDER → ../tmp/blender-*/blender → PATH
npm run models -- --only make_env
BLENDER=/путь/к/blender npm run models
```

Стенды для осмотра моделей (те же модели, но крупно и на нейтральном фоне):

```
?scene=model&clip=Walk&t=0.35&az=35&el=6&dist=3.2&ty=0.95   — персонаж
?scene=props&prop=car|tram|kit&clip=Drive&t=0.4            — транспорт и кит
```

Камера в `scene=props` сама кадрирует модель по габаритам; любой параметр
камеры из URL главнее. Подробности — в `docs/HANDOFF.md`.

Свои временные файлы (сборки, скриншоты, распакованный Blender) — только в
`/home/runner/hub-work/noir-3d/tmp`, никогда в `/tmp` (см. `MANIFEST.md`).

## Откат

Релиз — не точка отката. Если нужно вернуться к предыдущему состоянию:

```bash
git checkout vX.Y.Z -- public/models      # ассеты прошлого релиза
git revert <commit> && npm run release -- "откат ..." patch
```

## Ссылки

- `docs/HANDOFF.md` — что сделано, что дальше, грабли.
- `MANIFEST.md` — правила агентов по этому репозиторию.
