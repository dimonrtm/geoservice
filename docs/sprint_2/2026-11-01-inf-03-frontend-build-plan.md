# INF-03 — план реализации изоляции frontend Docker build

> **Для агента-исполнителя:** обязательный навык — superpowers:executing-plans при исполнении в этом чате либо superpowers:subagent-driven-development при выбранной пользователем делегации. Выполнять задачи последовательно, отмечая шаги чекбоксами. Не выполнять git add, git commit или git push: запрет AGENTS.md приоритетнее инструкций навыков.

**Цель:** исключить влияние локальных зависимостей, env и артефактов на frontend Docker dev/prod и проверять это в CI.

**Архитектура:** apps/frontend/.dockerignore ограничивает существующий COPY без изменения Dockerfile. Node runner создаёт синтетически загрязнённый context, проверяет общий слой через dev target, готовую prod-статику и явно заданные runtime-настройки dev. Отдельный CI job запускает тот же runner.

**Стек:** Node.js 20, стандартная библиотека Node, Docker/Buildx, существующие Vue/Vite/npm, GitHub Actions.

**Спецификация:** [принятый дизайн](2026-11-01-inf-03-frontend-build-design.md), принят пользователем сообщением «Принимаю».

## Общие ограничения

- Артефакты задачи сохраняются в docs/sprint_2/, русский текст, UTF-8 с LF.
- Не читать/копировать реальные env в fixtures и evidence; не удалять пользовательские файлы.
- Существующие Dockerfile, API resolver, nginx, Compose и зависимости сохраняют поведение.
- Локальный npm run dev продолжает читать env; Docker dev использует явный environment; production — существующий same-origin путь.
- Не фиксировать image digest и не требовать побайтовой идентичности между сборками.
- Не публиковать образы, не менять branch protection, не выполнять Docker prune.
- Нельзя подтверждать исправление только наличием ignore-файла, чистой временной сборкой или чистым итоговым dist.
- Не объявлять локальный прогон GitHub Actions успешно выполненным CI: результаты различать.

## Файлы и ответственность

| Файл | Действие и назначение |
| --- | --- |
| apps/frontend/.dockerignore | Создать: исключения context для всех targets |
| docs/sprint_2/inf-03/run.mjs | Создать: CLI, Docker lifecycle, проверки и evidence |
| docs/sprint_2/inf-03/fixtures.mjs | Создать: безопасная копия актуальных исходников и искусственные загрязнения |
| docs/sprint_2/inf-03/fixtures.test.mjs | Создать: проверки сохранения исходников, env/symlink изоляции и fixtures |
| .github/workflows/ci.yml | Добавить frontend_docker_isolation |
| apps/frontend/README.md | Уточнить локальные и Docker env |
| docs/sprint_2/2026-11-01-inf-03-frontend-build-runbook.md | Создать: команды и трактовка результатов |
| docs/sprint_2/2026-11-01-inf-03-frontend-build-implementation-report.md | Создать после проверок: результаты и ограничения |
| docs/sprint_2/evidence/inf-03/ | Компактные доказательства приёмки, без копий bundles/env |
| docs/sprint_2/README.md, infra-performance-review.md, 2026-10-26-deep-code-review.md | Обновить ссылки и статус по фактическим результатам |

## Фокус проверки

1. Предварительная очистка может скрыть дефект: после создания fixtures подтвердить их наличие, затем не фильтровать context; контроль без ignore должен обнаружить маркеры.
2. Vite удаляет dist и не встраивает unused env: проверять общий /app до Vite build, а не только итоговую статику.
3. Вложенные env/dependencies и symlink на внешнюю папку: вложенные fixtures исключаются Docker, подготовка не читает внешние symlink-цели.
4. Локальные незакоммиченные исходники и ресурсы public: копировать текущее дерево, не только HEAD; проверить сохранение контрольного исходника и public-ресурса.
5. Ошибка/таймаут запуска и занятые порты: динамический loopback port, ограниченное ожидание, ненулевой exit и cleanup только собственных ресурсов.

---

## Задача 1: доказательство дефекта и правила context

**Файлы:** fixtures.mjs, fixtures.test.mjs, run.mjs и apps/frontend/.dockerignore из таблицы выше.

**Интерфейсы:**

