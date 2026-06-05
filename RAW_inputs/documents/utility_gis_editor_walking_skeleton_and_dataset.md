# Utility GIS editor: walking skeleton и минимальный synthetic utility dataset

## Контекст

Документ объединяет два ответа по варианту использования **Utility GIS editor**:

1. Как должен выглядеть walking skeleton от входа пользователя до итогового authoritative state.
2. Какой самый маленький synthetic utility dataset нужен, чтобы сценарий был понятным и не выглядел игрушечным.

Главная идея: для Utility GIS editor важно проверить не просто CRUD-редактирование на карте, а безопасный путь сетевой правки через **edit version**, **validation**, **reconcile**, **conflict resolution**, **review** и **post в authoritative state**.

---

# 1. Walking skeleton от входа пользователя до authoritative state

## 1.1. Короткая формула

Walking skeleton должен доказывать полный end-to-end поток:

```text
Login
→ Work order
→ Edit version
→ Network edit
→ Save change set
→ Validate topology
→ Reconcile with Default
→ Resolve conflict
→ Reviewer approve
→ Post to Default
→ Authoritative state updated
```

Это не демо-карта с кнопкой `Save`. Это минимальная branch-like система, которая проверяет, что правка инженерной сети не теряется молча и попадает в authoritative state только после контроля.

---

## 1.2. Цель walking skeleton

Для Utility GIS editor walking skeleton должен проверять самый рискованный путь:

```text
Параллельная правка инженерной сети с контролируемой публикацией в authoritative state.
```

Минимальный сценарий:

```text
1. Пользователь логинится.
2. Открывает назначенный work order.
3. Создает isolated edit version.
4. Меняет network feature.
5. Меняет или создает network association.
6. Система сохраняет изменения как draft/change set.
7. Система запускает topology validation.
8. Система делает reconcile с текущим Default.
9. Если есть конфликт, показывает diff.
10. Конфликт разрешается явно.
11. Reviewer approve.
12. Система выполняет post в Default.
13. Read-only пользователь видит новое authoritative state.
14. Audit log показывает всю цепочку.
```

---

## 1.3. Минимальная предметная модель

Минимальные сущности:

```text
User
Role
WorkOrder
NetworkVersion
NetworkFeature
NetworkAssociation
ChangeSet
Conflict
ValidationIssue
AuthoritativeSnapshot
AuditLog
```

Минимальные роли:

```text
Utility GIS editor
Reviewer
Admin
Read-only consumer
```

Минимальные типы объектов сети:

```text
Line        — участок сети
Device      — устройство: выключатель, клапан, трансформатор, колодец
Junction    — узел соединения
Association — связь между объектами
```

Пример:

```text
Line L-1001
Device D-501
Junction J-10
Association: D-501 connected_to L-1001
```

---

## 1.4. Состояния процесса

```text
LoggedIn
WorkOrderOpened
EditVersionCreated
DraftEdited
DraftSaved
TopologyValidated
ReconcileStarted
ConflictDetected
ConflictResolved
ReviewRequested
ReviewApproved
PostedToDefault
AuthoritativeStateUpdated
VersionClosed
```

Минимальная схема:

```text
Login
  ↓
Open Work Order
  ↓
Create Edit Version
  ↓
Edit Network Feature
  ↓
Save Draft Change
  ↓
Validate Topology
  ↓
Reconcile With Default
  ↓
No Conflict ───────────────→ Request Review
  ↓                            ↓
Conflict Detected              Review Approved
  ↓                            ↓
Resolve Conflict ───────────→ Post To Default
                               ↓
                       Authoritative State
```

---

## 1.5. Сквозной пользовательский сценарий

### Шаг 1. Вход пользователя

После входа система должна определить:

```text
User: Алексей
Role: Utility GIS editor
Allowed AOI: Район-1
Allowed layers: electric_lines, electric_devices
Can edit: yes
Can post to authoritative state: no
Can approve: no
```

Важно: editor может редактировать рабочую версию, но не должен напрямую менять authoritative state.

---

### Шаг 2. Получение work order

```text
WorkOrder: WO-2026-00017
Тип: замена устройства
AOI: Район-1
Объект: Device D-501
Статус: Assigned
```

На карте пользователь видит:

```text
Authoritative layer: Default
Working version: отсутствует
```

---

### Шаг 3. Создание рабочей версии

Пользователь нажимает `Create edit version`.

Система создает:

```text
Version: V-WO-2026-00017-ALEXEY
Base version: Default
Status: Open
Owner: Алексей
```

Смысл: все изменения идут не сразу в Default, а в изолированную рабочую версию.

---

