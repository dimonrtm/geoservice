# Domain Knowledge Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Создать канонический доменный слой `Wiki/` + `DDD_Wiki/`, обновить `/ingest`, `/discover`, добавить planning skill для 14-дневных спринтов и выполнить первичный initialization-проход модели.

**Architecture:** Новый слой остается Markdown-first: атомарные доменные ноды лежат в `Wiki/`, производная DDD-модель лежит в `DDD_Wiki/`, а compact registries дают агентам быстрый вход. `Vision_wiki` становится legacy/source layer для доменных знаний, `Code_wiki` продолжает обновляться только через `/ingest repository-change`. Проверки доменной консистентности добавляются поверх существующего `scripts/lint-wiki.py` без внешних зависимостей.

**Tech Stack:** Markdown, YAML frontmatter, Obsidian wikilinks, Python standard library `unittest`, repo-local skills in `.agents/skills`.

---

## Repository Rules For This Plan

- Do not run `git add` or `git commit` unless the user explicitly asks after reviewing the changes.
- Use `apply_patch` for manual file edits.
- Keep human-readable wiki content, implementation plans, runbooks, follow-ups and state files in Russian.
- Do not edit `RAW_inputs/` files as part of implementation; read them only during initialization.
- Do not edit `C:\Repositories\ai-po-template-experiments`.
- Treat `/ingest` as raw-source processing only. Do not add a separate
  bootstrap-like `/ingest` mode.

## File Structure

Create:

- `Wiki/index.md` - entry point for canonical domain knowledge.
- `Wiki/_templates/*.md` - reusable templates for domain node types.
- `Wiki/_registry/*.md` - compact registries for glossary, entities, value objects, actors, external systems, commands, domain events, system events, policies, specifications, conflicts and questions.
- `Wiki/<type>/_info.md` - directory descriptions for every domain node folder.
- `DDD_Wiki/index.md` - entry point for derived DDD model.
- `DDD_Wiki/model_health.md` - model completeness, conflicts, gaps and next actions.
- `DDD_Wiki/<type>/_info.md` - directory descriptions for every DDD projection folder.
- `.agents/skills/source-command-plan-sprint/SKILL.md` - manual sprint planning procedure.

Modify:

- `scripts/lint-wiki.py` - include `Wiki/` and `DDD_Wiki/`; add domain consistency checks.
- `scripts/tests/test_lint_wiki.py` - add failing tests before implementation.
- `.agents/skills/source-command-ingest/SKILL.md` - raw-source domain extraction and DDD projection rules.
- `.agents/skills/source-command-discover/SKILL.md` - 150 candidate questions from model health, top 15 output.
- `.agents/skills/source-command-lint-wiki/SKILL.md` - document domain lint checks.
- `.agents/skills/source-command-sync-vision/SKILL.md` - include `Wiki/DDD_Wiki` in index/state synchronization.
- `docs/knowledge-pipeline/README.md` - document the new domain workflow.
- `AGENTS.md` - update repository-level operating rules.
- `index.md` - add `Wiki/` and `DDD_Wiki/` as canonical domain areas.
- `memory/project-state.md` - update live pipeline status after implementation.
- `docs/agent-memory/file-map.md` - add topic-to-file mappings for the domain layer.

Potentially modify:

- `scripts/README.md` - mention the expanded wiki lint if current README lists script behavior.

---

### Task 1: Add Failing Domain-Lint Tests

**Files:**
- Modify: `scripts/tests/test_lint_wiki.py`
- Test: `scripts/tests/test_lint_wiki.py`

- [ ] **Step 1: Add tests for new wiki roots and domain metadata**

Append these test methods inside `LintWikiTests`, before `assertIssue`:

```python
    def test_domain_wiki_roots_are_linted(self):
        self.write("Wiki/entities/no-frontmatter.md", "# WorkOrder\n")
        self.write("DDD_Wiki/aggregates/no-frontmatter.md", "# WorkOrder Aggregate\n")

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertIssue(issues, "missing_frontmatter", "Wiki/entities/no-frontmatter.md")
        self.assertIssue(
            issues, "missing_frontmatter", "DDD_Wiki/aggregates/no-frontmatter.md"
        )

    def test_domain_nodes_require_confidence_and_related(self):
        self.write(
            "Wiki/entities/work_order.md",
            "---\n"
            "title: WorkOrder\n"
            "type: entity\n"
            "status: active\n"
            "created: 2026-06-24\n"
            "updated: 2026-06-24\n"
            "source: RAW_inputs/documents/example.md\n"
            "tags: [domain]\n"
            "---\n"
            "\n"
            "# WorkOrder\n"
            "\n"
            "Описание.\n",
        )

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertIssue(issues, "missing_domain_metadata", "Wiki/entities/work_order.md")

    def test_domain_event_requires_domain_sections(self):
        self.write(
            "Wiki/domain_events/review_package_approved.md",
            "---\n"
            "title: ReviewPackageApproved\n"
            "type: domain-event\n"
            "status: planned\n"
            "created: 2026-06-24\n"
            "updated: 2026-06-24\n"
            "source: RAW_inputs/meetings/reviewer.md\n"
            "confidence: inferred\n"
            "related: [Wiki/entities/review_decision]\n"
            "tags: [domain-event]\n"
            "---\n"
            "\n"
            "# ReviewPackageApproved\n"
            "\n"
            "Reviewer подтвердил готовность package.\n",
        )

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertIssue(
            issues,
            "incomplete_domain_event",
            "Wiki/domain_events/review_package_approved.md",
        )

    def test_valid_domain_event_is_clean(self):
        self.write(
            "Wiki/domain_events/review_package_approved.md",
            "---\n"
            "title: ReviewPackageApproved\n"
            "type: domain-event\n"
            "status: planned\n"
            "created: 2026-06-24\n"
            "updated: 2026-06-24\n"
            "source: RAW_inputs/meetings/reviewer.md\n"
            "confidence: inferred\n"
            "related: [Wiki/entities/review_decision]\n"
            "tags: [domain-event]\n"
            "---\n"
            "\n"
            "# ReviewPackageApproved\n"
            "\n"
            "## Source Aggregate\n"
            "\n"
            "`ReviewDecision`.\n"
            "\n"
            "## Happened In The Past\n"
            "\n"
            "Reviewer approved immutable review package.\n"
            "\n"
            "## Downstream Reactions\n"
            "\n"
            "- Audit entry is appended.\n",
        )

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertEqual([], issues)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m unittest scripts.tests.test_lint_wiki -v
```