- fixtures.mjs: prepareContext(sourceDir, targetDir, { contaminated, omitIgnore }) -> Promise<{ fixturePaths: string[], forbiddenUrl: string | null }>. Пути абсолютные на входе, fixturePaths относительные к context. Создаёт только новый targetDir. omitIgnore применяется исключительно к временной копии.
- fixtures.mjs: assertFixturesPresent(contextDir, fixturePaths) -> Promise<void>; отсутствие ожидаемого файла — ошибка.
- run.mjs: CLI node docs/sprint_2/inf-03/run.mjs [--acceptance] [--evidence-dir PATH]. По умолчанию запускает загрязнённый сценарий; --acceptance добавляет чистый, отрицательный и прямой workspace build. Успех — exit 0 и status=passed в summary.json; любая ошибка — ненулевой exit и status=failed. Неизвестные аргументы отклоняются.

- [x] Написать Node tests на временных fixtures: сохраняется изменённый src-файл и public-файл; реальные .env.local и node_modules не копируются; symlink наружу отклоняется без чтения цели (на Windows использовать доступный directory junction); искусственные корневые и вложенные маркеры действительно созданы; отсутствие fixture вызывает ошибку. Запустить node --test docs/sprint_2/inf-03/fixtures.test.mjs и получить ожидаемый FAIL отсутствующего модуля.
- [x] Реализовать prepareContext и assertFixturesPresent стандартной библиотекой. До чтения проверять тип записи через lstat, не следовать symlinks/junctions. Не переносить локальные env, dependencies, dist и служебные артефакты; не использовать .dockerignore как алгоритм подготовки. Скопировать .dockerignore и Dockerfile-specific ignore, если он появился, кроме явно отрицательного сценария. Запустить те же tests до PASS.
- [x] Создать fixtures: node_modules/inf03-marker.txt, nested/node_modules/inf03-marker.txt; .env, .env.local, .env.production, .env.production.local, .env.example, nested/.env.local; dist/inf03-stale.txt, dist-ssr/inf03-stale.txt, coverage/inf03-marker.txt, .vite/inf03-marker.txt, .vscode/inf03-marker.txt, inf03.tsbuildinfo и inf03.log. Для env использовать один известный URL https://inf03-build.invalid, не реальные значения.
- [x] Реализовать первую часть run.mjs: определить repo относительно import.meta.url; проверить Docker daemon; создать уникальные временные пути и теги; подготовить загрязнённый context; подтвердить fixtures; собрать dev через docker buildx build --load --target dev; проверить каждый fixturePath на отсутствие в /app и наличие /app/node_modules/vite/package.json, /app/src, package manifests и конфигурации. До исправления проверка должна падать именно на найденных загрязнениях. Ошибка сети/npm не считается доказательством INF-03.
- [x] Добавить .dockerignore с корневыми и рекурсивными правилами для node_modules, .env/.env.*, dist/dist-ssr, coverage, .vite/.vite-temp/.cache, *.tsbuildinfo, *.log, .git, .idea, .vscode, .DS_Store, Thumbs.db. Не исключать src/public/manifests/nginx/config. Повторить проверку общего слоя: fixtures отсутствуют, зависимости присутствуют.

## Задача 2: production, dev runtime и локальная приёмка

**Файл:** docs/sprint_2/inf-03/run.mjs.

**Интерфейс:** расширяет CLI задачи 1, используя prepareContext и fixturePaths без повторной фильтрации; summary.json содержит status, режим, версии Node/Docker, результаты именованных проверок и ошибки cleanup. Evidence не содержит содержимого пользовательских файлов.

