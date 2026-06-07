---
title: Repository Change Ingest
type: state
status: active
created: 2026-05-30
updated: 2026-06-07
source: "git status/diff, 2026-05-30; 2026-05-31; 2026-06-02; 2026-06-04; 2026-06-05; 2026-06-06; 2026-06-07"
tags: [repository-change, code-wiki, ingest]
---

# Repository Change Ingest

Журнал значимых изменений репозитория, которые агент фиксирует через `/ingest repository-change` после полного завершения реализации плана или крупной задачи.

Pre-commit не запускает и не проверяет этот процесс. Ответственность за запись лежит на агенте.

## Записи

### 2026-06-07 - Ф7 metrics, risks и validation experiments

**Источник:** ответы пользователя на `/discover --phase Ф7`, пять RAW sources по metrics/post problems/manual baseline/risky assumptions/minimal experiments, `git status --short`, `git diff --stat`.

**Кратко:** Ф7 превратила demo-scope и NFR в измерительный контракт. North Star - `Safe Authoritative Post Rate >=95%` на 200 started work orders с 7-дневным correction window. Silent overwrite, пропущенный safety-critical conflict и Critical/High review error имеют абсолютный veto независимо от aggregate. Определены secondary metrics, обязательные P95, manual baseline и порядок минимальных экспериментов.

**Затронутые области:**

- `Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks.md` - решения Ф7 и принятый risk register.
- `Vision_wiki/concepts/metrics.md` - North Star, secondary metrics, guardrails, baseline и evidence.
- `Vision_wiki/decisions/risk_assumption_log.md` - workflow/validation/conflict assumptions и risks статистической валидности/evidence scope.
- `Vision_wiki/solution/nfr.md`, `Vision_wiki/solution/roadmap.md` - обязательные performance gates и последовательность экспериментов.
- `Vision_wiki/decisions/followups/index.md` - 200-work-order evaluation, manual baseline, UX test и 30-run benchmark.
- `RAW_inputs/index.md`, `Vision_wiki/index.md`, `index.md`, `memory/project-state.md`, `docs/agent-memory/` - источники, навигация, live state и долговременная память.

**Что помнить дальше:**

- 95% на 200 work orders означает минимум 190 safe posts, но safety blocker проваливает проверку при любом aggregate.
- Manual baseline снимается отдельно на 10-20 work orders low/medium/high.
- Порядок проверки: workflow acceptance -> validation trap test -> two-editors conflict drill -> baseline -> product evaluation.
- Performance benchmark выполняется 30 повторов; не все latency targets являются blockers.
- Reports в Git и structured audit в PostgreSQL входят в desired evidence; immutable object storage требует отдельного scope-решения.
- Метрики и эксперименты пока являются принятым контрактом проверки, а не реализованной instrumentation или доказанным результатом.

**Проверка:** `scripts/lint-wiki.py --root .` через bundled Python - ожидаемые 11 `missing_frontmatter` для неизменяемых RAW Markdown files, зафиксированные в `FU-2026-06-01-004`; `scripts/check-memory-needed.py --check` - passed; `git diff --check` - passed.

### 2026-06-06 - Ф6 constraints и NFR local demo

**Источник:** ответы пользователя на `/discover --phase Ф6`, подтверждение audit/reset approach, `git status --short`, `git diff --stat`.

**Кратко:** Ф6 зафиксировала эксплуатационные рамки local Docker Compose demo: reference hardware с 16 GB RAM, Chrome, startup/reset за несколько минут, JWT, separation of duties для `Editor`/`Reviewer`, WebSocket delivery за 1-2 секунды и observability minimum. Новые числовые latency targets для map load/save/validation/reconcile/post не вводились.

**Затронутые области:**

