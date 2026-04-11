# Аудит соответствия кода требованиям

Дата проверки: 2026-04-11

Основание для сверки:
- `docs/geoservice-requirements.md`
- `docs/geoservice-prd-v1.md`
- `docs/user-stories-and-test-cases.md`

## Итог

Код соответствует требованиям частично.

Что уже реализовано:
- защищённые backend-роуты и ролевая проверка `editor`;
- загрузка слоёв и объектов по `bbox`;
- CRUD для feature на уровне API;
- optimistic concurrency с обработкой `409`;
- health-check и CI для backend/frontend;
- tile/grid cache и cursor-based подзагрузка данных карты.

Что пока не реализовано или реализовано не полностью:
- realtime через WebSocket;
- история изменений feature;
- production-ready login flow вместо dev-login;
- сущность `Project`;
- пользовательский сценарий создания feature через UI;
- аналитические геооперации;
- integration/e2e покрытие ключевых сценариев.

## Ключевые расхождения

### 1. Realtime через WebSocket отсутствует

Статус: `Не соответствует`

Доказательства в коде:
- В приложении подключены только HTTP-router'ы `auth`, `secure`, `layers`: [main.py](/C:/Repositories/geoservice/apps/backend/app/main.py#L20)
- В backend нет websocket-router'а или websocket-handler'ов в `apps/backend/app/api`
- Во frontend не найден код клиента подписки на WebSocket в `apps/frontend/src`

Последствие:
- Не выполнено требование realtime-обновления второго клиента за `1-2 секунды`
- Не закрыт demo-сценарий совместного редактирования

Что нужно сделать:
- Добавить WebSocket endpoint подписки на слой
- Ввести серверную публикацию событий `feature_created`, `feature_updated`, `feature_deleted`
- Подключить frontend-клиент подписки и обновления tile-cache/source

### 2. История изменений feature отсутствует

Статус: `Не соответствует`