### Шаг 4. Редактирование объекта сети

Пользователь меняет объект:

```text
Device D-501
old status: planned
new status: installed
```

И добавляет связь:

```text
Association:
Device D-501 connected_to Line L-1001
```

Система сохраняет change set:

```text
ChangeSet CS-9001
Version: V-WO-2026-00017-ALEXEY
Feature: D-501
Operation: Update
Field: status
Old value: planned
New value: installed
```

Второе изменение:

```text
ChangeSet CS-9002
Version: V-WO-2026-00017-ALEXEY
Feature: Association D-501 → L-1001
Operation: Insert
```

---

## 1.6. Минимальная topology validation

Для skeleton достаточно 3–5 правил:

```text
1. Device должен быть связан хотя бы с одной Line.
2. Line не может иметь пустую геометрию.
3. Device должен находиться в допустимом расстоянии от Line.
4. Нельзя удалить Junction, если к нему подключена Line.
5. Association не может ссылаться на несуществующий объект.
```

Успешный результат:

```text
Validation status: Passed
Dirty areas: 0
```

Неуспешный результат:

```text
Validation status: Failed
Issue: Device D-501 is not connected to any line
```

---

## 1.7. Reconcile с authoritative state

Пользователь запускает:

```text
Reconcile with Default
```

Система сравнивает:

```text
Base snapshot at version creation
Current Default
User edit version
```

Минимальный конфликт:

```text
Алексей в своей версии:
Device D-501 status = installed

Другой пользователь уже запостил в Default:
Device D-501 status = removed
```

Система показывает:

```text
Conflict detected
Feature: Device D-501
Field: status

Base value: planned
Your value: installed
Default value: removed
```

Это ключевая часть skeleton. Без нее это обычный CRUD-редактор.

---

## 1.8. Разрешение конфликта

Минимальный UI:

```text
Use my version
Use Default version
Manual merge
```

Пример manual merge:

```text
status = replaced
comment = "Device physically replaced, old asset removed"
```

Система сохраняет решение:

```text
Conflict C-3001
Resolution: ManualMerge
ResolvedBy: reviewer
ResolvedAt: 2026-06-04 15:42
```

---

## 1.9. Review перед публикацией

Пользователь нажимает:

```text
Submit for review
```

Статус версии:

```text
ReviewRequested
```

Reviewer видит:

```text
WorkOrder: WO-2026-00017
Changed features: 2
Validation: Passed
Conflicts: Resolved
Ready to post: yes
```

Reviewer нажимает:

```text
Approve and post
```

---

## 1.10. Post to Default / authoritative state

После approve система переносит изменения в authoritative layer:

```text
Default version updated
Device D-501 status = replaced
Association D-501 → L-1001 created
WorkOrder status = Completed
Edit version status = Closed
```

Downstream-потребители видят уже не draft, а authoritative state:

```text
Authoritative state:
Device D-501
status = replaced
connected_to = Line L-1001
source_work_order = WO-2026-00017
```

---

## 1.11. Финальный экран для пользователя

Финальный экран не должен быть просто `Saved`.

Лучше:

```text
Work order completed
Version posted to authoritative state
Topology validation passed
Conflicts resolved: 1
Posted by: Reviewer
Posted at: 2026-06-04 15:45
Authoritative layer: updated
```

Пользователь должен понимать:

```text
моя правка не просто сохранена;
она прошла validation;
она не потеряла чужие изменения;
она опубликована в Default;
она стала authoritative.
```

---

## 1.12. Минимальный backend skeleton

```http
POST /auth/login
GET  /work-orders/assigned-to-me
POST /work-orders/{workOrderId}/versions
GET  /versions/{versionId}/features
PATCH /versions/{versionId}/features/{featureId}
POST /versions/{versionId}/associations
POST /versions/{versionId}/validate
POST /versions/{versionId}/reconcile
POST /conflicts/{conflictId}/resolve
POST /versions/{versionId}/submit-review
POST /versions/{versionId}/approve
POST /versions/{versionId}/post
GET  /authoritative/features/{featureId}
```

---

## 1.13. Минимальная БД

```text
users
roles
work_orders

network_features_default
network_associations_default

network_versions
network_feature_changes
network_association_changes

validation_issues
reconcile_runs
conflicts
conflict_resolutions
audit_log
```

В рабочей версии можно хранить не полную копию сети, а change-set:

```text
base_version_id
feature_id
operation
old_value
new_value
changed_by
changed_at
```

---

## 1.14. Минимальный frontend

Нужно 5 экранов:

```text
1. Login
2. My work orders
3. Map editor
4. Reconcile/conflict view
5. Review/post result
```

