---
title: Реестр Изменений Нод Code_wiki
type: state
status: active
created: 2026-05-30
updated: 2026-06-15
source: docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md
tags: [repository-change, code-wiki, ingest]
---

# Реестр Изменений Нод Code_wiki

Компактный реестр содержательных созданий и обновлений нод `Code_wiki`.
Строка добавляется только когда изменение ноды сохраняет новое устойчивое
техническое знание.

Завершение плана, commit, тестовый прогон и изменение служебных индексов сами
по себе не создают запись. Pre-commit не запускает и не проверяет этот процесс.

## Активный Реестр

| Дата | Нода | Причина | Источник |
| --- | --- | --- | --- |
| 2026-06-13 | [[состояние_проекта/_info]] | Repository-change log заменён компактным реестром с двухусловным gate. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
| 2026-06-13 | [[сборка/ci_and_quality]] | Добавлена read-only проверка жизненного цикла agent memory. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
| 2026-06-13 | [[правила_и_стиль/testing_strategy]] | Зафиксированы тесты и ручной workflow memory audit. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
| 2026-06-15 | [[архитектура/backend]] | Зафиксированы отдельный пакет `seeds` и single-query utility read path. | `apps/backend/app/seeds/`, `apps/backend/app/repositories/utility_network_repository.py` |
| 2026-06-15 | [[архитектура/api_and_realtime]] | Добавлен Editor-only feeder aggregate API и structured utility errors. | `apps/backend/app/api/utility_network.py` |
| 2026-06-15 | [[архитектура/data_model]] | Отражены utility schema, create-once dataset и aggregate spatial query. | `apps/backend/app/models/utility_network/`, `apps/backend/app/seeds/` |
| 2026-06-15 | [[dev_setup/local_development]] | Обновлены module runners demo users и utility dataset. | `apps/backend/app/seeds/runners/` |
| 2026-06-15 | [[deployment/docker_compose]] | Зафиксирован startup order migrations/users/utility/API и no-op restart. | `infra/docker-compose.yml` |
| 2026-06-15 | [[сборка/ci_and_quality]] | Добавлены utility DB tests, reseed после migration cycle и authenticated smoke. | `.github/workflows/ci.yml` |
| 2026-06-15 | [[правила_и_стиль/testing_strategy]] | Добавлено покрытие utility seed, spatial repository, mapping и access API. | `apps/backend/app/tests/test_utility_network_*.py` |