Доказательства в коде:
- В API есть только layer/feature CRUD: [layers.py](/C:/Repositories/geoservice/apps/backend/app/api/layers.py#L31)
- Нет endpoint'а вида `/features/{id}/history`
- В моделях нет отдельной сущности истории правок

Последствие:
- Не выполнено требование по просмотру истории объекта
- Нельзя показать кто, когда и что изменил

Что нужно сделать:
- Добавить модель или таблицу аудита правок
- Логировать `create/update/delete`
- Добавить endpoint чтения истории feature

### 3. Авторизация остаётся dev-only

Статус: `Частично соответствует`

Доказательства в коде:
- Dev-login включается условно: [auth.py](/C:/Repositories/geoservice/apps/backend/app/api/auth.py#L71)
- Во frontend используется только dev login: [auth.ts](/C:/Repositories/geoservice/apps/frontend/src/api/auth.ts#L4)
- Dev auth panel подключается флагом: [App.vue](/C:/Repositories/geoservice/apps/frontend/src/App.vue#L10)

Что уже есть:
- JWT
- `401` при отсутствии/битом токене
- `403` для записи без роли `editor`

Чего не хватает:
- Обычного login flow для реальных пользователей
- Явной схемы хранения/проверки пользователя вне dev-сценария

Что нужно сделать:
- Определить production-сценарий входа
- Добавить нормальный login endpoint и соответствующий UI

### 4. Сущность `Project` не отражена в доменной модели

Статус: `Не соответствует`

Доказательства в коде:
- В `apps/backend/app/models` отсутствует модель `Project`
- Слой описан отдельно: [layer.py](/C:/Repositories/geoservice/apps/backend/app/models/layer.py)

Последствие:
- Требование по базовым сущностям выполнено не полностью

Что нужно сделать:
- Либо добавить `Project` в доменную модель и API
- Либо зафиксировать в документации, что для текущего MVP проектный уровень исключён из scope

### 5. Create feature не доведён до пользовательского сценария

Статус: `Частично соответствует`

Доказательства в коде:
- Backend create endpoint есть: [layers.py](/C:/Repositories/geoservice/apps/backend/app/api/layers.py#L55)
- Frontend API для create есть: [layers.ts](/C:/Repositories/geoservice/apps/frontend/src/api/layers.ts#L72)
- В UI карты есть только `Сохранить` и `Удалить`: [MapView.vue](/C:/Repositories/geoservice/apps/frontend/src/components/MapView.vue#L13)
- Редактирование стартует кликом по существующей feature: [usePolygonEditing.ts](/C:/Repositories/geoservice/apps/frontend/src/composables/map/usePolygonEditing.ts#L115)

Последствие:
- Возможность создать новый объект есть на уровне API, но не завершена на уровне UX

Что нужно сделать:
- Добавить UX-поток создания новой feature
- Определить режим `create` в edit-store или отдельный create-flow

### 6. Геоаналитика отсутствует

Статус: `Не соответствует`

Доказательства в коде:
- В текущем API нет аналитических endpoint'ов: [layers.py](/C:/Repositories/geoservice/apps/backend/app/api/layers.py#L31)
- В backend не реализованы отдельные операции вроде `count in bbox`, `area`, `within radius`

Что нужно сделать:
- Реализовать минимум 1-2 аналитические операции из требований
- Добавить тесты и UI/демо-сценарий их использования

### 7. Покрытие тестами уже лучше, но пока уже требований

Статус: `Частично соответствует`

Доказательства в коде:
- CI проверяет backend/frontend: [ci.yml](/C:/Repositories/geoservice/.github/workflows/ci.yml#L10)
- Backend unit-тесты ограничены несколькими файлами: [test_feature_service.py](/C:/Repositories/geoservice/apps/backend/app/tests/test_feature_service.py#L1)

Что уже есть:
- unit-тесты backend;
- unit-тесты frontend;
- автоматический прогон тестов в GitHub Actions.

Чего не хватает:
- integration-тестов на API CRUD;
- тестов на auth roles;
- тестов на realtime;
- e2e/acceptance тестов по пользовательским сценариям.

### 8. UI не адаптирован под роль `viewer`

Статус: `Частично соответствует`

Доказательства в коде:
- Кнопки `Сохранить` и `Удалить` всегда видимы: [MapView.vue](/C:/Repositories/geoservice/apps/frontend/src/components/MapView.vue#L13)
- Ограничение записи есть только на backend: [auth.py](/C:/Repositories/geoservice/apps/backend/app/api/auth.py#L65)

Последствие:
- Безопасность не нарушена
- Но UX не соответствует ожиданию ролевого интерфейса

Что нужно сделать:
- Скрывать или дизейблить mutate-действия для `viewer`

## Матрица соответствия

| Требование | Статус | Комментарий |
| --- | --- | --- |
| JWT и защищённые endpoint'ы | Частично соответствует | Есть JWT и role check, но login пока dev-only |
| `Viewer`/`Editor` роли | Частично соответствует | Backend соблюдает, UI не адаптирован |
| Список слоёв | Соответствует | Реализовано |
| Загрузка feature по `bbox` | Соответствует | Реализовано |
| Получение feature по id | Соответствует | Реализовано |
| Create feature | Частично соответствует | API есть, UI flow не завершён |
| Update/Delete feature | Соответствует | Реализовано |
| Optimistic concurrency / `409` | Соответствует | Реализовано и обработано на frontend |
| Realtime через WebSocket | Не соответствует | Не реализовано |
| История изменений | Не соответствует | Не реализовано |
| Мини-аналитика | Не соответствует | Не реализовано |
| Health-check | Соответствует | Реализовано |
| CI format/lint/test/build | Соответствует | Реализовано |
| `Project` как сущность | Не соответствует | В коде отсутствует |

## Приоритеты доработки

### Приоритет 1
- WebSocket realtime
- История изменений feature
- Production-ready login flow

### Приоритет 2
- Полноценный create-flow в UI
- Ролевой UX для `viewer`
- Integration/e2e тесты ключевых сценариев

### Приоритет 3
- Геоаналитика
- Возврат к вопросу о сущности `Project` и её месту в MVP

## Вывод

Текущее состояние проекта уже достаточно хорошее для технического MVP ядра карты и CRUD-редактирования. Однако по формальным требованиям продукт ещё нельзя считать полностью соответствующим спецификации из-за отсутствия realtime, истории изменений, production-auth и завершённого пользовательского сценария создания объектов.
