---
name: source-command-discover
description: Ручная процедура /discover для первичной инициализации project knowledge wiki или подготовки discovery-встречи по фазам Ф0-Ф8.
---

# /discover

## Текущая Нормативная Процедура

Этот раздел является приоритетным для текущего `/discover`. Более старые разделы ниже применяются только там, где они не противоречат model-driven discovery.

Перед выбором вопросов прочитать `Wiki/index.md`, `Wiki/_registry/*.md`, `DDD_Wiki/index.md`, `DDD_Wiki/model_health.md`, `Code_wiki/index.md`, релевантные `Code_wiki/архитектура/*.md`, `memory/project-state.md` и playbook'и из `Общие_принципы/`. Затем обязательно проверить фактический текущий код через `rg --files` и `rg`: реализованные endpoints, services/use cases, domain/infrastructure models, migrations, frontend stores/components/API clients/contracts и tests/smoke вокруг выбранного контекста. `Code_wiki` полезен как карта, но не заменяет проверку кода.

Если проект не пустой, `/discover` не задает общий список вопросов. Он сначала исследует текущую доменную модель, DDD-покрытие, конфликты, gaps в `DDD_Wiki/model_health.md`, открытые вопросы в `Wiki/_registry/questions.md`, противоречия в `Wiki/conflicts/`, технические ограничения из `Code_wiki/` и фактическое состояние кода: что уже реализовано, какие статусы/таблицы/API реально существуют, какие planned concepts еще отсутствуют в коде, какие tests/smoke уже закрепляют behavior.

`Vision_wiki/` является legacy/source knowledge. Обращаться к нему только в крайнем случае: когда актуальные `Wiki/`, `DDD_Wiki/`, `Code_wiki/`, `memory/project-state.md` и текущий код не дают ответа, когда нужно проверить происхождение старого решения, или когда есть явный конфликт с legacy-источником. Не использовать `Vision_wiki/` как равноправную основу для новых DDD-вопросов и не позволять legacy-формулировкам перебивать актуальную модель и код.

## Обязательный Code Reality Check

Перед генерацией 150 candidate questions:

1. Найти через `rg --files` и `rg -n` текущую реализацию по терминам контекста.
2. Прочитать реализованные backend routes, use-case services, repositories/models/migrations, frontend stores/components/API clients/contracts и tests/smoke вокруг scope.
3. Разделить найденное на `implemented`, `partially implemented`, `planned only`, `legacy/reference`.
4. Формулировать вопросы от ближайшего кодового шага, а не от идеальной DDD-модели.
5. Для каждого top-вопроса указать code anchor: файл, API, model/service, frontend component/store или test, который делает вопрос актуальным. Если code anchor отсутствует, явно отметить вопрос как planned gap without code yet.
6. Штрафовать при выборе top 15 вопросы, которые требуют перескочить через несколько еще не реализованных слоев без понятного incremental path.
7. Для sprint planning выбирать вопросы так, чтобы ответы помогали спланировать ближайшие 14 дней от текущего кода, а не строили оторванный от реализации backlog.

Затем внутренне сгенерировать 150 candidate questions. Кандидаты должны покрывать: ubiquitous language, subdomains, bounded contexts, context map, entities, value objects, aggregates, commands, domain events, system events, policies, specifications, external systems, integration patterns, invariants, lifecycle/state machines, data model gaps, implemented endpoints/services/models/frontend/tests, code/model mismatches, conflicts, incremental path from current code and sprint planning relevance.

Из 150 кандидатов выбрать top 15 по критериям: насколько ответ разблокирует непротиворечивую модель, снижает риск неверного bounded context/aggregate, помогает разрешить конфликт, повышает confidence низкоуверенного узла, привязан к текущему коду, минимизирует drift между DDD и реализацией, влияет на ближайшие 14 дней разработки, имеет понятного адресата и может быть отвечен пользователем.

В ответе показать только top 15, сгруппированные по смыслу. Для каждого вопроса указать коротко: какой узел или конфликт он уточняет, code anchor или planned gap, почему сейчас важен, и как пользователь может ответить. Не показывать все 150, если пользователь явно не попросил.

Пользователь может ответить прямо в чате или положить ответ новым файлом в `RAW_inputs/`. Если ответ появился как raw-файл, следующий `/ingest` должен обработать его как новый источник. Если ответ дан в чате и пользователь просит сохранить результат, создать trace-summary или обновить wiki только с явным source на этот chat/discovery result.

Для `--phase` и `--context` сначала применить фильтр фазы/контекста, но всё равно строить вопросы из текущей модели, конфликтов и Code Reality Check. Обычный размер выдачи остается 10-15 вопросов, целевой размер для model-driven discovery - top 15.

`/discover` запускает discovery-режим со стейкхолдером. Он не должен просто выдавать общий список вопросов: сначала нужно понять, это первый запуск wiki или подготовка к конкретной встрече.

## Обязательный Контекст

Перед ответом прочитать:

- `memory/project-state.md` - текущее состояние проекта.
- `Wiki/index.md` и `Wiki/_registry/*.md` - актуальные domain nodes, questions, conflicts и registries.
- `DDD_Wiki/index.md` и `DDD_Wiki/model_health.md` - актуальная DDD-модель, gaps и model health.
- `Code_wiki/index.md` и релевантные `Code_wiki/архитектура/*.md` - карта технических знаний.
- Текущий код через `rg --files` и `rg -n` - фактические endpoints, services, models, migrations, frontend contracts/stores/components и tests/smoke.
- `Vision_wiki/index.md` - только как legacy/source fallback в крайнем случае, если актуальные wiki/code-источники не отвечают на вопрос или нужно проверить происхождение старого решения.
- `Vision_wiki/solution/_info.md` - только при первичном запуске или legacy-проверке solution-артефактов.
- `Общие_принципы/Вопросы стейкхолдеру.md` - playbook вопросов.
- `Общие_принципы/Фреймворк работы со стейкхолдером.md` - протоколы поведения на встрече.
- `Общие_принципы/Фазы наполнения wiki.md` - фазы наполнения wiki.

## Первый Запуск

Если в `memory/project-state.md` указано, что `/discover` еще не запускался, или в `Vision_wiki/solution/` нет стартовых solution-артефактов, это первичный запуск.

На первичном запуске нужно:

1. Коротко объяснить, что сейчас собирается базовый контекст проекта.
2. Задать базовую анкету из 5-7 вопросов, не больше.
3. Создать недостающие пустые стартовые solution-артефакты:
   - `Vision_wiki/solution/USM.md`
   - `Vision_wiki/solution/roadmap.md`
   - `Vision_wiki/solution/nfr.md`
   - `Vision_wiki/solution/architecture_vision.md`
4. Убедиться, что существует `Общие_принципы/Фазы наполнения wiki.md`.
5. Не заполнять продуктовые факты без ответов пользователя.
6. После ответов пользователя предложить следующие 3 шага и только затем обновлять wiki-ноды.

### Базовая Анкета

1. Как коротко называется проект и как его лучше именовать в wiki?
2. Какой тип продукта ближе всего: B2B-SaaS, internal tool, marketplace, public service, data platform, AI-agent, другое?
3. На какой стадии продукт сейчас: идея, прототип, MVP, production, scale?
4. Кто ключевой стейкхолдер: роль, имя, зона решений?
5. Какие RAW-материалы уже есть или скоро появятся: документы, встречи, код, схемы, заметки?
6. Какой результат discovery нужен первым: Product Vision Board, Lean Canvas, User Story Map, roadmap, NFR, техническое задание, другое?
7. Сколько времени и сколько встреч реально выделено на discovery?

## Запуск С `--phase`

Если пользователь указал `--phase Ф0` ... `--phase Ф8`, выбрать вопросы только из этой фазы в `Общие_принципы/Вопросы стейкхолдеру.md`.

В ответе обязательно показать:

- цель фазы;
- 10-15 вопросов;
- какие wiki-ноды будут заполнены ответами;
- чек-лист встречи;
- какие follow-up'ы фиксировать после встречи.

## Запуск С `--context`

Если пользователь указал контекст встречи, уточнить:

- с кем встреча: роль и имя;
- сколько минут доступно;
- какое решение или знание нужно получить;
- какие материалы уже есть в `RAW_inputs/`.

Затем выбрать 10-15 релевантных вопросов из фаз, связанных с контекстом. `must`-вопросы задавать первыми, `should` - если есть время, `nice` - только в конце.

## Если Аргументов Нет И Проект Уже Не Пустой

Не угадывать цель. Спросить пользователя, что нужно:

- подготовиться к новой встрече;
- пройти конкретную фазу discovery;
- проверить полноту wiki;
- подготовить follow-up'ы по старым конфликтам;
- другое.

## Что Записать После Discovery

Если пользователь явно просит зафиксировать результат, обновить:

- `RAW_inputs/meetings/` или `RAW_inputs/discovery/` - новый source material для последующего `/ingest`, если нужно сохранить ответы или transcript.
- `Wiki/_registry/questions.md`, `Wiki/conflicts/`, `DDD_Wiki/model_health.md` - только если пользователь просит сразу зафиксировать discovery result и есть явный source на этот результат.
- `memory/project-state.md` - последний `/discover`.
- `Vision_wiki/chats/YYYY-MM-DD-<topic>-checklist.md` и `Vision_wiki/decisions/followups/index.md` - только как legacy/source trace в крайнем случае, не как canonical place для новой DDD-модели.
- solution/concepts/entities ноды только на основе ответов или источников; актуальные domain/model updates сначала писать в `Wiki/` и `DDD_Wiki/`, а не в legacy `Vision_wiki/`.

## Ограничения

- Не задавать больше 7 вопросов в первичной анкете.
- Не превращать первый запуск в полный проход всех Ф0-Ф8.
- Не давать продуктовые советы до закрытия базовых фаз Ф1-Ф3.
- Не копировать факты из donor-репозитория.
- Не строить discovery-вопросы только от DDD/wiki: если вопрос влияет на план спринта, он должен учитывать текущий код и ближайший incremental path от него.
- Не использовать legacy `Vision_wiki/` как основной источник для новых вопросов, если актуальные `Wiki/`, `DDD_Wiki/`, `Code_wiki/` и текущий код уже дают достаточный контекст.
- Wiki-контент вести на русском языке; пути, команды, API и имена файлов не переводить.
