# F1 — итоговое независимое ревью

Дата: 2026-11-17. Проверены рабочий diff, новые production-файлы, тесты, принятые дизайн/план и rulings. Ревью read-only, без изменений и тяжёлых запусков. Critical: 0, Important: 2, Minor: 0.

## 1. Revert не связывался с новой попыткой — исправлено

`confirmRevert` отправлял новую команду, сохраняя предыдущую `activeSaveAttempt`. После Save completion Revert отбрасывался как чужая команда; при чистом выбранном draft — как completion без подходящей draft identity. Recovery record уже удалён, но localPhase оставалась sending.

Исправление: перед отправкой Revert фиксируются текущий EditorContext, commandId и draftIdentity; navigationId остаётся null. Общий completion завершает только эту попытку. Две интеграционные регрессии Save→Revert и clean selection→Revert получили RED (sending), затем GREEN. Проверяются idle, commandResult, удаление recovery record и draft.

## 2. Guard пропускал aliases/exports/helper escapes — исправлено

Guard не узнавал переименованный импорт storeToRefs, отдельный export specifier и передачу mutable owner reference неизвестному импортированному helper.

Исправление: отслеживаются импортные bindings storeToRefs, named/default exports и передача owner state импортированным helpers. Известные чистые readers/copy constructors имеют явный список проверенных контрактов по source+name. Новые fixtures получили RED, затем GREEN; production guard показывает 0 нарушений. Это локальный AST-анализ известных bindings, не доказательство для произвольного JavaScript/any/reflection.

## Границы заключения

Ревьюер не оценивал полную развязку auth/HTTP (F2), внутренний recovery I/O (F4) и не предполагал успех выполнявшихся тестов/M4. Итоговые команды и результаты перечислены в [verification](2026-11-17-stage-2-f1-verification.md).