Expected: at least these tests fail because `Wiki/` and `DDD_Wiki/` are not in `WIKI_ROOTS`, and domain metadata checks do not exist yet:

```text
FAIL: test_domain_wiki_roots_are_linted
FAIL: test_domain_nodes_require_confidence_and_related
FAIL: test_domain_event_requires_domain_sections
```

- [ ] **Step 3: Git checkpoint**

Run:

```powershell
git diff -- scripts/tests/test_lint_wiki.py
```

Expected: diff contains only the four new tests. Do not stage or commit.

---

### Task 2: Extend `lint-wiki.py` For Domain Roots And Domain Checks

**Files:**
- Modify: `scripts/lint-wiki.py`
- Test: `scripts/tests/test_lint_wiki.py`

- [ ] **Step 1: Add `Wiki` and `DDD_Wiki` to lint roots**

In `scripts/lint-wiki.py`, replace `WIKI_ROOTS` with:

```python
WIKI_ROOTS = (
    "Wiki",
    "DDD_Wiki",
    "Vision_wiki",
    "Code_wiki",
    "RAW_inputs",
    "memory",
    "Общие_принципы",
    "docs/knowledge-pipeline",
)
```

- [ ] **Step 2: Add domain constants**

After `SOURCE_OPTIONAL_TYPES`, add:

```python
DOMAIN_ROOTS = {"Wiki", "DDD_Wiki"}
DOMAIN_METADATA_REQUIRED = ("confidence", "related")
DOMAIN_SECTION_RULES = {
    ("Wiki", "commands"): (
        "## Actor",
        "## Target",
        "## Preconditions",
        "## Outcome",
    ),
    ("Wiki", "domain_events"): (
        "## Source Aggregate",
        "## Happened In The Past",
        "## Downstream Reactions",
    ),
    ("Wiki", "policies"): ("## Rule", "## Decision Outcome"),
    ("Wiki", "specifications"): ("## Predicate", "## Failure Meaning"),
    ("Wiki", "value_objects"): ("## Equality", "## Immutability"),
    ("DDD_Wiki", "bounded_contexts"): ("## Ubiquitous Language Boundary",),
    ("DDD_Wiki", "subdomains"): ("## Classification",),
    ("DDD_Wiki", "context_map"): ("## Upstream Downstream", "## Integration Pattern"),
}
```

- [ ] **Step 3: Call domain validation from `lint`**

In `lint`, after broken wikilink checks, add:

```python
        issues.extend(validate_domain_node(relative, frontmatter, body))
```

Use the indentation level inside the `for file_path in files:` loop, after the wikilink loop.

- [ ] **Step 4: Add domain validation helpers**

Add these functions before `main`:

```python
def validate_domain_node(relative: Path, frontmatter: dict[str, str], body: str) -> list[Issue]:
    if not relative.parts or relative.parts[0] not in DOMAIN_ROOTS:
        return []
    if "_templates" in relative.parts:
        return []
    if relative.name in {"index.md", "_info.md"}:
        return []

    issues: list[Issue] = []
    missing_metadata = [
        key
        for key in DOMAIN_METADATA_REQUIRED
        if frontmatter.get(key) in {None, "", "null", "~"}
    ]
    if missing_metadata:
        issues.append(
            Issue(
                "missing_domain_metadata",
                relative,
                f"Missing domain metadata: {', '.join(missing_metadata)}.",
            )
        )

    section_rule = domain_section_rule(relative)
    if section_rule:
        missing_sections = [section for section in section_rule if section not in body]
        if missing_sections:
            issues.append(
                Issue(
                    domain_section_issue_code(relative),
                    relative,
                    f"Missing sections: {', '.join(missing_sections)}.",
                )
            )

    return issues


def domain_section_rule(relative: Path) -> tuple[str, ...]:
    if len(relative.parts) < 2:
        return ()
    return DOMAIN_SECTION_RULES.get((relative.parts[0], relative.parts[1]), ())


def domain_section_issue_code(relative: Path) -> str:
    if len(relative.parts) >= 2 and relative.parts[0] == "Wiki":
        folder = relative.parts[1]
        if folder == "domain_events":
            return "incomplete_domain_event"
        if folder == "commands":
            return "incomplete_command"
        if folder == "policies":
            return "incomplete_policy"
        if folder == "specifications":
            return "incomplete_specification"
        if folder == "value_objects":
            return "incomplete_value_object"
    if len(relative.parts) >= 2 and relative.parts[0] == "DDD_Wiki":
        return "incomplete_ddd_projection"
    return "incomplete_domain_node"
```

- [ ] **Step 5: Ensure source is required for domain nodes**

In `source_required`, extend the final root check:

```python
    return node_type in SOURCE_REQUIRED_TYPES or relative.parts[0] in {
        "Wiki",
        "DDD_Wiki",
        "Vision_wiki",
        "Code_wiki",
    }
```

- [ ] **Step 6: Run focused lint tests**

Run:

```powershell
python -m unittest scripts.tests.test_lint_wiki -v
```

Expected:

```text
Ran 9 tests
OK
```

The exact test count may be higher if another agent added tests. All tests must pass.

- [ ] **Step 7: Run full script tests**

Run:

```powershell
python -m unittest discover -s scripts\tests -v
```

Expected: all script tests pass.

- [ ] **Step 8: Git checkpoint**

Run:

```powershell
git diff -- scripts/lint-wiki.py scripts/tests/test_lint_wiki.py
```

Expected: diff contains roots, domain metadata checks and tests. Do not stage or commit.

---

### Task 3: Create Domain Wiki Skeleton And Templates

