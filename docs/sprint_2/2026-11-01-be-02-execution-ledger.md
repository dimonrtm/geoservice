# Журнал исполнения — docs/sprint_2/2026-11-01-be-02-plan.md

## Подготовка

- Используются executing-plans, test-driven-development и verification-before-completion.
- Исходный прогон целевых service/publisher/HTTP tests: 32 passed, 2 dependency deprecation warnings.
- Ruling: работа в существующем checkout `first-edit-save` — согласно приоритету повторного использования текущего checkout; исходных изменений кода нет. Новая worktree не создаётся.
- Ruling: журнал и evidence находятся в `docs/sprint_2`, как запросил пользователь. Git-ориентированные task-start/task-done/review-package заменяются явными записями и проверкой unstaged diff, поскольку commit запрещён AGENTS.md.
- Pre-flight: задачи 1 и 2 используют неизменную сигнатуру FeatureService.update_feature; противоречий интерфейсов нет.
- Docker доступен после разрешённого sandbox escalation; прежнее ограничение доступа снято.

## Задача 1

Регрессионные и контрактные тесты написаны до изменения сервиса. Проверяемая ошибка: `{}` не должно заменяться старым словарём или приводить к отказу при сборке DTO. Контрактные тесты остальных случаев фиксируют уже работающие требования, поэтому ожидаемо могут проходить до исправления.

- RED: 3 failed, 1 passed; неправильный старый словарь и два BusinessValidationException. Уже пустой словарь без новой geometry маскирует дефект и проходит.
- GREEN: 45 passed, 2 прежних dependency warnings. Проверены service/schema/publisher/HTTP tests.
- Task 1: complete. Production-изменение ограничено выбором properties по `is not None`.

## Задача 2

Написаны шесть параметризованных интеграционных сценариев: commit, stale version, ошибка после реального UPDATE; каждый с geometry=None и новой geometry. Проверки publication выполняются снаружи callback: сервис подавляет исключения publisher, поэтому assertion внутри callback мог бы дать ложноположительный результат.

- Task 2: complete. `test_legacy_patch_properties.py`: 6 passed в проекте `geoservice-be02-0da6492d`; Alembic прошёл, контейнер БД и сеть удалены в finally.

## Задача 3

- Общая регрессия: 348 passed, 2 прежних warnings.
- Black --check: 4 files would be left unchanged. Ruff: All checks passed.
- Результаты и границы сохранены в `evidence/be-02/verification.md`.
- Финальное read-only ревью запрошено через requesting-code-review; проверяется unstaged diff и новые файлы, без commit range.
- Финальное независимое ревью: Critical/Important/Minor — нет. Ревьюер оценил код и тесты; завершение sprint-документов проверено исполнителем.
- Final Ruling: гарантии WebSocket-доставки, полный RETURNING, Utility Save и BE-03/AR-02/AR-03 остаются вне scope согласно принятому дизайну; они не затронуты и не объявлены исправленными. Цена границы — прежние ограничения legacy realtime сохраняются.
- Final Ruling: сквозной HTTP+WebSocket+БД прогон не добавляется — принятый план разделяет schema/HTTP, настоящий service/repository и publisher serialization. Фактическая доставка по сети не заявляется подтверждённой.
- Final Ruling: используется сохранение текущего checkout без интеграционных Git-операций — прямое правило AGENTS.md приоритетнее меню finishing-a-development-branch. Дополнительные проверки сверх согласованного набора не запускались без новой причины.
- Task 3: complete. Evidence и реестр обновлены, diff --check успешен, LF проверены у всех 11 изменённых/новых файлов. Index пуст; add/commit/push не выполнялись. Новая память не создаётся: знания сохранены в артефактах BE-02.