- `Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md` - ответы Ф6 и решение по audit/reset.
- `Vision_wiki/solution/nfr.md`, `Vision_wiki/decisions/constraints.md`, `Vision_wiki/solution/architecture_vision.md` - runtime, security, availability, observability и audit requirements.
- `Vision_wiki/solution/roadmap.md` - `import GeoJSON`, reset/`full-clean` и observability перенесены в Now.
- `Vision_wiki/decisions/risk_assumption_log.md` - reference hardware assumption и риск неявной reset semantics.
- `Vision_wiki/decisions/followups/index.md` - уточнен open follow-up local demo support package.
- `index.md`, `Vision_wiki/index.md`, `memory/project-state.md`, `docs/agent-memory/` - навигация, live state и долговременная память.

**Что помнить дальше:**

- Обычный restart сохраняет demo state.
- Обычный reset восстанавливает `synthetic_utility_feeder_01` и сохраняет `audit_log`.
- Отдельный `full-clean` удаляет demo data и audit.
- Audit фиксирует actor/role/action/time/target/context/before-after/result и ключевые события edit -> validate -> reconcile -> review -> post.
- `import GeoJSON` входит в первый walking skeleton.
- Для local demo не требуются SLA, backup/restore и production compliance guarantees.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - ожидаемые 4 `missing_frontmatter` для неизменяемых RAW Markdown files, зафиксированные в `FU-2026-06-01-004`; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - passed.

### 2026-06-05 - Ф5 rollout и актуализация knowledge wiki

**Источник:** ответы пользователя на `/discover --phase Ф5`, `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`, `git status --short`, `git diff --stat`.

**Кратко:** после Ф4 demo-scope обработан source с детальным walking skeleton/dataset и выполнен `/sync-vision`; затем Ф5 зафиксировала rollout GeoService как local Docker Compose demo для разработчика и владельца pet-проекта. Ценность первого rollout - `learning value` и демонстрация, что pipeline сетевой правки стал проще. Главный rollout-риск - непонятный UI conflict review.

**Затронутые области:**

- `Vision_wiki/chats/2026-06-05-utility-gis-editor-walking-skeleton-and-dataset.md` - source summary для desired technical skeleton и `synthetic_utility_feeder_01`.
- `Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md` - ответы Ф5 по rollout, audience, value, integrations и support package.
- `Vision_wiki/decisions/constraints.md` - constraints demo: local Docker Compose, synthetic data, integration boundaries и promise boundaries.
- `Vision_wiki/concepts/lean_canvas.md`, `Vision_wiki/solution/roadmap.md`, `Vision_wiki/decisions/risk_assumption_log.md` - local demo rollout, `learning value`, UI conflict review risk и roadmap для demo support package.
- `Vision_wiki/decisions/followups/index.md` - добавлены `FU-2026-06-05-001` для local demo support package и `FU-2026-06-05-002` для conflict review UX.
- `index.md`, `Vision_wiki/index.md`, `RAW_inputs/index.md`, `memory/project-state.md`, `docs/agent-memory/` - навигация, live state и долговременная память.

**Что помнить дальше:**

- Первый rollout не является коммерческим go-to-market: decision maker - владелец pet-проекта, audience - developer.
- В первый показ приоритетнее `Editor flow`; `Reviewer` нужен как роль, но polish reviewer decision flow может идти Next.
- Нужны `PostGIS seed`, `auth`, README, seed/reset script, demo сценарий и troubleshooting.
- Не обещать замену `ArcGIS Enterprise + Utility Network`, production branch versioning, topology/trace engine, real utility data, hosted/SaaS rollout, enterprise ACL/compliance/audit guarantees, offline sync, external GIS integrations и доказанный commercial ROI.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - ожидаемые `missing_frontmatter` для RAW Markdown files `RAW_inputs/documents/Ф2.md`, `RAW_inputs/documents/03.06.2026deep-research-report.md`, `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md`, `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`; конфликт зафиксирован в `FU-2026-06-01-004`; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - passed.

### 2026-06-04 - `/discover --phase Ф4`: demo-scope для `Utility GIS editor`

**Источник:** ответы пользователя на `/discover --phase Ф4`, `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md`, `git status --short`, `git diff --stat`.

**Кратко:** Ф4 зафиксировала scope GeoService как demo focused conflict/review layer для `Utility GIS editor`. Главный результат - demo; главный сигнал ценности - `review стал проще`; primary scenario - `geometry/association conflict`; `edit after reconcile` перенесен в Next/Later. GeoService показывает собственную optimistic conflict + review model, а не full branch versioning platform.