Пример conflict view:

```text
Feature: Device D-501

Base:    planned
Mine:    installed
Default: removed

[Use mine] [Use Default] [Manual merge]
```

---

## 1.15. Что обязательно должно быть в walking skeleton

```text
1. Login/RBAC.
2. Work order.
3. Isolated edit version.
4. Редактирование хотя бы одного network feature.
5. Редактирование хотя бы одной association.
6. Validation.
7. Reconcile с Default.
8. Один искусственно созданный конфликт.
9. Conflict resolution.
10. Reviewer approve.
11. Post в authoritative state.
12. Audit trail.
```

Без этих частей skeleton не проверит главный риск варианта использования.

---

## 1.16. Что можно не делать в первой версии

```text
1. Полная utility network topology.
2. Настоящий trace engine.
3. Сложные dirty areas.
4. Offline sync.
5. 3D.
6. Полная история всех версий.
7. Массовые bulk edits.
8. Продвинутый geometry diff.
9. Полная схема ArcGIS branch versioning.
```

Для skeleton достаточно доказать жизненный цикл:

```text
draft → validate → reconcile → review → post → authoritative
```

---

## 1.17. Критерии готовности walking skeleton

Walking skeleton можно считать успешным, если воспроизводится такой тест:

```text
1. Editor A входит в систему.
2. Editor A открывает work order.
3. Editor A создает edit version.
4. Editor A меняет Device D-501.
5. Editor B или тестовый скрипт меняет тот же Device D-501 в Default.
6. Editor A запускает reconcile.
7. Система показывает конфликт.
8. Конфликт разрешается.
9. Reviewer approve.
10. Изменение публикуется в Default.
11. Read-only пользователь видит новое authoritative state.
12. Audit log показывает всю цепочку.
```

Главные критерии:

```text
Ни одна параллельная правка не теряется молча.

Пользователь понимает, на каком этапе находится его правка:
draft, validated, conflicted, reviewed или authoritative.

Authoritative state обновляется только после validation, reconcile и approve.
```

---

# 2. Минимальный synthetic utility dataset

## 2.1. Короткий ответ

Самый маленький dataset, который понятен и не выглядит игрушечным:

```text
1 service area / AOI
1 subnetwork / feeder
7 junctions
6 line segments
6 devices
8–10 associations
2 work orders
3 users
2 edit versions + Default
4 заранее подготовленных conflict-сценария
```

Итого: примерно **20–25 записей сетевых объектов** плюс служебные записи.

Это достаточно мало для быстрой реализации, но достаточно похоже на настоящую utility-сеть.

---

## 2.2. Рекомендуемый вариант: маленький electric feeder

Лучше взять электросеть, потому что на ней хорошо видны:

```text
линии,
устройства,
узлы,
switch status,
topology validation,
association,
ошибочный trace,
конфликт статуса,
конфликт геометрии,
конфликт удаления.
```

Название dataset:

```text
synthetic_utility_feeder_01
```

Смысловая модель:

```text
Подстанция → выключатель → линия → секционный выключатель → трансформатор → потребитель

Плюс боковая ветка и normally-open tie switch.
```

Это уже не игрушка, потому что появляется utility-смысл: если неправильно изменить выключатель или связь, downstream trace станет неверным.

---

## 2.3. Service area / AOI

| id | name | purpose |
|---|---|---|
| AOI-01 | Район-1 | зона, где Utility GIS editor имеет право редактировать |

Зачем нужен:

```text
Проверить, что editor может редактировать только внутри своей зоны.
```

---

## 2.4. Junctions — 7 узлов

| id | name | type | description |
|---|---|---|---|
| J-001 | Substation bus | busbar | точка выхода из подстанции |
| J-002 | Feeder joint 1 | junction | промежуточный узел |
| J-003 | Switch node | junction | место установки секционного switch |
| J-004 | Branch joint | junction | узел ветвления |
| J-005 | Transformer tap | junction | точка подключения трансформатора |
| J-006 | Customer service point | service_point | точка потребителя |
| J-007 | Tie point | junction | точка связи с соседним фидером |

Почему не меньше:

```text
Если сделать 2–3 узла, не будет ветвления, tie switch и нормальной проверки topology.
```

---

## 2.5. Lines — 6 линейных объектов

| id | name | from | to | status | voltage |
|---|---|---|---|---|---|
| L-001 | Feeder main 1 | J-001 | J-002 | in_service | 10kV |
| L-002 | Feeder main 2 | J-002 | J-003 | in_service | 10kV |
| L-003 | Feeder main 3 | J-003 | J-004 | in_service | 10kV |
| L-004 | Transformer tap line | J-004 | J-005 | in_service | 10kV |
| L-005 | Low voltage service | J-005 | J-006 | in_service | 0.4kV |
| L-006 | Tie line | J-003 | J-007 | in_service | 10kV |

