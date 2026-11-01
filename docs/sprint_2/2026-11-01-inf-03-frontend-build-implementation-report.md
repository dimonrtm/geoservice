# INF-03: отчёт о реализации

Дата: 2026-11-01. Статус: исправлена в согласованных границах; изменения оставлены unstaged.

## Результат

Добавлен apps/frontend/.dockerignore для общих dev/prod targets. Он исключает host node_modules, все .env/.env.*, dist/dist-ssr, кэши, coverage, логи и метаданные редакторов/ОС. Dockerfile, зависимости, API resolver, nginx и Compose не изменялись. Локальный Vite сохраняет env-файлы; dev-контейнер использует явный environment.

В CI добавлен frontend_docker_isolation: тесты подготовки context/процессов и реальная dev/prod-сборка с искусственными загрязнениями. Runner проверяет общий слой до Vite, готовую статику и явный API URL dev. Отдельный --acceptance проверяет clean/dirty/negative/workspace. Ошибки и cleanup не маскируются успешным skip.

## Проверки

| Проверка | Фактический результат |
| --- | --- |
| До исправления | 15 искусственных файлов обнаружены в общем слое; runner завершился ошибкой по целевой причине |
| После .dockerignore | Те же 15 файлов отсутствуют; dev/prod собираются; production assets и dev runtime проходят |
| Расширенная приёмка | Dirty, clean и реальный Windows workspace проходят; без ignore обнаружены все 15 маркеров |
| Ошибка build в временной копии | exit 37 приводит к failed, Node integration test проходит, cleanupErrors пуст; соседние файлы сохранены |
| Node unit tests | 7/7 на Windows Node 24.12.0 и Linux Node 20 Alpine |
| Frontend | 53 test files, 467 tests; format/lint/typecheck/build проходят |
| Workflow | YAML разобран установленным js-yaml; job имеет timeout 30 минут и не использует continue-on-error |
| Финальный Docker smoke | После исправления timeout runner passed, cleanupErrors пуст |
| Wiki lint | Только 37 прежних missing_frontmatter в неизменённых RAW Markdown; новых замечаний нет |

Docker Server 28.1.1, Buildx v0.23.0-desktop.1. Обычная frontend-сборка сообщает о большом chunk более 500 kB; это не ошибка INF-03. Настоящий GitHub Actions run в этой сессии не запускался: проверены локальный runner, Linux/Node 20 unit tests и конфигурация workflow.

## Evidence

- [Целевое падение до исправления](evidence/inf-03/before-fix/summary.json).
- [Положительная проверка](evidence/inf-03/after-fix/summary.json).
- [Приёмка clean/dirty/negative/workspace](evidence/inf-03/acceptance/summary.json).
- [Ожидаемая ошибка build и успешный cleanup](evidence/inf-03/failure-path/summary.json).
- [Финальный smoke после правки timeout](evidence/inf-03/final/summary.json).

## Независимое ревью

Независимый reviewer прочитал изменения, дизайн и evidence. Единственное важное замечание: SIGKILL родителя на Linux оставлял потомка с stdout, поэтому таймаут мог ждать завершения Buildx. Новый тест воспроизвёл 4074 мс при лимите 500 мс. Исправлено завершением собственной process group на POSIX и taskkill /T по собственному PID на Windows; тест прошёл примерно за 505 и 674 мс соответственно. Остальные 7 тестов также прошли. Повторное ревью не проводилось; исправление проверено тестами. Других Critical/Important/Minor замечаний нет.

## Принятые технические решения и ограничения

- Работа выполнена в текущем checkout first-edit-save; существующие изменения FE-02 не затронуты. Ledger сохранён в docs/sprint_2 по требованию пользователя. Git staging/commit/push не выполнялись.
- Добавлены отдельные тесты процессов и failure cleanup сверх исходного перечня файлов плана; это сохраняет воспроизводимые проверки ошибок без новых зависимостей.
- Исключается также .env.example: он не является входом Docker-сборки. Новые типы локальных артефактов потребуют дополнять список исключений и fixtures.
- Проверка не доказывает побайтовую идентичность образов в разные дни, отсутствие любых секретов в произвольных исходниках или безопасность remote cache exports.
- Принудительное завершение самого runner средствами ОС может не дать выполнить finally; runbook описывает адресную проверку оставшихся ресурсов.
- Merge-blocking зависит от required status check в GitHub branch protection; настройки не изменялись. INF-04 остаётся открытой.

## Знания проекта

Repository-change ingest обновил Code_wiki о Docker isolation CI. Конфликт прежнего описания INF-03 зарегистрирован как FU-2026-11-01-001 и затем разрешён отдельной post-ingest correction Docker runbook. Новая agent memory не нужна: устойчивое объяснение уже сохранено в коде, runbook и Code_wiki.

[Дизайн](2026-11-01-inf-03-frontend-build-design.md), [выполненный план](2026-11-01-inf-03-frontend-build-plan.md), [runbook](2026-11-01-inf-03-frontend-build-runbook.md), [ledger](2026-11-01-inf-03-execution-ledger.md).
