# FE-03 — план реализации безопасной загрузки workspace

> **Для исполнителя:** применять superpowers:executing-plans при выполнении в текущем чате либо superpowers:subagent-driven-development при выбранном пользователем выполнении через субагентов. Выполнять задачи последовательно с отметками ниже.

**Цель:** исключить записи workspace до готовности стиля и обращения к уничтоженной карте из отложенной инициализации.

**Архитектура:** MapView сохраняет первоначальный render после createMap; watcher работает только после готовности. useMapInstance владеет отменой конкретного запуска и завершает ожидание при destroyMap. Доменный store не меняется.

**Стек:** Vue 3, TypeScript, MapLibre GL, Vitest, Vue Test Utils, jsdom; существующие зависимости.

**Спецификация:** [принятый дизайн](2026-10-31-fe-03-workspace-style-readiness-design.md); [анализ и ответы](2026-10-31-fe-03-workspace-style-readiness-analysis.md).

## Общие ограничения

- Первоначальный render предшествует ready=true. Сохранить сообщения и скрытие команд FE-02.
- После remove не вызывать API удалённого экземпляра, включая resize после nextTick.
- Отмена завершается null; disposed проверяется в MapView до обработки null как ошибки.
- Не менять backend, store, API, baseline, draft, CommandId, recovery и условие позиционирования по AOI.
- Не добавлять timeout, runtime recovery, переключение стилей, новые UI или зависимости.
- Git add/commit/push запрещены AGENTS.md; оставить изменения unstaged. Имеющиеся пользовательские изменения не перезаписывать.
- Документы на русском, текстовые файлы UTF-8 с LF. Артефакты только в docs/sprint_2.

## Фокус проверки

1. load наступает до первого nextTick — событие не теряется; тест задачи 1.
2. callback уже вошёл в await, когда карту удалили — поздний resize запрещён; тест задачи 1.
3. Старый запуск завершается после создания следующего — ссылка и готовность новой карты не изменяются; тест задачи 1.
4. Workspace и key меняются несколько раз до загрузки — первыми применяются последние данные и текущий fit; тест задачи 2.
5. Обратное событие workspaceFitted меняет props родителя — не зацикливает fit и не открывает команды преждевременно; тест задачи 2.

## Задача 1. Отмена инициализации конкретного экземпляра

**Файлы:** изменить `apps/frontend/src/composables/map/useMapInstance.ts`; создать `apps/frontend/src/composables/map/useMapInstance.test.ts`.

**Интерфейс:** сохранить `useMapInstance(mapEl: Ref<HTMLDivElement | null>, style: StyleSpecification = baseMapStyle)` и возвращаемые `map`, `createMap(): Promise<Map | null>`, `destroyMap(): void`. Новое поведение — отменённый createMap завершается null; успешно завершённый возвращает живой экземпляр.

- [x] Добавить тестовый double Map с реестром обработчиков load, журналом вызовов и возможностью вручную продолжить nextTick. Настоящий composable исполняется; MapLibre Map/NavigationControl подменены. Использовать управляемые Promise, без реальных задержек.
- [x] Добавить тесты `cancels_before_initial_tick`, `cancels_waiting_for_load`, `cancels_inside_load_tick`, `captures_load_before_initial_tick`, `ignores_old_start_after_recreate`, `destroy_is_idempotent`, `returns_live_map_after_load`. Основные assertions:

```ts
expect(await cancelledCreation).toBeNull();
expect(oldMap.remove).toHaveBeenCalledTimes(1);
expect(callsAfterRemove).toEqual([]);
expect(map.value).toBe(newMap); // только сценарий нового запуска
expect(await successfulCreation).toBe(newMap);
```

В тесте снятия подписки проверить off с тем же callback; отдельно вызвать сохранённый callback вручную после отмены, чтобы проверить защиту уже поставленного в очередь продолжения. Каждый ожидающий Promise должен завершаться; отсутствие вызовов само по себе недостаточно.
- [x] Из `apps/frontend` запустить `npm.cmd run test -- src/composables/map/useMapInstance.test.ts --maxWorkers=2`. Зафиксировать ожидаемые FAIL на текущем коде: поздний resize, незавершённая отмена или пропущенный load. Ошибки загрузки тестового окружения не считать доказательством дефекта.
- [x] Реализовать приватный контекст запуска с идентичностью экземпляра, признаком отмены, callback load и завершением ожидания. Установить подписку до первого await; проверять актуальность после каждого await. В destroyMap инвалидировать запуск, снять подписку до remove и завершить ожидание; повторная очистка безопасна. Не менять публичный тип результата и не добавлять реактивную готовность стиля. Асинхронный callback не должен оставлять необработанное отклонение: ошибки действующего запуска передаются createMap, отменённое продолжение бездействует.
- [x] Повторить команду тестов задачи 1; ожидается PASS. Проверить, что успешный resize и возврат карты не пропали из-за защиты отмены.