Зачем нужен `L-006`:

```text
Он делает dataset похожим на настоящую сеть, потому что появляется normally-open tie.
```

---

## 2.6. Devices — 6 устройств

| id | name | type | node | status | normal_state |
|---|---|---|---|---|---|
| D-001 | Breaker BR-01 | breaker | J-001 | closed | closed |
| D-002 | Switch SW-01 | switch | J-003 | closed | closed |
| D-003 | Fuse FU-01 | fuse | J-004 | closed | closed |
| D-004 | Transformer TX-01 | transformer | J-005 | in_service | in_service |
| D-005 | Tie switch SW-TIE-01 | switch | J-007 | open | open |
| D-006 | Meter M-01 | meter | J-006 | active | active |

Почему именно такие:

```text
Breaker показывает начало питания.
Switch нужен для конфликтов по status.
Fuse нужен для topology/trace.
Transformer нужен для смены voltage level.
Tie switch нужен для проверки, что сеть не превращается в лишнюю петлю.
Meter/Service point нужен, чтобы downstream trace имел понятный бизнес-результат.
```

---

## 2.7. Associations — 8–10 связей

| id | association_type | from | to |
|---|---|---|---|
| A-001 | connected_to | D-001 | L-001 |
| A-002 | connected_to | D-002 | L-002 |
| A-003 | connected_to | D-002 | L-003 |
| A-004 | connected_to | D-003 | L-003 |
| A-005 | connected_to | D-003 | L-004 |
| A-006 | connected_to | D-004 | L-004 |
| A-007 | connected_to | D-004 | L-005 |
| A-008 | connected_to | D-005 | L-006 |
| A-009 | feeds | D-004 | D-006 |
| A-010 | contained_in | D-001 | AOI-01 |

Самые важные связи:

```text
D-002 connected_to L-002/L-003
D-004 connected_to L-004/L-005
D-005 connected_to L-006
```

Именно на них можно проверять:

```text
association insert,
association delete,
association conflict,
invalid association,
topology validation.
```

---

## 2.8. Work orders — 2 штуки

| id | title | assigned_to | target_object | goal |
|---|---|---|---|---|
| WO-001 | Replace switch SW-01 | Editor A | D-002 | заменить/обновить секционный выключатель |
| WO-002 | Retire feeder segment | Editor B | L-003 / D-002 | вывести участок или изменить его статус |

Почему два:

```text
Один work order проверяет обычный путь edit → validate → review → post.
Второй нужен, чтобы создать конфликт в Default до post первого пользователя.
```

---

## 2.9. Users — 3 пользователя

| user | role | purpose |
|---|---|---|
| alexey.editor | Utility GIS editor | основной пользователь |
| bolat.editor | Utility GIS editor | создает параллельную правку |
| marina.reviewer | Reviewer | approve/reject перед post |

Этого достаточно для проверки:

```text
editor не может post напрямую,
reviewer видит diff,
reviewer approve нужен перед authoritative state.
```

---

## 2.10. Versions — минимум 3 состояния

| version | owner | purpose |
|---|---|---|
| Default | system | authoritative state |
| V-WO-001-ALEXEY | alexey.editor | рабочая версия первого editor |
| V-WO-002-BOLAT | bolat.editor | параллельная версия / источник конфликта |

Главное: `Default` должен измениться после того, как `V-WO-001-ALEXEY` была создана.

Тогда можно проверить:

```text
Default changed after version creation
→ reconcile required
→ conflict detected
→ post blocked until conflict resolution
```

---

## 2.11. Conflict-сценарии

### Сценарий 1. Update/update conflict

```text
Base Default:
D-002.status = closed

Editor A в V-WO-001:
D-002.status = replaced

Editor B уже запостил в Default:
D-002.status = retired

Expected:
Conflict type = Update/Update
Post blocked = true
```

---

### Сценарий 2. Geometry/geometry conflict

```text
Editor A:
меняет геометрию L-003

Editor B:
тоже меняет геометрию L-003 и постит раньше

Expected:
Conflict type = Geometry/Geometry
System shows both versions
Post blocked until explicit resolution
```

Минимальные варианты решения:

```text
Use my geometry
Use Default geometry
Cancel and edit manually
```

---

### Сценарий 3. Update/delete conflict

```text
Editor A:
меняет D-003.status = inspected

Editor B:
удаляет или decommissions D-003 в Default

Expected:
Conflict type = Update/Delete
Post blocked = true
```