- [x] Добавить сборку prod из того же загрязнённого context. Через docker create/cp извлечь /usr/share/nginx/html без запуска nginx; проверить index.html, непустой assets, отсутствие inf03-stale.txt и строки https://inf03-build.invalid во всех текстовых assets. Не запускать nginx без backend DNS и не добавлять backend ради чтения статики.
- [x] Добавить dev runtime smoke: запустить свой dev-контейнер с -e VITE_API_BASE_URL=https://inf03-runtime.invalid и динамическим портом на 127.0.0.1; опросить / до HTTP 200, затем /src/api/baseUrl.ts и проверить Vite-transformed модуль на явно переданное значение. Проверка env через docker inspect сама по себе недостаточна. Backend и доступ к домену .invalid не нужны.
- [x] Ограничить Docker build 10 минутами, команды инспекции 2 минутами, readiness 60 секундами с короткими интервалами. Docker вызывать spawn с shell:false и windowsHide:true. Обработать error/timeout/nonzero, завершать дочерний процесс и выполнять finally cleanup. До удаления временного каталога проверять его абсолютный путь и принадлежность собственному mkdtemp; контейнеры/теги удалять по сохранённым идентификаторам. Ошибки cleanup отражать в evidence и exit status.
- [x] Реализовать --acceptance: сначала пройти обычный загрязнённый сценарий; отдельно проверить чистый context теми же положительными утверждениями без fixtures; затем в новой временной копии удалить только ignore-файлы и убедиться, что проверка общего слоя находит конкретные маркеры. Не считать произвольное падение build успешным отрицательным тестом. Ошибка отсутствия ожидаемой регрессии завершает весь runner неуспехом.
- [x] В --acceptance после синтетических проверок выполнить обычные dev/prod build непосредственно из apps/frontend, без копирования/очистки workspace, с уникальными тегами. До этого убедиться в наличии ожидаемого .dockerignore и отсутствии перекрывающего Dockerfile-specific ignore; при несоответствии остановиться до передачи реального context. Не выводить значения env или содержимое реальных локальных файлов. Проверить результаты теми же smoke/assertions, где применимо.
- [x] Запустить node docs/sprint_2/inf-03/run.mjs --acceptance. Ожидание: exit 0; dirty/clean/workspace успешны, negative-control обнаружил загрязнения. Проверить отсутствие собственных контейнеров/тегов и временных context после завершения.
- [x] Проверить неуспешный путь на изолированной fixture-копии с преднамеренно неверной командой Dockerfile: ненулевой exit, status=failed, cleanup выполнен. Не менять рабочий Dockerfile. Убедиться, что исходники и соседний контрольный каталог не удалены. Если таймаут проверяется отдельным коротким smoke, использовать только собственный disposable container.

## Задача 3: CI, документация и итоговая проверка

**Файлы:** .github/workflows/ci.yml, apps/frontend/README.md, runbook, report и sprint индексы из таблицы.

**Интерфейс:** CI использует CLI задачи 1 без --acceptance; локальная приёмка использует --acceptance. Evidence directory задаётся явно в RUNNER_TEMP для CI; локально — docs/sprint_2/evidence/inf-03/<уникальный-id>.

- [x] Добавить frontend_docker_isolation на ubuntu-latest с timeout-minutes: 30, checkout, setup-node@v4 node-version: 20, setup-buildx-action@v3. Запустить Node fixture tests, затем node docs/sprint_2/inf-03/run.mjs --evidence-dir <путь-в-RUNNER_TEMP>. Не устанавливать frontend dependencies на host этого job и не заменять существующие npm jobs.
- [x] Добавить upload-artifact@v4 с if: always(), retention-days: 7 и только каталогом evidence runner. Не включать continue-on-error для сборки/проверок. Проверить workflow доступным YAML-инструментом и прочитать итоговый diff; не устанавливать новый пакет ради единственной синтаксической проверки. Если полноценный CI run не выполнен, прямо записать это в отчёт.
- [x] Написать runbook с обеими CLI-командами, prerequisites Docker Linux daemon/Node 20, временем ожидания, доказательствами и ограничением branch protection. Объяснить, что проверки не выводят пользовательские env, не публикуют образы и не требуют работающего Compose-стенда.
- [x] Обновить frontend README: Docker исключает env, dev получает API URL из Compose environment, production использует origin сайта, локальный npm run dev сохраняет .env.local. Никаких новых production build args.
- [x] Из apps/frontend выполнить npm run format:check, npm run lint, npm run typecheck, npm test, npm run build. Результаты сохранять кратко; несвязанные исходные ошибки не исправлять молча. Запустить node --test docs/sprint_2/inf-03/fixtures.test.mjs и обычный runner после окончательных изменений, если они затрагивали его поведение.
- [x] Проверить git diff --check, окончания строк новых файлов отдельным byte-check и git status --short. Не изменять посторонние файлы пользователя; ранее были замечены изменения state-файлов visual companion FE-02, их актуальное состояние определить перед исполнением.
- [x] Записать implementation report: реальные прогоны dirty/clean/negative/workspace, frontend suites, версии и ограничения. Обновить статус INF-03 в review и README только при выполненной приёмке; добавить ссылки на дизайн, план, report/runbook. Не закрывать INF-04. Оставить все изменения unstaged для пользователя.

## Самопроверка плана

Каждый пункт дизайна покрыт задачами: правила и безопасные fixtures — задача 1; общий слой, prod, явный dev env, clean/dirty и чувствительность — задачи 1–2; CI, документация и обычные проверки — задача 3. Пять рисков из фокуса проверки включены в соответствующие шаги. Дополнительных production изменений и новых зависимостей нет. План выполнен. Результаты и отклонения см. в [отчёте](2026-11-01-inf-03-frontend-build-implementation-report.md) и ledger. Дополнительно добавлены run.test.mjs и failure.integration.test.mjs; Node unit tests также выполнены на Linux Node 20.