## Задача 2. Отрисовка только актуального workspace после запуска

**Файлы:** изменить `apps/frontend/src/components/MapView.vue` и `apps/frontend/src/components/MapView.test.ts`. `EditorWorkOrdersView.vue` и store — источники контракта, не цели изменения.

**Интерфейс:** потребляет createMap из задачи 1. Сохраняет props workspace/workspaceKey/shouldFitWorkspace и события `workspaceFitted: [workspaceKey: string]`, `readyChange: [ready: boolean]`. Внутренний `renderWorkspace(): void` остаётся доступен первичной отрисовке до ready=true.

- [x] Добавить `defers_workspace_updates_until_startup`: при существующем map и pending createMap последовательно заменить workspace A → B → C через setProps с ожиданием Vue между заменами; до resolve проверить:

```ts
expect(mocks.ensureWorkspaceLayers).not.toHaveBeenCalled();
expect(mocks.setWorkspaceData).not.toHaveBeenCalled();
expect(mocks.fitWorkspaceToAoi).not.toHaveBeenCalled();
expect(wrapper.emitted('workspaceFitted')).toBeUndefined();
expect(wrapper.emitted('readyChange')).toEqual([[false]]);
```

После resolve проверить первую передачу C в setWorkspaceData, текущий key в workspaceFitted и ready=true после успешного render. Тестовые A/B/C должны иметь отличающиеся geometry/token, чтобы проверять данные, а не только число вызовов.
- [x] Добавить `uses_latest_fit_request` с изменением key и shouldFitWorkspace до resolve; при false fit отсутствует. Добавить `renders_readback_without_refit` после ready с shouldFitWorkspace=false. В `fit_ack_does_not_repeat_fit` родитель после workspaceFitted сбрасывает shouldFitWorkspace; повторный setData допустим, повторный fit — нет.
- [x] Добавить проверку unmount после resolve до продолжения mounted: нет render и нового ready=true. Существующие тесты ошибки render, null, rejected startup и всех трёх режимов сохранить. Проверить отсутствие workspace-записей при изменении props после ошибки запуска.
- [x] Запустить `npm.cmd run test -- src/components/MapView.test.ts --maxWorkers=2`; новые проверки ранней записи должны дать FAIL на прежнем watcher.
- [x] Ограничить watcher готовностью текущего MapView и отсутствием disposal. Сохранить отдельный первоначальный вызов renderWorkspace после createMap, чтение актуальных props и порядок render → setReady(true). Не добавлять очередь snapshots и не менять shouldFitWorkspace/store.
- [x] Повторить тесты задачи 2; ожидается PASS, включая существующие FE-02 проверки.

## Итоговая проверка и отчёт

- [x] Из `apps/frontend` запустить `npm.cmd run test -- src/composables/map/useMapInstance.test.ts src/components/MapView.test.ts src/components/EditorWorkOrdersView.test.ts src/components/WorkspaceLineInteraction.test.ts src/map/workspace-layers.test.ts --maxWorkers=2`; ожидается PASS без необработанных исключений.
- [x] Запустить `npm.cmd run typecheck` и `npm.cmd run build`; ожидается exit 0. Затем один полный `npm.cmd run test -- --maxWorkers=2`; повторять только при изменениях или расследовании отказов.
- [x] Проверить реальный браузер: обычное открытие workspace и уход при незавершённой загрузке; по возможности воспроизвести ранний readback при задержанной карте. Сохранять способ управления задержкой и наблюдения. Не подменять отсутствие реального воспроизведения результатами mocks; явно указать непроверенные сценарии. Временную диагностическую подмену не оставлять в product-коде.
- [x] Проверить diff на scope и LF; выполнить `git diff --check`. Новые файлы отдельно проверить на CR, поскольку git ls-files их не показывает.
- [x] Записать `docs/sprint_2/2026-10-31-fe-03-workspace-style-readiness-implementation-report.md`: что исправлено, RED/GREEN evidence, команды/результаты и ограничения браузерной проверки. Обновить статус FE-03 в frontend-review и компактные ссылки README/общего ревью, сохранив чужие изменения. Не создавать отдельную agent memory или repository-change ingest без нового уникального знания: этот дизайн и отчёт сохраняют техническую причину.

## Самопроверка плана

Первичная отрисовка, watcher, актуальность props и fit покрыты задачей 2. Все точки отмены и сквозная гарантия покрыты задачей 1 и компонентной проверкой задачи 2. Публичные типы сохраняются. Пять пограничных случаев из фокуса распределены по тестам. Новые продуктовые требования и изменения доменной модели не добавлены.

Статус: выполнен в текущем чате по поручению пользователя. Итоги и границы browser harness — в отчёте о реализации и execution ledger.