**Затронутые области:**

- `Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md` - сводка решений Ф4, walking skeleton и synthetic dataset.
- `Vision_wiki/solution/USM.md`, `roadmap.md`, `architecture_vision.md`, `Vision_wiki/concepts/first_release_mvp.md` - demo-scope, walking skeleton, architecture boundary и explicit non-goals.
- `Vision_wiki/concepts/product_vision_board.md`, `lean_canvas.md`, `Vision_wiki/decisions/risk_assumption_log.md` - demo priority, focused conflict/review positioning и mitigated risks.
- `Vision_wiki/decisions/followups/index.md` - закрыты `FU-2026-05-31-002`, `FU-2026-05-31-003`, `FU-2026-06-01-003`; `FU-2026-06-02-001` оставлен open как подготовка synthetic utility dataset.
- `RAW_inputs/index.md`, `Vision_wiki/index.md`, `index.md`, `memory/project-state.md`, `docs/agent-memory/` - навигация, live state и долговременная память.

**Что помнить дальше:**

- В MVP входят conflict explanation и reviewer decision.
- Явно не входят full branch versioning, topology engine, offline sync, CRDT/OT, rich ACL и production utility network model.
- Технологические рамки сохраняются: FastAPI, PostGIS, Vue/MapLibre, WebSocket, `version`/`409`.
- Synthetic dataset Ф4: 1 AOI, 1 feeder, 7 junctions, 6 line segments, 6 devices, 8-10 associations, 2 work orders, 3 users, 2 edit versions + `Default`, 4 conflict-сценария.
- Scope creep сигнал: появление новых незапланированных на релиз фич.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - ожидаемые `missing_frontmatter` для неизменяемых RAW Markdown files `RAW_inputs/documents/Ф2.md`, `RAW_inputs/documents/03.06.2026deep-research-report.md`, `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md`, конфликт зафиксирован в `FU-2026-06-01-004`; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-06-02 - `/discover --phase Ф2`: выбран `Utility GIS editor`

**Источник:** второй проход ответов пользователя на `/discover --phase Ф2`, `RAW_inputs/documents/Ф2.md`, `git status --short`, `git diff --stat`.

**Кратко:** Ф2 завершена на уровне research-гипотез. Primary research-persona GeoService - `Utility GIS editor`; кадастровый сценарий отложен как более сложный для реализации. Детализирован work order workflow замены трансформатора и переподключения линии, где главный риск - неверное состояние сети.

**Затронутые области:**

- `Vision_wiki/entities/personas/utility_gis_editor.md` - отдельная primary persona-нода с workflow, болями, desired outcome и synthetic validation.
- `Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md`, `Vision_wiki/concepts/jtbd.md` - закрытие Ф2 и primary JTBD.
- `Vision_wiki/concepts/product_vision_board.md`, `lean_canvas.md`, `Vision_wiki/decisions/risk_assumption_log.md`, `Vision_wiki/solution/USM.md` - синхронизация utility authoritative editing гипотез без расширения Release 1.
- `Vision_wiki/decisions/followups/index.md`, `Vision_wiki/index.md`, `index.md`, `memory/project-state.md`, `docs/agent-memory/` - закрытый выбор primary scenario, synthetic pilot, навигация и долговременная память.

**Что помнить дальше:**

