# INF-05: отчёт реализации

Дата: 2026-11-01. Статус: реализовано и локально принято в согласованных границах.
Основание: [дизайн](2026-11-01-inf-05-save-size-design.md),
[план с принятой поправкой](2026-11-01-inf-05-save-size-plan.md),
[журнал исполнения](2026-11-01-inf-05-execution-ledger.md).

## Изменение и границы

В `apps/frontend/nginx.conf` добавлен отдельный regex location для канонического
geometry path с `client_max_body_size 0`. Save и Revert передают полную геометрию
без прежнего ограничения nginx 1 MiB. Соседние API и path suffix сохраняют предел.
Сохранены существующие proxy-настройки, upstream URI, auth headers и ответы API.

Это единственное изменение продукта. UI, backend, доменные guards, протокол
команды, recovery, buffering и таймауты не менялись. CI/workflow и автоматические
suites не изменены; runner запускается только вручную.

При реализации исправлен недосмотр анализа: текущий UI по принятому решению
Дня 10 редактирует только трёхвершинные линии. Пользователь согласовал большую
проверку настоящим API/nginx/БД и отдельный browser cycle на штатной линии.
Поэтому результат не выдаётся за поддержку редактирования больших линий в UI.

## Доказательства

| Проверка | Результат и evidence |
| --- | --- |
| Итоговая полная приёмка | [fc9eedcf](evidence/inf-05/geoservice-inf05-fc9eedcf/verification.json): документированная PowerShell-команда, exit 0; proxy 7/7, большой API/DB цикл, штатный browser cycle, cleanup passed |
| RED до изменения nginx | [9a18a593](evidence/inf-05/geoservice-inf05-9a18a593/verification.json): тело 1 048 577 байт получает 413 вместо upstream 200 на geometry path и path с query; остальные контроли верны |
| GREEN после изменения | [9ad6b299](evidence/inf-05/geoservice-inf05-9ad6b299/verification.json): 7/7 HTTP cases, проверены method, URI, SHA-256 и размер тела |
| Большой API/DB цикл | [0752c577](evidence/inf-05/geoservice-inf05-0752c577/verification.json), поле `largeApi`: 60 003 вершины, Save/Revert по 1 654 616 байт, успешные GET/readback и replay; baseline/network неизменны. Этот ранний запуск целиком failed из-за последующей browser-фазы |
| Штатный browser cycle | [f0052c25](evidence/inf-05/geoservice-inf05-f0052c25/verification.json): Chromium 156.0.8078.4, Save → reload → Revert → reload, изменена только вершина 1, 401/422 guards, ошибок страницы нет |
| Cleanup после ошибки proxy | [a8b2e141](evidence/inf-05/geoservice-inf05-a8b2e141/verification.json): ожидаемый exit 1, cleanup passed |
| Cleanup после подготовки БД | [84d2a5f1](evidence/inf-05/geoservice-inf05-84d2a5f1/verification.json): ожидаемый exit 1, cleanup passed, включая volume |
| Некорректный аргумент runner | До исправления оставался один temp dir; после — exit 1 и ноль новых каталогов. Проверено сравнением каталогов до/после; журнал содержит результат |

Полный runner строит production frontend/API из текущего checkout, включая
незакоммиченные изменения, с действующими `.dockerignore`. Fixture создана только
в собственной БД. Между большой API-фазой и browser-фазой собственный volume
пересоздаётся, чтобы не менять baseline открытой версии. После завершения удаляются
собственные контейнеры, сеть, volume и временный config; evidence остаётся.

## Диагностика и review

Сначала локальная проверка соседних координат fixture была медленной из-за
повторного `ST_PointN`; заменена на `ST_DumpPoints + lag`. Продукт не изменялся.
Browser smoke из INF-02 вычислял координаты до появления панели команд; screenshot
и `map-target.json` показали смещение canvas. Теперь сценарий ожидает панель
готовой карты и выбирает линию настоящими кликами около расчётной точки.
Никакого вызова store selection или подмены API в browser-фазе нет.

Независимое read-only review не нашло Critical или дефектов продукта. Important —
незавершённая browser-приёмка — устранён успешным browser-only и итоговым полным
прогоном. Два Minor устранены: проверка аргументов до
создания temp directory и устаревшая формулировка плана. Повторное review не
выполняется; исправления проверяются локально. Отложенных minor-замечаний нет.

Итоговый прогон: Chromium 156.0.8078.4, 60 003 вершины в API fixture,
по 1 654 616 байт в больших Save и Revert; в обычном UI — 191 и 170 байт.
Обе фазы подтвердили неизменность baseline и authoritative network. Проверки
UTF-8/LF, Prettier и `git diff --check` пройдены. Образы и точная конфигурация nginx
зафиксированы в evidence. Полные backend/frontend suites не перезапускались:
продуктовый код изменён только в nginx и проверен реальным HTTP/API/browser путём.

## Запуск и пределы результата

```powershell
& docs/sprint_2/verify-inf-05.ps1
```

Подробности — [runbook](2026-11-01-inf-05-save-size-runbook.md).
Для развёртывания нужно пересобрать production frontend. Внешний HTTPS
proxy/WAF должен иметь совместимую настройку этого пути; он локально не проверялся.
Большой синтетический пример не является нагрузочным нормативом и не обещает
неограниченные ресурсы. Восстановление старых protocol blocks исключено пользователем.

Работа выполнена в текущем checkout без staging/commit/push. Журнал хранится в
Sprint 2 вместо commit-based skill helpers. Agent memory не дублируется:
дизайн, runbook и этот отчёт сохраняют необходимые знания.
