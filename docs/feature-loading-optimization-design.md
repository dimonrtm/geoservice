# Технический дизайн: оптимизация загрузки объектов карты

## Контекст

Текущая проблема из `project-problems-and-solutions.md`:

### 2.1. Клиент запрашивает целые GeoJSON-коллекции при каждом смещении карты

Сейчас frontend работает по схеме:

1. после `moveend` вызывает `reloadFeatures()`;
2. отправляет новый `bbox`-запрос;
3. получает полную `FeatureCollection`;
4. полностью заменяет данные источника через `source.setData(...)`.

Это подтверждается текущей реализацией:

- [useFeatureLoading.ts](C:/Repositories/geoservice/apps/frontend/src/composables/map/useFeatureLoading.ts)
- [maplibrelayers.ts](C:/Repositories/geoservice/apps/frontend/src/map/maplibrelayers.ts)
- [layers.ts](C:/Repositories/geoservice/apps/frontend/src/api/layers.ts)
- [layer_repository.py](C:/Repositories/geoservice/apps/backend/app/repositories/layer_repository.py)

## Почему это проблема

Такая схема создаёт нагрузку сразу в нескольких местах:

- лишние сетевые запросы при каждом смещении карты;
- повторная сериализация геометрий на backend;
- повторный `ST_AsGeoJSON` для каждого запроса;
- полная пересборка `GeoJSONSource` в браузере;
- слабая масштабируемость при росте объёма данных.

## Цель

Перейти от модели:

- один `bbox`-запрос на весь viewport;
- полная замена source на каждый pan/move;

к модели:

- загрузка только недостающих spatial-чанков;
- клиентский cache по grid/tile;
- агрегированная сборка текущего `FeatureCollection`;
- отдельный сценарий для просмотра и отдельный для редактирования.

## Рекомендуемая стратегия

Лучший путь для текущего проекта:

1. внедрить клиентский cache по grid/tile;
2. перестать привязывать загрузку к одному сырому `bbox`;
3. при смещении карты догружать только недостающие ячейки;
4. собирать единый `FeatureCollection` из локального cache;
5. оставить backend endpoint прежним на первом этапе;
6. позже отдельно улучшить backend-контракт выборки;
7. ещё позже, если данные вырастут, перейти на `MVT`/vector tiles.

## Почему не raw bbox-cache

Кэш по точному `bbox` малоэффективен:

- viewport меняется при каждом pan;
- даже небольшое смещение создаёт новый ключ;
- повторное использование данных получается слабым.

Grid/tile-cache работает лучше:

- соседние области используют часть уже загруженных данных;
- возврат к просмотренной области почти не требует сети;
- легче ограничивать объём cache;
- легче делать invalidation.

## Архитектурное решение

### 1. Ввести spatial cache на клиенте

Кэш должен храниться по ключу:

- `layerId`
- `zoom`
- `gridX`
- `gridY`

Пример ключа:

`layerId:zoom:gridX:gridY`

Это важно, чтобы:

- разные слои не смешивались;
- разные уровни масштаба кэшировались отдельно.

### 2. Отделить просмотр от редактирования

Нужно разделить два сценария:

- просмотр карты: работа через cache/grid;
- редактирование feature: отдельная загрузка feature по `id`.

Тогда карта не будет постоянно гонять полные геометрии через edit-flow.

### 3. Собирать агрегированный source из cache

Frontend должен:

1. вычислить набор нужных tile/grid-ключей для текущего viewport;
2. определить, какие чанки отсутствуют в cache;
3. загрузить только недостающие чанки;
4. собрать `FeatureCollection` из уже загруженных чанков;
5. выполнить один `setData(...)` уже на агрегированном результате.

## Новые frontend-модули

### `apps/frontend/src/map/feature-grid.ts`

Ответственность:

- вычисление размера grid-ячейки по zoom;
- перевод viewport bbox в набор tile/grid-ключей;
- вычисление bbox конкретной ячейки;
- утилиты для snap/grid math.

### `apps/frontend/src/composables/map/useFeatureTileCache.ts`

Ответственность:

- хранение tile-cache;
- хранение статусов загрузки;
- dedupe in-flight запросов;
- TTL и invalidation;
- сборка итогового `FeatureCollection`.

### `apps/frontend/src/contracts/map-cache.ts`

Ответственность:

- типы cache-структур.

Пример типов:

```ts
export type TileKey = string;

export type CachedTile = {
  key: TileKey;
  bbox: [number, number, number, number];
  loadedAt: number;
  featureIds: string[];
};

export type TileLoadState = "idle" | "loading" | "ready" | "error";

export type TileEntry = {
  state: TileLoadState;
  data: CachedTile | null;
  error?: string;
};

export type FeatureIndex = Map<string, ApiFeature>;
export type TileIndex = Map<TileKey, TileEntry>;
```

## Изменения в текущих файлах

### `apps/frontend/src/composables/map/useFeatureLoading.ts`

Нужно заменить текущую схему:

- `lastRequestedBbox`
- один запрос на весь viewport

на новую:

- вычисление необходимых tiles;
- загрузка только `missingTiles`;
- сборка агрегированного результата;
- обновление source из cache.

Логика должна выглядеть примерно так:

```ts
async function refreshViewport(layer: LayerDto) {
  const viewportBbox = getCurrentBbox(map.value);
  const zoom = Math.floor(map.value?.getZoom() ?? 0);

  const neededTiles = getTileKeysForViewport(viewportBbox, zoom);
  const missingTiles = neededTiles.filter((key) => !isTileReady(layer.id, key));

  await loadMissingTiles(layer.id, zoom, missingTiles);

  const fc = buildVisibleFeatureCollection(layer.id, neededTiles);
  setSourceData(map.value, getSourceId(layer), fc);
}
```

### `apps/frontend/src/map/maplibrelayers.ts`

Этот модуль можно оставить в роли render-helper.

Менять нужно не сам `setSourceData(...)`, а источник данных для него:

- сейчас туда попадает один свежий `bbox`-ответ;
- должно попадать агрегированное `FeatureCollection` из cache.

### `apps/frontend/src/composables/map/useLayerSelection.ts`

При смене слоя нужно:

- переключать namespace cache по `layer.id`;
- не смешивать объекты разных слоёв;
- пересобирать источник уже из cache выбранного слоя.

### `apps/frontend/src/stores/edit.ts`

После мутаций надо поддерживать cache консистентным.

Минимальная стратегия:

- `patch feature`: обновить `featureIndex` по `id`;
- `delete feature`: удалить feature из `featureIndex` и из `featureIds` затронутых tiles;
- `create feature`: инвалидировать tiles текущего viewport и перезагрузить их.

## Backend на первом этапе

На первом этапе можно не менять существующий endpoint:

`GET /api/v1/layers/{layerId}/features?bbox=...&limit=...`

Он уже подходит как транспортный слой для загрузки отдельных grid/tile-чанков.

## Backend на втором этапе

После внедрения client cache стоит улучшить контракт ответа:

- добавить стабильную сортировку;
- добавить `meta.returned`;
- добавить `meta.truncated`;
- добавить `meta.limit`;
- по возможности разделить `summary/full` режимы.

Пример:

```json
{
  "features": [],
  "meta": {
    "limit": 500,
    "returned": 312,
    "truncated": false,
    "bbox": [0, 0, 1, 1]
  }
}
```

Это особенно важно, если одна tile будет обрезаться по `limit` и её нельзя будет считать полностью загруженной.

## Размер grid

Практичный стартовый вариант:

```ts
function getGridStepForZoom(zoom: number): number {
  if (zoom < 10) return 0;
  if (zoom < 13) return 0.2;
  if (zoom < 16) return 0.05;
  return 0.01;
}
```

Такой вариант:

- прост в реализации;
- подходит для MVP;
- не требует сразу переходить на web-mercator tile-system;
- позже может быть заменён на настоящие xyz tiles.

## Правила cache

Рекомендуемые правила:

- namespace cache: по `layer.id`;
- TTL: `2-5` минут;
- максимальное число tiles на слой: около `100`;
- eviction: `LRU`;
- in-flight dedupe: повторный запрос к уже загружаемой tile не стартует второй раз.

## Рассмотренные альтернативы

### 1. Только `bbox`-кэш

Плюсы:

- самый дешёвый по разработке шаг.

Минусы:

- мало повторного использования;
- слабый эффект при активном pan.

Вывод:

- недостаточно как основное решение.

### 2. Grid/tile-cache поверх текущего API

Плюсы:

- лучший баланс между сложностью и эффектом;
- можно внедрить без смены backend delivery layer;
- хорошо подходит для текущего состояния проекта.

Минусы:

- нужен новый cache/state слой на frontend.

Вывод:

- это рекомендуемое решение.

### 3. Дифф-обновление source

Плюсы:

- уменьшает стоимость перерисовки.

Минусы:

- сложнее реализовать с текущим `GeoJSONSource`;
- не решает корневую проблему загрузки данных.

Вывод:

- разумно только после tile-cache.

### 4. Сразу перейти на vector tiles / `MVT`

Плюсы:

- лучшее решение по масштабируемости;
- хорошо масштабируется в production.

Минусы:

- сильно повышает сложность проекта прямо сейчас;
- потребуется отдельная архитектура для editing flow.

Вывод:

- это следующий архитектурный этап, но не лучший первый шаг.

## Рекомендуемый план внедрения

### Этап 1

1. Добавить `feature-grid.ts`.
2. Добавить `useFeatureTileCache.ts`.
3. Перевести `useFeatureLoading.ts` на tile/grid refresh.
4. Оставить backend API без изменений.

### Этап 2

1. Добавить invalidation после `create/patch/delete`.
2. Добавить unit-тесты на grid math и cache aggregation.
3. Добавить unit-тесты на TTL/invalidation.

### Этап 3

1. Улучшить backend-контракт ответа.
2. Добавить `meta.truncated`.
3. Добавить стабильную сортировку.
4. Определить стратегию пагинации/tile completeness.

### Этап 4

1. При росте данных рассмотреть `MVT`.
2. Разделить browse-delivery и edit-delivery окончательно.

## Итоговая рекомендация

Для этого проекта не стоит сразу прыгать в `MVT` или сложные diff-обновления.

Самое рациональное решение:

- внедрить grid/tile-cache на frontend;
- использовать текущий `bbox` endpoint как transport layer;
- догружать только недостающие чанки;
- хранить просмотр и редактирование раздельно;
- только потом усиливать backend-контракт и переходить к более тяжёлой spatial-архитектуре.

Именно этот путь даст максимальный выигрыш по производительности при умеренной сложности внедрения.