- Все утверждения о `Utility GIS editor` являются research-гипотезами на основе документации существующих продуктов; реальных заказчиков и пользователей GeoService для интервью пока нет.
- Synthetic pilot должен проверить topology, `attribute vs attribute`, `geometry/association`, `edit after reconcile`.
- Branch versioning, `Conflicts view`, reviewer workflow и topology validation не входят в Release 1 автоматически: это решение относится к Ф4.
- Следующая discovery-фаза - Ф3 для сравнения альтернатив в контексте utility authoritative editing.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - ожидаемый `missing_frontmatter` для неизменяемого `RAW_inputs/documents/Ф2.md`, уже зафиксированный в `FU-2026-06-01-004`; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` и `git diff --cached --check` - без ошибок.

### 2026-06-02 - `/discover --phase Ф2`: authoritative editing persona-кандидаты

**Источник:** ответы пользователя на `/discover --phase Ф2`, `RAW_inputs/documents/Ф2.md`, `git status --short`, `git diff --stat`.

**Кратко:** discovery Ф2 сузил исследование GeoService до двух модельных authoritative editing сценариев: `Utility GIS editor` и кадастровый инженер. Единственный primary scenario еще не выбран; внешняя пользовательская боль остается гипотезой до synthetic pilot или проверки на реальном рабочем контексте.

**Затронутые области:**

- `Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md` - сводка ответов Ф2 и границы подтвержденного знания.
- `Vision_wiki/entities/personas/authoritative_gis_editing_candidates.md`, `Vision_wiki/concepts/jtbd.md` - два persona-кандидата и provisional JTBD.
- `Vision_wiki/concepts/product_vision_board.md`, `lean_canvas.md`, `Vision_wiki/decisions/risk_assumption_log.md`, `Vision_wiki/solution/USM.md` - продуктовые гипотезы authoritative editing без расширения Release 1.
- `Vision_wiki/decisions/followups/index.md`, `Vision_wiki/index.md`, `index.md`, `memory/project-state.md`, `docs/agent-memory/` - очередь вопросов, навигация, live state и долговременная память.

**Что помнить дальше:**

- Нужно выбрать один primary scenario или явно зафиксировать сравнительное исследование двух сценариев.
- Детали пользовательских болей пока взяты из research `RAW_inputs/documents/Ф2.md`, а не из интервью с реальным пользователем.
- Scope Release 1 не расширяется автоматически до branch/workspace mode, reviewer workflow или topology validation: это решение относится к Ф4.
- Пользовательские изменения `.obsidian/` и форматирование Markdown-таблиц не являются частью этого repository-change ingest.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - ожидаемый `missing_frontmatter` для неизменяемого `RAW_inputs/documents/Ф2.md`, уже зафиксированный в `FU-2026-06-01-004`; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-05-31 - `/discover --phase Ф1`: исследовательские цели

**Источник:** ответы пользователя на `/discover --phase Ф1`, `git status --short`, `git diff --stat`.

**Кратко:** зафиксировано, что GeoService является исследовательским pet-проектом для изучения алгоритмов совместного редактирования геометрии и проверки AI-first разработки сложной геоинформационной системы. Внешняя пользовательская боль пока не подтверждена.

**Затронутые области:**

- `Vision_wiki/chats/2026-05-31-phase-f1-why-now.md` - сводка ответов Ф1.
- `Vision_wiki/concepts/about_project.md`, `product_vision_board.md`, `lean_canvas.md` - продуктовый контекст и гипотезы.
- `Vision_wiki/decisions/risk_assumption_log.md`, `followups/index.md` - риски, assumptions и следующие вопросы.
- `Vision_wiki/index.md`, `memory/project-state.md`, `docs/agent-memory/` - индексы, live state и долговременная память.

**Что помнить дальше:**

- Не приписывать GeoService подтвержденную внешнюю пользовательскую боль до Ф2-Ф3.
- Следующая фаза: Ф2 пользователи и боль.
- Критерий первого релиза "все типа работает" нужно заменить на проверяемый demo-script и acceptance criteria.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - `Wiki lint passed.`; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-05-31 - Первичный `/discover` и уточнение Release 1

**Источник:** ответы пользователя на первичную анкету `/discover`, `git status --short`, `git diff --stat`.

**Кратко:** зафиксирован стартовый discovery-контекст GeoService: это pet-проект на стадии идея / прототип, владельцем решений является разработчик Попов Дмитрий. Пользователь подтвердил актуальность `RAW_inputs/documents/спринт 1.odt` и уточнил, что документ описывает план первого релиза, а не спринта.

**Затронутые области:**

- `Vision_wiki/chats/2026-05-31-initial-discover.md`, `Vision_wiki/concepts/about_project.md`, `Vision_wiki/entities/stakeholders/dmitry_popov.md` - базовый discovery-контекст.
- `Vision_wiki/chats/2026-05-30-release-1-document.md`, `Vision_wiki/concepts/first_release_mvp.md`, `Vision_wiki/solution/` - продуктовая терминология Release 1.
- `Code_wiki/архитектура/api_contract_first_release_requirements.md` - desired API contract первого релиза.
- `RAW_inputs/index.md`, `Vision_wiki/index.md`, `Code_wiki/index.md`, `memory/project-state.md`, `docs/agent-memory/` - индексы, live state и долговременная память.

**Что помнить дальше:**

- Имя RAW-файла `RAW_inputs/documents/спринт 1.odt` не меняется: исходные материалы остаются неизменяемыми.
- Следующие discovery-фазы: Ф1 проблема и why-now, Ф2 пользователи и боль, Ф3 альтернативы и контекст использования.
- Точный тип продукта пока не определен и не должен угадываться до прохождения Ф1-Ф3.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - `Wiki lint passed.`; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок; поиск stale renamed-node references в активной wiki - совпадений нет.

### 2026-05-30 - Project knowledge wiki pipeline

**Источник:** `git status --short`, `git diff --stat`, результаты проверок 2026-05-30.

**Кратко:** в репозиторий GeoService перенесена шаблонная структура project knowledge wiki и ручной pipeline `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki` без привязки к donor-проекту `C:\Repositories\ai-po-template-experiments`. Wiki ведётся на русском языке, при этом пути, команды, API, идентификаторы и имена файлов не переводятся.

**Затронутые области:**

- `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/`, `memory/`, `Общие_принципы/` - структура базы знаний, шаблоны и индексы.
- `.agents/skills/source-command-*` - repo-local инструкции для ручных команд `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`.
- `.obsidian/` - конфигурация Obsidian graph для wiki.
- `docs/knowledge-pipeline/README.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md` - правила работы с pipeline.
- `docs/agent-memory/` - память о правилах: планы на русском, обязательная запись важных решений, корректный режим `/discover`, полнота skill-системы, agent-driven `repository-change ingest`.
- `scripts/lint-wiki.py`, `scripts/check-memory-needed.py` и `scripts/tests/` - проверки wiki и обязательности memory updates.

**Важное решение:** `repository-change ingest` не выполняется Python-скриптом, не запускается pre-commit и не проверяется pre-commit hook. После полного завершения реализации плана или крупной задачи агент должен сам вызвать `/ingest repository-change` через skill `source-command-ingest` перед финальным отчётом пользователю. Не вызывать после каждого мелкого шага.

**Удалено как устаревшее:** `scripts/repository_change_ingest.py`, `scripts/prepare_commit.cmd`, `scripts/tests/test_repository_change_ingest.py`, local pre-commit hook `repository-change-ingest-guard`.

**Риски и что помнить дальше:**

- В старом файле плана `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md` остались исторические шаги про Python/pre-commit, но в начале файла добавлена актуализация, которая их supersede'ит.
- Donor-репозиторий `C:\Repositories\ai-po-template-experiments` остаётся только read-only reference; туда нельзя вносить правки и нельзя переносить project-specific факты.
- После `/ingest` old documentation можно исправлять только по конфликтам, которые уже есть в `Vision_wiki/decisions/followups/index.md`, связаны с `Code_wiki` и разрешимы из новых знаний. Код, конфигурация, миграции и тесты требуют отдельной implementation task.

**Проверка:** `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts\lint-wiki.py --root .` - `Wiki lint passed.`; `python scripts\check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-05-30 - Аудит полноты source-command skills

