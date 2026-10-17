# День 10 — отчёт реализации взаимодействия с линией

Дата: 2026-10-17. Основание: [принятый дизайн и ответы D10-Q01–Q10](2026-10-17-day-10-map-interaction-analysis.md). Пользователь отдельно разрешил реализацию.

Результат Дня 10 реализован: Editor выбирает eligible line и перемещает единственную внутреннюю вершину. Подтверждён этап M3 «взаимодействие с картой»; Save/Cancel/Revert controls и полный путь сохранения остаются Дню 11 и последующим задачам.

## Изменения

- `apps/frontend/src/domain/workspaceLineInteraction.ts`: eligibility existing XY LineString ровно с тремя координатами, ограничение persisted changeSet и проверка candidate относительно полного AOI. Проверяются оба сегмента, отверстия Polygon, MultiPolygon, границы, нулевые сегменты и наложение. Новых зависимостей нет.
- `apps/frontend/src/composables/map/useWorkspaceLineInteraction.ts`: выбор по уникальным ID, список при неоднозначном попадании, один draggable Marker, обновление local draft во время drag, удержание последней допустимой позиции с причиной. Недопустимые координаты не передаются в store.
- `apps/frontend/src/components/WorkspaceLineInteraction.vue`: причины ограничений, список линий и подтверждение отмены dirty draft. Отказ сохраняет правку; подтверждение снимает выбор либо выбирает новую цель. Диалоги поддерживают фокус, Tab и Escape.
- `MapView.vue` и `EditorWorkOrdersView.vue`: подключение взаимодействия после загрузки карты только для открытого interactive workspace. Legacy editing и empty modes сохранены.
- `apps/frontend/src/map/workspace-layers.ts`: независимая GeoJSON-проекция current/candidate, выделение выбранной линии, явное сохранение строкового feature ID через `promoteId`.

Pinia остаётся единственным владельцем draft. Endpoints, current snapshot, token, persisted changeSet и associations не изменяются жестом. Cancel локальной правки не вызывает HTTP. При недоступном контексте marker удаляется; списки и подтверждения сбрасываются при смене контекста. Backend, migrations, dependency manifests не менялись.

## Проверки

| Проверка | Результат |
| --- | --- |
| Новые geometry tests | 5 tests PASS: eligibility, boundary, straight line, outside, zero/backtracking, holes, concavity, MultiPolygon |
| Новые interaction component tests | 7 tests PASS с реальным Pinia store: drag/projection, invalid/reentry, список и дубли, cancel/switch, недоступная feature, teardown, interrupted drag, фокус |
| Подключение Editor и string identity map source | Отдельные regression tests PASS |
| Заключительный `npm test -- --maxWorkers=2` | 32 suites, 230 tests PASS |
| `npx vue-tsc -p tsconfig.app.json --noEmit` | PASS до финального исправления promoteId; заключительный `npm run build` повторно проверил TypeScript через `vue-tsc -b` |
| Заключительный `npm run lint` | PASS |
| Заключительный `npm run build` | PASS; JS bundle около 1,219 MB до gzip; предупреждение Vite о chunk > 500 kB |
| `git diff --check` | PASS |

Первый обычный полный `npm test`, запущенный одновременно с lint/typecheck, дал 6 failures: начальные import tests в `MapView`, auth, workOrders и useLayerRealtime превысили 5 секунд; после timeout первый realtime test повлиял на два следующих assertion cases. Повтор полного набора с двумя workers прошёл, включая эти suites. Test timeout и конфигурация проекта не увеличивались. Финальный повтор после всех исправлений также прошёл с двумя workers.

Sandbox первоначально блокировал esbuild (`spawn EPERM`). Vitest/build запускались повторно с разрешением вне sandbox. Доступ к Docker pipe также потребовал разрешённого запуска.

## Review и найденные дефекты

Независимое review выявило две P2-проблемы. Обе воспроизведены failing tests, исправлены и проверены:

1. Прерванный drag мог оставить `suppressClick=true` после удаления marker; cleanup теперь сбрасывает флаг и таймер.
2. Переход «список → подтверждение» не менял boolean открытой панели и терял фокус; watcher теперь различает тип панели.

Повторное read-only review подтвердило исправления и не выявило новых Critical/Important замечаний. Ревьюер не запускал тесты повторно; результаты запуска приведены отдельно выше.

Ручная проверка дополнительно выявила потерю соответствия строкового feature ID при hit testing реальной карты: линия отображалась, но клик не находил её в workspace. Исправлено явным `promoteId: __workspaceFeatureId` и этой presentation property, получаемой из исходного `feature.id`. Свойство добавляется только в копию для карты, current не меняется. Для current и draft используется единый путь проекции; добавлен failing → passing regression test. После исправления реальный клик выбирает линию.

## Ручная проверка demo

После сообщения пользователя о запуске Docker проверены сервисы. Обновлён только локальный `frontend-dev`; БД и backend не пересоздавались, volumes не удалялись. Исправление map source доставлено в этот же контейнер для повторной проверки.

В браузере `http://localhost:5173` под demo Editor выполнены:

1. Открытие `WO-001`: 19 объектов, 9 связей.
2. Выбор трёхвершинной demo линии и появление одного внутреннего Marker.
3. Drag: линия визуально изменяется вместе с Marker, endpoints неподвижны.
4. Drag указателя за правую границу AOI: Marker остаётся внутри, отображается причина ограничения. Отпускание снаружи не переносит вершину наружу.
5. Следующий drag обратно внутрь AOI: движение доступно, сообщение исчезает.
6. Клик по пустоте с dirty draft → подтверждение. «Продолжить правку» сохраняет геометрию и выбор; последующее подтверждение отмены восстанавливает исходную линию и убирает Marker.
7. Клик по двухвершинной линии показывает причину недоступности. Выбор допустимой линии без движения и клик по пустоте снимают выбор без подтверждения.

Скриншоты:

- [Вершина после перемещения](evidence/day-10/vertex-moved.png).
- [Блокировка выхода за AOI](evidence/day-10/aoi-blocked.png).
- [Линия после локальной отмены и снятия выбора](evidence/day-10/local-edit-cancelled.png).

Browser tool выполняет отдельные drag-жесты от точки до точки. Возвращение указателя в допустимую область без отпускания кнопки проверено последовательностью событий в component test, а не объявлено отдельной ручной проверкой. Выбор из нескольких eligible lines и переход между ними проверены на синтетическом component fixture: основной demo содержит одну доступную для этого сценария линию. Отверстия и MultiPolygon проверены unit tests, не синтетической подменой demo AOI.

## Границы результата

- Клавиатурное перемещение самой вершины, Save/Revert controls и полный recovery UI остаются следующему дню. Текущий диалог отмены включён по прямым ответам D10-Q07/Q08.
- Локальная проверка XY не обещает идентичность PostGIS после серверной canonicalization в численных пограничных случаях. Policy grid не копируется на клиент; серверная validation остаётся обязательной.
- Ручная проверка не выполняла Save и не меняла persisted geometry. В конце локальная правка отменена.
- Все изменения оставлены unstaged. `git add`, `git commit`, `git push` не выполнялись.
- Новая agent memory и repository-change ingest не создавались: принятые решения, runtime-связи и причины исправлений сохранены в анализе, коде, тестах и этом отчёте; отдельное дублирование в wiki не требуется для текущей задачи.