**Files:**
- Create: `Wiki/index.md`
- Create: `Wiki/_templates/*.md`
- Create: `Wiki/_registry/*.md`
- Create: `Wiki/*/_info.md`
- Create: `DDD_Wiki/index.md`
- Create: `DDD_Wiki/model_health.md`
- Create: `DDD_Wiki/*/_info.md`

- [ ] **Step 1: Create root indexes**

Create `Wiki/index.md`:

```markdown
---
title: Domain Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: null
confidence: verified
related: [DDD_Wiki/index]
tags: [domain-wiki, canonical-domain]
---

# Domain Wiki

Канонический слой атомарных доменных знаний GeoService.

## Структура

- [[_registry/glossary]] - compact registry ubiquitous language.
- [[_registry/entities]] - compact registry entities и aggregate roots.
- [[_registry/value_objects]] - compact registry value objects.
- [[_registry/concepts]] - compact registry concepts.
- [[_registry/actors]] - compact registry actors, roles и personas.
- [[_registry/external_systems]] - compact registry external systems.
- [[_registry/commands]] - compact registry commands.
- [[_registry/domain_events]] - compact registry domain events.
- [[_registry/system_events]] - compact registry system events.
- [[_registry/policies]] - compact registry policies.
- [[_registry/specifications]] - compact registry specifications.
- [[_registry/conflicts]] - compact registry model conflicts.
- [[_registry/questions]] - generated discovery/planning questions.

## Связанные Слои

- [[../DDD_Wiki/index]] - производная DDD-модель.
- [[../Vision_wiki/index]] - legacy/source layer продуктовых знаний.
- [[../Code_wiki/index]] - техническая wiki.
```

Create `DDD_Wiki/index.md`:

```markdown
---
title: DDD Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: null
confidence: verified
related: [Wiki/index]
tags: [ddd-wiki, domain-model]
---

# DDD Wiki

Производная DDD-модель GeoService, построенная из атомарных нод `Wiki/`.

## Структура

- [[domains/_info]] - domains.
- [[subdomains/_info]] - core/supporting/generic subdomains.
- [[bounded_contexts/_info]] - bounded contexts и language boundaries.
- [[context_map/_info]] - context map и integration patterns.
- [[aggregates/_info]] - aggregate boundaries и aggregate roots.
- [[services/_info]] - domain/application services.
- [[repositories/_info]] - repositories как model-facing abstractions.
- [[factories/_info]] - factories.
- [[modules/_info]] - modules.
- [[relationships/_info]] - relationships.
- [[state_machines/_info]] - state machines.
- [[invariants/_info]] - invariants.
- [[use_cases/_info]] - use cases.
- [[integration_patterns/_info]] - integration patterns.
- [[model_health]] - полнота модели, gaps и conflicts.
```

- [ ] **Step 2: Create registry files**

Create every file in `Wiki/_registry/` with frontmatter and an empty table. Use this pattern for `Wiki/_registry/entities.md`:

```markdown
---
title: Entities Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: null
confidence: verified
related: [Wiki/index, DDD_Wiki/aggregates/_info]
tags: [domain-registry, entities]
---

# Реестр Сущностей

| ID | Нода | Тип | Bounded context | Статус | Уверенность | Главный источник | Связи | Открыто |
|---|---|---|---|---|---|---|---|---|
```

Use these exact table headers for the other registry files:

```markdown
# Реестр Ubiquitous Language

| ID | Термин | Нода | Bounded context | Статус | Уверенность | Главный источник | Cross-context | Открыто |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Value Objects

| ID | Нода | Bounded context | Equality | Immutability | Статус | Уверенность | Источник | Открыто |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Концепций

| ID | Нода | Тип | Bounded context | Статус | Уверенность | Главный источник | Связи | Открыто |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Actors

| ID | Нода | Actor type | Responsibility | Bounded context | Статус | Уверенность | Источник | Открыто |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр External Systems

| ID | Нода | Direction | Integration pattern | Bounded context | Статус | Уверенность | Источник | Открыто |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Commands

| ID | Command | Нода | Actor | Target | Preconditions | Outcome | Статус | Источник |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Domain Events

| ID | Domain event | Нода | Bounded context | Raised by | Значение для домена | Downstream reactions | Статус | Источник |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр System Events

| ID | Событие | Нода | Actor | Trigger | Изменяет | Preconditions | Статус | Источник |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Policies

| ID | Policy | Нода | Bounded context | Rule | Decision outcome | Статус | Уверенность | Источник |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Specifications

| ID | Specification | Нода | Bounded context | Predicate | Failure meaning | Статус | Уверенность | Источник |
|---|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Конфликтов Модели

| ID | Конфликт | Блокирует | Ноды | Источник A | Источник B | Severity | Следующий вопрос |
|---|---|---|---|---|---|---|---|
```

```markdown
# Реестр Вопросов

| ID | Context | Question | Score | Reason | Unlocks | Source nodes | Answer path | Статус |
|---|---|---|---:|---|---|---|---|---|
```

- [ ] **Step 3: Create templates**

Create these files under `Wiki/_templates/`: `entity.md`, `value_object.md`, `actor.md`, `command.md`, `domain_event.md`, `system_event.md`, `policy.md`, `specification.md`, `conflict.md`.

Use this exact pattern for `Wiki/_templates/domain_event.md`:

```markdown
---
title: Domain Event Template
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: null
confidence: verified
related: [Wiki/_registry/domain_events]
tags: [template, domain-event]
---

# Domain Event Template

```markdown
---
title: EventName
type: domain-event
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: RAW_inputs/path/to/source.md
confidence: verified | inferred | hypothesis
related: [Wiki/entities/example]
tags: [domain-event]
---

# EventName

## Meaning

Что произошло в домене и почему это важно экспертам домена.

## Source Aggregate

Какой aggregate/context порождает событие.

## Happened In The Past

Формулировка события в прошедшем времени.

## Downstream Reactions

- Какая реакция возникает после события.

## Open Questions

- Нет.
```
```

Create the other templates with the same frontmatter shape and these exact required sections:

- `Wiki/_templates/command.md`: `## Actor`, `## Target`, `## Preconditions`, `## Outcome`, `## Open Questions`.
- `Wiki/_templates/policy.md`: `## Rule`, `## Decision Outcome`, `## Open Questions`.
- `Wiki/_templates/specification.md`: `## Predicate`, `## Failure Meaning`, `## Open Questions`.
- `Wiki/_templates/value_object.md`: `## Equality`, `## Immutability`, `## Open Questions`.
- `Wiki/_templates/entity.md`: `## Identity`, `## Lifecycle`, `## Relationships`, `## Open Questions`.
- `Wiki/_templates/actor.md`: `## Responsibilities`, `## Boundaries`, `## Open Questions`.
- `Wiki/_templates/system_event.md`: `## Actor`, `## Trigger`, `## Affected Entity`, `## Outcome`, `## Open Questions`.
- `Wiki/_templates/conflict.md`: `## Conflict`, `## Blocks`, `## Source A`, `## Source B`, `## Severity`, `## Next Question`.

- [ ] **Step 4: Create `_info.md` files**

For every direct subdirectory in `Wiki/` and `DDD_Wiki/`, create `_info.md` with:

```markdown
---
title: <Directory Name>
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: null
confidence: verified
related: [Wiki/index]
tags: [domain-wiki]
---

# <Directory Name>

Назначение папки в доменном слое.
```

For `DDD_Wiki/*/_info.md`, set `related: [DDD_Wiki/index]` and `tags: [ddd-wiki]`.

- [ ] **Step 5: Run lint tests**

Run:

```powershell
python -m unittest scripts.tests.test_lint_wiki -v
python scripts/lint-wiki.py --root .
```

Expected for unit tests: pass.

Expected for repository lint: existing RAW frontmatter conflicts may remain because `RAW_inputs` is read-only by workflow. New `Wiki/` and `DDD_Wiki/` files must not introduce new issues.

- [ ] **Step 6: Git checkpoint**

Run:

```powershell
git status --short -- Wiki DDD_Wiki scripts/lint-wiki.py scripts/tests/test_lint_wiki.py
```

Expected: new domain skeleton files and lint changes. Do not stage or commit.

---

### Task 4: Update `/ingest` Skill For Raw Domain Extraction

**Files:**
- Modify: `.agents/skills/source-command-ingest/SKILL.md`

- [ ] **Step 1: Update description**

Change the skill description frontmatter to:

```yaml
description: Ручная процедура /ingest для обработки RAW_inputs и значимых источников проекта в Wiki/DDD_Wiki, Vision_wiki/Code_wiki.
```

- [ ] **Step 2: Add canonical domain context**

In `## Обязательный Контекст`, add these bullets after `memory/project-state.md`:

```markdown
- `Wiki/index.md` - канонические атомарные доменные ноды.
- `Wiki/_registry/*.md` - compact registries доменной модели.
- `DDD_Wiki/index.md` - производная DDD-модель.
- `DDD_Wiki/model_health.md` - gaps, conflicts и полнота модели.
```

- [ ] **Step 3: Add raw-source-only boundary**

After `## Шаг 1. Определить Объект Ingest`, add:

```markdown
### Граница Raw Source

Обычный `/ingest` работает с сырыми источниками. Его объектом являются файлы из
`RAW_inputs/` или явно указанный внешний source, который агент обосновывает как
raw/source input. `/ingest` не выполняет initialization существующей базы
знаний, не сканирует весь репозиторий и не заменяет `/ingest repository-snapshot`.

Если пользователь не указал путь, `/ingest` ищет только новые добавленные файлы
в `RAW_inputs/`, которых еще нет в обработанных source-записях
`RAW_inputs/index.md`, `Wiki/`, `DDD_Wiki`, `Vision_wiki`, `Code_wiki` или
`memory/project-state.md`. Старые уже обработанные raw-файлы повторно не читать
и не переобрабатывать. Если старый raw-файл выглядит измененным, это
неоднозначность: не запускать повторный ingest автоматически, а запросить явное
решение пользователя.

Обрабатывать нужно любые новые raw-файлы, а не только файлы с ответами на
вопросы. Новым raw source может быть документ, заметка, meeting transcript,
research result, planning answer, discovery answer, exported chat или другой
сырой материал, если он лежит в `RAW_inputs/` и еще не обработан.

Если файл в `RAW_inputs/` содержит ответы на вопросы `/discover` или
планирования спринта, `/ingest` извлекает из него устойчивые доменные факты,
закрывает или уточняет вопросы и обновляет затронутые ноды `Wiki/DDD_Wiki`.
Сам выбор состава спринта остается ответственностью planning skill.
```

- [ ] **Step 4: Replace fact extraction taxonomy**

In `## Шаг 4. Извлечь Факты`, extend the `type` bullet with:

```markdown
- `type` - glossary term, entity, value object, concept, actor, external system,
  command, domain event, system event, policy, specification, relationship,
  invariant, state transition, conflict, question, solution, technical note.
```

- [ ] **Step 5: Add domain distribution rules**

At the start of `## Шаг 5. Разнести По Wiki`, add:

```markdown
Сначала обновить канонический доменный слой:

- glossary terms: `Wiki/glossary/<slug>.md` и `Wiki/_registry/glossary.md`.
- entities: `Wiki/entities/<slug>.md` и `Wiki/_registry/entities.md`.
- value objects: `Wiki/value_objects/<slug>.md` и `Wiki/_registry/value_objects.md`.
- actors/roles/personas: `Wiki/actors/<slug>.md` и `Wiki/_registry/actors.md`.
- external systems: `Wiki/external_systems/<slug>.md` и `Wiki/_registry/external_systems.md`.
- commands: `Wiki/commands/<slug>.md` и `Wiki/_registry/commands.md`.
- domain events: `Wiki/domain_events/<slug>.md` и `Wiki/_registry/domain_events.md`.
- system events: `Wiki/system_events/<slug>.md` и `Wiki/_registry/system_events.md`.
- policies: `Wiki/policies/<slug>.md` и `Wiki/_registry/policies.md`.
- specifications: `Wiki/specifications/<slug>.md` и `Wiki/_registry/specifications.md`.
- model conflicts: `Wiki/conflicts/YYYY-MM-DD-<topic>.md`,
  `Wiki/_registry/conflicts.md` и `DDD_Wiki/model_health.md`.

Затем обновить производную DDD-модель:

- domains/subdomains: `DDD_Wiki/domains/`, `DDD_Wiki/subdomains/`.
- bounded contexts: `DDD_Wiki/bounded_contexts/`.
- context map: `DDD_Wiki/context_map/`.
- aggregates: `DDD_Wiki/aggregates/`.
- services/repositories/factories/modules: соответствующие папки `DDD_Wiki/`.
- state machines/invariants/use cases/integration patterns: соответствующие папки `DDD_Wiki/`.
```

- [ ] **Step 6: Preserve legacy Vision behavior**

In the existing Vision distribution bullets, add this sentence:

```markdown
`Vision_wiki` остается legacy/source layer для доменных знаний. Новые
канонические доменные факты пишутся в `Wiki/DDD_Wiki`; `Vision_wiki` обновлять
только для legacy summaries, product decisions или существующих product
workflow нод.
```

- [ ] **Step 7: Update index/state step**

In `## Шаг 7. Обновить Индексы И State`, add:

```markdown
- `Wiki/index.md` и `Wiki/_registry/*.md` - добавить ссылки на новые доменные ноды.
- `DDD_Wiki/index.md` и `DDD_Wiki/model_health.md` - обновить DDD projection и health.
```

- [ ] **Step 8: Verify skill text**

Run:

```powershell
$bad = 'domain' + '-bootstrap'
rg -n "Raw Source|новые добавленные|повторно не читать|любые новые raw|Wiki/_registry|DDD_Wiki|domain event|planning skill" .agents/skills/source-command-ingest/SKILL.md
rg -n $bad .agents/skills/source-command-ingest/SKILL.md
```

Expected:

- Matches for `Raw Source`, `новые добавленные`, `повторно не читать`,
  `любые новые raw`, `Wiki/_registry`, `DDD_Wiki`, `domain event`,
  `planning skill`.
- No matches for the old bootstrap-like mode name.

---

### Task 5: Update `/discover` Skill For Model-Driven Questions

**Files:**
- Modify: `.agents/skills/source-command-discover/SKILL.md`

- [ ] **Step 1: Add domain context files**

In `## Обязательный Контекст`, add:

```markdown
- `Wiki/index.md` и релевантные `Wiki/_registry/*.md` - каноническое состояние атомарных доменных знаний.
- `DDD_Wiki/index.md` - текущая DDD-модель.
- `DDD_Wiki/model_health.md` - gaps, conflicts, model completeness.
- `Code_wiki/index.md` - техническое состояние, если вопрос связан с реализацией.
```

- [ ] **Step 2: Add model-driven mode**

Before `## Запуск С --phase`, add:

```markdown
## Model-Driven Discovery

Если `Wiki/` и `DDD_Wiki/` существуют, `/discover` стартует от состояния
доменной модели, а не от общего списка вопросов. Агент должен:

1. Прочитать `DDD_Wiki/model_health.md`, `Wiki/_registry/conflicts.md`,
   релевантные registry-файлы и нужные ноды `Wiki/`.
2. Сгенерировать 150 candidate questions.
3. Не показывать все 150 вопросов пользователю по умолчанию.
4. Отранжировать вопросы и показать top 15.
5. Для каждого top-вопроса указать: какую часть модели он разблокирует,
   почему выбран, какие ноды затронет, можно ли ответить в чате или файлом в
   `RAW_inputs/`.

Вопросы должны покрывать ubiquitous language, subdomain classification,
bounded context boundaries, context map, context mapping patterns, aggregates,
aggregate roots, value objects, commands, domain events, policies,
specifications, roles/permissions, external system boundaries, invariants,
state transitions, conflicts и расхождения модели с кодом.
```

- [ ] **Step 3: Keep phase mode compatible**

In `## Запуск С --phase`, add:

```markdown
Если указана фаза Ф0-Ф8 и существует `DDD_Wiki/model_health.md`, фазовые
вопросы должны быть отфильтрованы через текущие gaps/conflicts модели. Не
задавать вопросы, которые не связаны с текущей моделью, RAW source или
решением пользователя.
```

- [ ] **Step 4: Verify discover skill**

Run:

```powershell
rg -n "Model-Driven Discovery|150 candidate|top 15|DDD_Wiki/model_health|domain events|context map" .agents/skills/source-command-discover/SKILL.md
```

Expected: all patterns are found.

---

### Task 6: Add Sprint Planning Skill

**Files:**
- Create: `.agents/skills/source-command-plan-sprint/SKILL.md`
- Modify: `docs/agent-memory/file-map.md`

- [ ] **Step 1: Create skill directory**

Create directory:

```text
.agents/skills/source-command-plan-sprint/
```

- [ ] **Step 2: Create `SKILL.md`**

Create `.agents/skills/source-command-plan-sprint/SKILL.md` with:

```markdown
---
name: source-command-plan-sprint
description: Ручная процедура /plan-sprint для подготовки 14-дневного спринта на основе DDD_Wiki, Wiki, Code_wiki, текущего кода и RAW ответов.
---

# /plan-sprint

`/plan-sprint` помогает выбрать реалистичный вертикальный инкремент на
фиксированный таймбокс 14 календарных дней. Он не заменяет `/discover`:
`/discover` уточняет модель, а `/plan-sprint` выбирает следующий sprint scope.

## Обязательный Контекст

Перед ответом прочитать:

- `DDD_Wiki/model_health.md` - gaps, conflicts и completeness.
- `DDD_Wiki/index.md` - структура DDD-модели.
- `Wiki/index.md` и релевантные `Wiki/_registry/*.md` - атомарные доменные ноды.
- `Wiki/_registry/conflicts.md` - открытые конфликты модели.
- `Code_wiki/index.md` и релевантные технические ноды.
- Текущий код и тесты только по области, которая может попасть в спринт.
- `Vision_wiki/solution/roadmap.md` и legacy product context как справочный слой.
- `docs/release_*` - существующие sprint/release документы.

## Если Пользователь Указал RAW Ответы

Если пользователь указал файл в `RAW_inputs/`, прочитать его как planning
source. Если ответы содержат устойчивые доменные уточнения, предложить или
выполнить обычный `/ingest <path>` до финализации sprint packet, когда эти
уточнения блокируют выбор scope.

## Вопросы

Сгенерировать 150 candidate planning questions. Не показывать все 150
пользователю по умолчанию.

Отранжировать и показать top 15. Scoring:

- влияет ли ответ на выбор feature;
- относится ли feature к core subdomain или supporting/generic области;
- снижает ли риск реализации;
- помогает ли выбрать вертикальный инкремент;
- закрывает ли конфликт доменной модели;
- есть ли техническая готовность в коде;
- можно ли проверить результат в конце 14-дневного спринта;
- не расширяет ли scope за пределы release.

## Sprint Planning Packet

После ответов подготовить:

- цель 14-дневного спринта;
- top features;
- rejected/deferred items;
- affected domain nodes;
- code gaps;
- acceptance criteria;
- risks;
- вопросы или ответы, которые нужно положить в `RAW_inputs/`;
- какие wiki-ноды будут обновлены через `/ingest`.

## Ограничения

- Не расширять спринт больше 14 календарных дней.
- Не выбирать горизонтальный infrastructure-only scope без проверяемого
  пользовательского или доменного инкремента, если пользователь явно не
  попросил технический спринт.
- Не обновлять `Code_wiki` напрямую; техническое знание идет через
  `/ingest repository-change`.
- Не писать продуктовые факты в `Vision_wiki` как новый канон домена.
- Wiki-контент вести на русском языке; пути, команды, API и идентификаторы не
  переводить.
```

- [ ] **Step 3: Update file map**

Add one line to `docs/agent-memory/file-map.md` near other knowledge-pipeline mappings:

```markdown
- domain sprint planning workflow: `.agents/skills/source-command-plan-sprint/SKILL.md`, `DDD_Wiki/model_health.md`, `Wiki/_registry/questions.md`
```

- [ ] **Step 4: Verify skill discovery text**

Run:

```powershell
rg -n "source-command-plan-sprint|14 календарных дней|150 candidate planning|Sprint Planning Packet" .agents/skills/source-command-plan-sprint/SKILL.md docs/agent-memory/file-map.md
```

Expected: all patterns are found.

---

### Task 7: Update Pipeline Docs And Repository Instructions

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/knowledge-pipeline/README.md`
- Modify: `index.md`
- Modify: `memory/project-state.md`
- Modify: `.agents/skills/source-command-lint-wiki/SKILL.md`
- Modify: `.agents/skills/source-command-sync-vision/SKILL.md`
- Modify: `scripts/README.md` if it documents wiki lint roots

- [ ] **Step 1: Update `AGENTS.md` project wiki section**

In the `Project Knowledge Wiki` list, add:

```markdown
- `Wiki/` stores canonical atomic domain knowledge: ubiquitous language, entities, value objects, actors, commands, domain events, policies, specifications, conflicts and questions.
- `DDD_Wiki/` stores the derived DDD model: domains, subdomains, bounded contexts, context map, aggregates, services, repositories, factories, modules, state machines, invariants, use cases, integration patterns and model health.
```

After the manual workflow list, add:

```markdown
Domain workflow:

1. Initial domain model for this repository is created by an implementation initialization pass after `Wiki/`, `DDD_Wiki/` and related skills exist. It is not a separate `/ingest` mode.
2. Normal `/ingest` works with raw/source files only and updates `Wiki/DDD_Wiki` from those sources.
3. Without an explicit path, normal `/ingest` processes only new added files in `RAW_inputs/` and does not reread already processed old raw files.
4. Normal `/ingest` processes any new raw file, not only discovery/planning answer files.
5. `/discover` uses current `DDD_Wiki/model_health.md` and model conflicts to generate 150 candidate questions and show top 15.
6. `/plan-sprint` prepares a 14-day sprint from `DDD_Wiki`, `Wiki`, `Code_wiki`, current code and optional RAW planning answers.
7. `Vision_wiki` remains legacy/source layer for domain knowledge. Do not write new canonical domain facts there.
```

- [ ] **Step 2: Update `docs/knowledge-pipeline/README.md`**

Add a section after current `/ingest` description:

```markdown
## Canonical Domain Layer

`Wiki/` and `DDD_Wiki/` are the canonical domain layer.

- `Wiki/` stores atomic domain nodes and compact registries.
- `DDD_Wiki/` stores the derived DDD model and `model_health.md`.
- `Vision_wiki` remains a legacy/source layer for product discovery history.
- Normal `/ingest` processes raw/source files only.
- Without an explicit path, `/ingest` processes only new added files in
  `RAW_inputs/` that are not yet present in processed source records. It does
  not reread already processed old raw files.
- Any new raw file can be processed: documents, meeting notes, research,
  discovery answers, planning answers, exported chats or other raw materials.
- Initial domain model in this repository is created by a one-time implementation initialization pass, not by a separate `/ingest` mode.
```

Add a `/plan-sprint` section:

```markdown
## `/plan-sprint`

`/plan-sprint` prepares a 14-day sprint. It reads `DDD_Wiki/model_health.md`,
`Wiki/_registry/*.md`, open conflicts, `Code_wiki`, relevant code, existing
release docs and optional RAW planning answers. It generates 150 candidate
planning questions, shows top 15 and then prepares a sprint planning packet.
```

- [ ] **Step 3: Update root `index.md`**

In `## Области Знаний`, add:

```markdown
- [[Wiki/index]] - канонические атомарные доменные знания GeoService.
- [[DDD_Wiki/index]] - производная DDD-модель, context map, aggregates и model health.
```

In `## Ручной Pipeline`, add:

```markdown
- Планирование спринта: запустить `/plan-sprint`, ответить на top 15 вопросов в чате или файлом в `RAW_inputs/`, затем подготовить sprint planning packet на 14 календарных дней.
```

- [ ] **Step 4: Update `memory/project-state.md`**

In the pipeline state section, add one bullet:

```markdown
- Domain layer status: `Wiki/` и `DDD_Wiki/` добавлены как канонический доменный слой; первичный initialization-проход должен построить стартовую модель и `DDD_Wiki/model_health.md`.
```

- [ ] **Step 5: Update lint and sync skills**

In `.agents/skills/source-command-lint-wiki/SKILL.md`, add domain checks to the list:

```markdown
- domain roots `Wiki/` and `DDD_Wiki`;
- domain metadata `confidence` and `related`;
- required sections for commands, domain events, policies, specifications, value objects, bounded contexts, subdomains and context map.
```

In `.agents/skills/source-command-sync-vision/SKILL.md`, add `Wiki/` and `DDD_Wiki/` to "Собрать Изменения" and "Обновить Индексы".

- [ ] **Step 6: Run documentation grep**

Run:

```powershell
$bad = 'domain' + '-bootstrap'
rg -n "Wiki/|DDD_Wiki|/plan-sprint|14" AGENTS.md docs/knowledge-pipeline/README.md index.md memory/project-state.md .agents/skills/source-command-lint-wiki/SKILL.md .agents/skills/source-command-sync-vision/SKILL.md
rg -n $bad AGENTS.md docs/knowledge-pipeline/README.md index.md memory/project-state.md .agents/skills/source-command-lint-wiki/SKILL.md .agents/skills/source-command-sync-vision/SKILL.md
```

Expected:

- Matches for `Wiki/`, `DDD_Wiki`, `/plan-sprint`, `14`.
- No match for the old bootstrap-like mode name.

---

### Task 8: Run Primary Domain Initialization Pass

**Files:**
- Create: selected initial files under `Wiki/`
- Create: selected initial files under `DDD_Wiki/`
- Modify: `Wiki/_registry/*.md`
- Modify: `DDD_Wiki/model_health.md`
- Modify: `Wiki/index.md`
- Modify: `DDD_Wiki/index.md`

**Primary sources to read:**
- `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md`
- `RAW_inputs/documents/UtilityGisEditorRole.md`
- `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md`
- `docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md`
- `Vision_wiki/concepts/utility_gis_editing_domain.md`
- `Vision_wiki/decisions/release_1_utility_workflow.md`
- `Vision_wiki/decisions/release_2_conflict_explanation.md`
- `Code_wiki/архитектура/data_model.md`
- `Code_wiki/архитектура/api_and_realtime.md`

- [ ] **Step 1: Read primary sources**

Run:

```powershell
Get-Content -Raw -Encoding UTF8 'RAW_inputs\documents\utility_gis_editor_domain_dictionary.md'
Get-Content -Raw -Encoding UTF8 'RAW_inputs\documents\UtilityGisEditorRole.md'
Get-Content -Raw -Encoding UTF8 'docs\release_1\sprint_1\2026-06-12-sprint-1-day-1-domain-model-design.md'
Get-Content -Raw -Encoding UTF8 'docs\release_1\2026-06-11-release-1-utility-workflow-sprints.md'
Get-Content -Raw -Encoding UTF8 'Vision_wiki\concepts\utility_gis_editing_domain.md'
Get-Content -Raw -Encoding UTF8 'Vision_wiki\decisions\release_1_utility_workflow.md'
Get-Content -Raw -Encoding UTF8 'Vision_wiki\decisions\release_2_conflict_explanation.md'
Get-Content -Raw -Encoding UTF8 'Code_wiki\архитектура\data_model.md'
Get-Content -Raw -Encoding UTF8 'Code_wiki\архитектура\api_and_realtime.md'
```

Expected: enough information to seed core domain nodes without inventing facts.

- [ ] **Step 2: Create initial glossary and actors**

Create:

- `Wiki/glossary/utility_gis_editing.md`
- `Wiki/actors/editor.md`
- `Wiki/actors/reviewer.md`
- `Wiki/actors/publisher.md`

Each file must have `confidence`, `related`, source, and sections:

```markdown
# <Name>

## Meaning

## Responsibilities

## Boundaries

## Open Questions
```

For `publisher.md`, set `status: needs-review` and include the open question about whether `Reviewer` and `Publisher` are separate outside the demo.

- [ ] **Step 3: Create initial entities and value objects**

Create:

- `Wiki/entities/work_order.md`
- `Wiki/entities/edit_version.md`
- `Wiki/entities/default_state.md`
- `Wiki/entities/feeder.md`
- `Wiki/entities/network_feature.md`
- `Wiki/entities/network_association.md`
- `Wiki/entities/review_decision.md`
- `Wiki/value_objects/aoi.md`
- `Wiki/value_objects/risk_tier.md`

Use source hierarchy from the spec. If Release 1 docs and Release 2 docs differ, preserve the conflict in `Wiki/conflicts/` instead of choosing silently.

- [ ] **Step 4: Create initial commands and events**

Create:

- `Wiki/commands/open_edit_version.md`
- `Wiki/commands/submit_for_review.md`
- `Wiki/commands/approve_review_package.md`
- `Wiki/commands/post_to_default.md`
- `Wiki/domain_events/edit_version_opened.md`
- `Wiki/domain_events/review_package_approved.md`
- `Wiki/domain_events/authoritative_post_completed.md`
- `Wiki/system_events/workspace_loaded.md`

For each command include `## Actor`, `## Target`, `## Preconditions`, `## Outcome`.

For each domain event include `## Source Aggregate`, `## Happened In The Past`, `## Downstream Reactions`.

- [ ] **Step 5: Create initial policies and specifications**

Create:

- `Wiki/policies/reviewer_post_policy.md`
- `Wiki/policies/stale_approval_policy.md`
- `Wiki/specifications/editor_assigned_to_work_order.md`
- `Wiki/specifications/edit_version_ready_for_review.md`
- `Wiki/specifications/post_allowed.md`

For each policy include `## Rule` and `## Decision Outcome`.

For each specification include `## Predicate` and `## Failure Meaning`.

- [ ] **Step 6: Create initial conflicts**

Create:

- `Wiki/conflicts/2026-06-24-reviewer-vs-publisher.md`
- `Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy.md`

Each conflict must include:

```markdown
## Conflict

## Blocks

## Source A

## Source B

## Severity

## Next Question
```

- [ ] **Step 7: Create initial DDD model projections**

Create:

- `DDD_Wiki/domains/geoservice.md`
- `DDD_Wiki/subdomains/utility_authoritative_editing.md`
- `DDD_Wiki/subdomains/generic_map_editing.md`
- `DDD_Wiki/bounded_contexts/work_order.md`
- `DDD_Wiki/bounded_contexts/utility_network.md`
- `DDD_Wiki/bounded_contexts/review_post.md`
- `DDD_Wiki/bounded_contexts/audit.md`
- `DDD_Wiki/bounded_contexts/auth.md`
- `DDD_Wiki/context_map/geoservice_context_map.md`
- `DDD_Wiki/aggregates/work_order.md`
- `DDD_Wiki/aggregates/edit_version.md`
- `DDD_Wiki/aggregates/review_package.md`
- `DDD_Wiki/state_machines/work_order_lifecycle.md`
- `DDD_Wiki/invariants/release1_safety_invariants.md`
- `DDD_Wiki/use_cases/utility_editor_workflow.md`
- `DDD_Wiki/integration_patterns/external_gis_anticorruption_boundary.md`

Mark `utility_authoritative_editing` as `core`. Mark `generic_map_editing` as `supporting` or `generic` with `confidence: inferred` and explain the classification in the body.

- [ ] **Step 8: Update registries**

Add one row for every created node to the matching `Wiki/_registry/*.md`.

Use deterministic IDs:

- `TERM-001`, `TERM-002` for glossary.
- `ENT-001`, `ENT-002` for entities.
- `VO-001`, `VO-002` for value objects.
- `ACT-001`, `ACT-002` for actors.
- `CMD-001`, `CMD-002` for commands.
- `DEV-001`, `DEV-002` for domain events.
- `EVT-001`, `EVT-002` for system events.
- `POL-001`, `POL-002` for policies.
- `SPEC-001`, `SPEC-002` for specifications.
- `CON-001`, `CON-002` for conflicts.

- [ ] **Step 9: Update `DDD_Wiki/model_health.md`**

Set content:

```markdown
---
title: Domain Model Health
type: state
status: active
created: 2026-06-24
updated: 2026-06-24
source: null
confidence: verified
related: [DDD_Wiki/index, Wiki/_registry/conflicts]
tags: [ddd-wiki, model-health]
---

# Domain Model Health

| Область | Полнота | Конфликты | Gaps | Риск для planning | Следующее действие |
|---|---:|---:|---:|---|---|
| WorkOrder lifecycle | 70% | 0 | 3 | medium | Уточнить состояния после validation/review. |
| Review/Post policy | 45% | 2 | 5 | high | Проверить с real Reviewer и Data Owner. |
| Utility network associations | 60% | 1 | 4 | high | Развести physical/logical impact и demo rules. |

## Открытые Конфликты

- [[../Wiki/conflicts/2026-06-24-reviewer-vs-publisher]]
- [[../Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]]

## Следующие Вопросы

- Кто в реальной организации имеет право выполнить technical post?
- Является ли `Reviewer` только approving actor или также publisher в demo?
- Какие association changes достаточно убедительны для Release 2 demo?
```

- [ ] **Step 10: Run wiki lint**

Run:

```powershell
python scripts/lint-wiki.py --root .
```

Expected: no new issues from `Wiki/` and `DDD_Wiki/`. Existing RAW frontmatter issues may remain.

- [ ] **Step 11: Git checkpoint**

Run:

```powershell
git status --short -- Wiki DDD_Wiki
```

Expected: created initial domain model files. Do not stage or commit.

---

### Task 9: Final Verification And Memory Gate

**Files:**
- Possibly modify: `docs/agent-memory/file-map.md`
- Possibly modify: existing durable memory only if `scripts/check-memory-needed.py --check` requires it

- [ ] **Step 1: Run script tests**

Run:

```powershell
python -m unittest discover -s scripts\tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run wiki lint**

Run:

```powershell
python scripts/lint-wiki.py --root .
```

Expected: if failures remain, they must be the known RAW frontmatter conflict. New `Wiki/DDD_Wiki` files must be clean.

- [ ] **Step 3: Run memory gate**

Run:

```powershell
python scripts/check-memory-needed.py --check
```

Expected: if it warns, update an existing durable memory entry only when the unique knowledge is not already preserved by the spec, plan, skills or wiki files.

- [ ] **Step 4: Check old forbidden mode is absent**

Run:

```powershell
$bad1 = '/ingest ' + 'domain' + '-bootstrap'
$bad2 = 'domain' + '-bootstrap'
rg -n $bad1 AGENTS.md docs .agents Wiki DDD_Wiki
rg -n $bad2 AGENTS.md docs .agents Wiki DDD_Wiki
```

Expected: no matches.

- [ ] **Step 5: Check required domain terms are discoverable**

Run:

```powershell
rg -n "Ubiquitous Language|Value Object|Domain Event|Context Map|Anti-Corruption Layer|Specification|Policy|Command|External System|/plan-sprint" Wiki DDD_Wiki .agents docs AGENTS.md index.md
```

Expected: all terms are found.

- [ ] **Step 6: Final diff review**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors. Working tree includes only intended implementation files plus pre-existing unrelated changes. Do not stage or commit without explicit user request.

---

## Self-Review Checklist For Implementer

- The plan creates `Wiki/` and `DDD_Wiki/` as canonical domain layers.
- The plan does not add a bootstrap-like `/ingest` mode.
- `/ingest` remains raw-source processing.
- No-arg `/ingest` processes only new added `RAW_inputs/` files.
- `/ingest` handles any new raw file, not only answer files.
- `/discover` generates 150 candidate questions and shows top 15.
- `/plan-sprint` targets a fixed 14-calendar-day sprint.
- DDD coverage includes strategic and tactical concepts from the design spec.
- Domain lint checks verify `confidence`, `related` and required domain sections.
- `Vision_wiki` remains legacy/source layer.
- `Code_wiki` remains governed by `/ingest repository-change`.
- No task requires `git add` or `git commit`.