**Источник:** повторная сверка `.agents/skills/source-command-*` с `C:\Repositories\ai-po-template-experiments`, проверка supporting-файлов и актуальных инструкций 2026-05-30.

**Кратко:** в GeoService присутствуют все четыре repo-local skills из reference-подхода: `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`. Для них созданы нужные wiki-директории, шаблоны, solution-артефакты, методические файлы, Obsidian config, linter и memory-check. Проверено, что skills не ссылаются на отсутствующие helper-файлы.

**Что важно помнить:**

- Reference-репозиторий содержит `scripts/ingest-raw.sh`, `.claude/commands/` и `.claude/agents/`, но текущие Codex skills на них не ссылаются. Это Claude Code-specific окружение, а не обязательная зависимость для `.agents/skills`.
- Изменения в самом репозитории попадают в базу знаний через agent-driven `/ingest repository-change` после полного завершения плана или крупной задачи. Это не git hook и не фоновый daemon: если изменения сделаны человеком без агента, нужно вручную попросить агента выполнить `/ingest repository-change` или запустить соответствующий workflow.
- Единственный исправленный найденный недочет: `docs/agent-memory/file-map.md` больше не называет `.pre-commit-config.yaml` частью wiki automation, потому что repository-change ingest отвязан от pre-commit.