---

### Сценарий 4. Association conflict

```text
Editor A:
создает association D-002 connected_to L-003

Editor B:
меняет L-003 status = retired
или удаляет связь D-002 → L-003

Expected:
Association conflict
Topology validation failed or reconcile conflict
```

---

## 2.12. Минимальные validation rules

Чтобы dataset не выглядел игрушечным, нужны хотя бы 5 правил:

```text
1. Device не может быть orphan: он должен иметь хотя бы одну connected_to association.
2. Line должен иметь from_junction и to_junction.
3. Transformer должен соединять разные voltage levels: 10kV → 0.4kV.
4. Normally-open tie switch не должен создавать активную петлю, если он closed без разрешения.
5. Нельзя post, если есть unresolved dirty areas / validation issues.
```

Эти правила дают ощущение настоящей engineering domain logic.

---

## 2.13. Нужные атрибуты

### Lines

```text
id
name
from_junction_id
to_junction_id
voltage
status
installation_year
geometry
updated_at
updated_by
```

### Devices

```text
id
name
device_type
junction_id
status
normal_state
asset_id
installation_year
updated_at
updated_by
```

### Associations

```text
id
association_type
from_feature_id
to_feature_id
status
created_at
created_by
```

### Work orders

```text
id
title
status
assigned_to
target_feature_id
created_at
completed_at
```

### Versions

```text
id
name
base_version_id
owner_id
work_order_id
status
created_at
last_reconcile_at
posted_at
```

---

## 2.14. Как dataset должен выглядеть на карте

```text
[J-001 Substation]
      |
    L-001
      |
[J-002]
      |
    L-002
      |
[J-003]--- L-006 ---[J-007 Tie switch open]
  |
 D-002 Switch
  |
 L-003
  |
[J-004]---D-003 Fuse
  |
 L-004
  |
[J-005 Transformer]
  |
 L-005
  |
[J-006 Meter/Customer]
```

Смысл карты должен быть понятен без объяснения:

```text
есть источник питания,
есть магистраль,
есть секционный switch,
есть трансформатор,
есть потребитель,
есть tie switch,
есть место для конфликта.
```

---

## 2.15. Почему меньший dataset будет игрушечным

### Если оставить только одну линию и одно устройство

```text
Нет ветвления.
Нет trace-смысла.
Нет association conflict.
Нет topology риска.
Нет реалистичного reconcile/post.
```

Это будет обычный CRUD.

### Если оставить только 2–3 линии

```text
Можно показать geometry edit, но нельзя показать utility-смысл:
какой объект питается, где switch, что ломает сеть.
```

### Если убрать второй work order

```text
Нельзя естественно показать параллельную правку.
Конфликт придется создавать искусственно через SQL.
```

### Если убрать reviewer

```text
Сценарий перестает проверять controlled authoritative publishing.
```

---

## 2.16. Нижняя граница dataset

Если совсем минимизировать, не стоит опускаться ниже:

```text
1 AOI
1 feeder
5 junctions
4 lines
4 devices
6 associations
2 work orders
2 editors
1 reviewer
Default + 2 edit versions
```

Оптимальный минимум:

```text
1 AOI
1 feeder
7 junctions
6 lines
6 devices
10 associations
2 work orders
3 users
3 versions
```

---

## 2.17. Что dataset должен доказать

Он должен позволить показать полный путь:

```text
1. Editor A входит в систему.
2. Открывает WO-001.
3. Создает edit version.
4. Меняет D-002 Switch.
5. Добавляет или меняет association.
6. Запускает validation.
7. Editor B параллельно меняет тот же объект или связанную line.
8. Editor B постит изменения в Default.
9. Editor A запускает reconcile.
10. Система показывает conflict.
11. Conflict явно разрешается.
12. Reviewer смотрит diff.
13. Reviewer approve.
14. Система post-ит изменения в Default.
15. Read-only пользователь видит новое authoritative state.
16. Audit log показывает всю цепочку.
```

---

## Итог

Самый маленький synthetic utility dataset, который не выглядит игрушечным:

```text
Один маленький feeder с подстанцией, секционным switch, fuse, transformer, meter, tie switch, 6 line segments, 7 junctions, 8–10 associations и двумя параллельными work orders.
```

Такой dataset маленький, но уже проверяет главное:

```text
network topology,
associations,
dirty/invalid state,
parallel editing,
conflict detection,
review,
post to authoritative state,
audit trail.
```

Главный принцип:

```text
Dataset должен быть маленьким по количеству объектов,
но настоящим по типам риска.
```