### 2026-05-30 - Добавлен `/ingest repository-snapshot`

**Источник:** запрос пользователя о том, как добавлять в базу знаний уже существующие неизмененные данные репозитория.

**Кратко:** добавлен режим `/ingest repository-snapshot` для первичной или периодической инвентаризации текущего состояния репозитория. Он дополняет `/ingest repository-change`: snapshot работает с уже существующей кодовой базой, change работает с завершенными изменениями через `git status`/`git diff`.

**Затронутые области:**

- `.agents/skills/source-command-ingest/SKILL.md` - добавлен алгоритм `repository-snapshot`.
- `docs/knowledge-pipeline/README.md`, `AGENTS.md`, `README.md` - описано, когда вызывать snapshot.
- `Code_wiki/состояние_проекта/repository_snapshot.md` - создан журнал snapshot'ов.
- `Code_wiki/index.md`, `Code_wiki/состояние_проекта/_info.md` - добавлены ссылки на журналы snapshot/change.
- `memory/project-state.md` и `docs/agent-memory/file-map.md` - обновлены навигационные и state-записи.
- `docs/agent-memory/decisions/2026-05-30-repository-snapshot-ingest.md` - сохранено durable решение.

**Что помнить дальше:** `/ingest repository-snapshot` не индексирует весь код дословно и не меняет код/конфигурацию/миграции/тесты. Он создает технические wiki-ноды о текущей архитектуре, dev setup, сборке, deployment, API, моделях, тестах, правилах и рисках.

**Проверка:** `python scripts/lint-wiki.py --root .` - passed; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-05-30 - Batch-режим `/ingest` без параметров для RAW_inputs

**Источник:** запрос пользователя: `/ingest` без параметров должен обрабатывать все новые `RAW_inputs` по очереди, если их немного; если файлов много или есть неоднозначность, нужно показать список и попросить подтверждение.

**Кратко:** обновлено поведение `/ingest` без параметров. Теперь агент ищет новые или измененные RAW-файлы, которых еще нет в обработанных source-записях wiki/state. Если найдено 1-5 однозначных кандидатов, они обрабатываются по очереди в одном запуске `/ingest`. Если кандидатов больше 5 или есть неоднозначность, агент сначала показывает список и просит подтверждение.

**Затронутые области:**

- `.agents/skills/source-command-ingest/SKILL.md` - уточнен шаг определения объекта ingest.
- `docs/knowledge-pipeline/README.md` - добавлен раздел `/ingest` без параметров.
- `AGENTS.md` - добавлена краткая инструкция для будущих агентов.
- `docs/agent-memory/file-map.md` - добавлена навигационная запись для batch RAW ingest.
- `docs/agent-memory/decisions/2026-05-30-raw-inputs-batch-ingest.md` - сохранено durable решение.

**Что помнить дальше:** если новых RAW-кандидатов нет, `/ingest` без параметров ничего не меняет и сообщает, что ingest не выполнен. Он может предложить явный путь, `/ingest repository-snapshot` или `/ingest repository-change`, но не должен создавать пустые wiki-правки.

**Проверка:** `python scripts/lint-wiki.py --root .` - passed; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.
