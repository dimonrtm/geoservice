# Acceptance Criteria для варианта использования Utility GIS editor

## Контекст

Этот документ фиксирует acceptance criteria для варианта использования **Utility GIS editor**.

Цель критериев — заменить расплывчатую формулировку **«все типа работает»** на проверяемые условия готовности.

Главный риск сценария: **правка инженерной сети должна дойти до authoritative state без silent overwrite, с validation, conflict handling, review и audit trail**.

---

# Acceptance criteria

## AC-01. Пользователь не может редактировать authoritative state напрямую

**Given** пользователь вошел как `Utility GIS editor`
**When** он открывает слой инженерной сети
**Then** система показывает authoritative layer как read-only
**And** пользователь может редактировать только через рабочую версию / edit version
**And** прямой `UPDATE/DELETE/INSERT` в Default/authoritative state через UI невозможен

Критерий заменяет фразу:

> “Редактирование вроде работает”

на:

> “Редактор физически не может случайно изменить authoritative state в обход версии”.

---

## AC-02. Для work order создается отдельная edit version

**Given** пользователю назначен work order `WO-001`
**When** пользователь нажимает `Create edit version`
**Then** создается версия `V-WO-001-{user}`
**And** версия имеет ссылку на base authoritative state
**And** все дальнейшие изменения сохраняются только внутри этой версии
**And** work order получает статус `In editing`

Минимально в БД должно быть видно:

```text
work_order_id = WO-001
version_id = V-WO-001-ALEXEY
base_version = Default
status = Open
owner = Алексей
```

---

## AC-03. Изменение feature сохраняется как change set, а не как немедленная публикация

**Given** открыта edit version
**When** пользователь меняет атрибут `Device D-501.status` с `planned` на `installed`
**Then** изменение сохраняется как draft/change set
**And** authoritative state остается без изменений
**And** система хранит старое и новое значение

Проверяемый результат:

```text
Default:
D-501.status = planned

Edit version:
D-501.status = installed

ChangeSet:
feature_id = D-501
field = status
old_value = planned
new_value = installed
operation = Update
```

---

## AC-04. Изменение association сохраняется и валидируется

**Given** пользователь редактирует сетевой объект
**When** он создает association `Device D-501 connected_to Line L-1001`
**Then** association сохраняется в edit version
**And** authoritative associations не меняются до post
**And** validation проверяет, что оба объекта существуют
**And** validation проверяет, что связь допустима по правилам сети

Пример успешного результата:

```text
Validation: Passed
Issues: 0
Association: D-501 -> L-1001
```

Пример неуспешного результата:

```text
Validation: Failed
Issue: Association references missing Line L-1001
```

---

## AC-05. Нельзя отправить версию на review, если topology validation failed

**Given** в edit version есть ошибка topology
**When** пользователь нажимает `Submit for review`
**Then** система блокирует отправку
**And** показывает список validation issues
**And** версия остается в статусе `Draft` или `ValidationFailed`

Пример:

```text
Cannot submit for review.

Validation issue:
Device D-501 is not connected to any line.
```

Это лучше, чем “работает”, потому что явно проверяет:

> Невалидная сеть не может попасть к reviewer и тем более в authoritative state.

---

## AC-06. Reconcile находит конфликт update/update по одному объекту

**Given** пользователь создал edit version от Default
**And** в момент создания версии `Device D-501.status = planned`
**And** пользователь в edit version изменил статус на `installed`
**And** другой пользователь уже изменил Default на `removed`
**When** пользователь запускает `Reconcile with Default`
**Then** система должна создать conflict
**And** показать base value, my value и current Default value

Ожидаемый conflict view:

```text
Feature: Device D-501
Field: status

Base value: planned
My value: installed
Default value: removed

Conflict type: Update/Update
```

Главная проверка:

> Конфликт не должен быть перезаписан молча.

---

## AC-07. Reconcile находит конфликт update/delete

**Given** пользователь изменил `Device D-501` в edit version
**And** тот же объект был удален из Default до post
**When** пользователь запускает reconcile
**Then** система показывает конфликт `Update/Delete`
**And** запрещает post до явного решения
**And** пользователь/reviewer должен выбрать: восстановить объект, принять удаление или выполнить manual merge

Ожидаемый результат:

```text
Conflict type: Update/Delete
Feature: D-501
My operation: Update
Default operation: Delete
Post allowed: false
```

---

## AC-08. Reconcile находит конфликт geometry/geometry

**Given** пользователь изменил геометрию `Line L-1001` в edit version
**And** другой пользователь уже изменил геометрию этой же линии в Default
**When** запускается reconcile
**Then** система показывает geometry conflict
**And** post блокируется до выбора версии геометрии
**And** audit log фиксирует выбранное решение

Минимальный acceptable вариант без сложного geometry diff:

```text
Conflict type: Geometry/Geometry
Feature: Line L-1001

Options:
- Use my geometry
- Use Default geometry
- Cancel and edit manually
```

---

## AC-09. Post невозможен при unresolved conflicts

**Given** после reconcile есть хотя бы один unresolved conflict
**When** пользователь или reviewer нажимает `Post to Default`
**Then** система возвращает ошибку
**And** authoritative state не меняется
**And** версия остается в статусе `Conflicted`

Ожидаемый ответ:

```text
Post rejected.
Reason: unresolved conflicts exist.
Unresolved conflicts: 1
Authoritative state changed: false
```

---

## AC-10. Reviewer approval обязателен перед публикацией

**Given** edit version прошла validation и reconcile
**When** Utility GIS editor нажимает `Post to Default`
**Then** система запрещает публикацию, если нет reviewer approval
**And** показывает статус `Waiting for review`

Ожидаемый результат:

```text
Post rejected.
Reason: reviewer approval required.
Current status: ReviewRequested
```

Для этой роли это важно: редактор готовит правку, но authoritative state должен обновляться контролируемо.

---

## AC-11. Reviewer видит полный diff перед approve

**Given** версия отправлена на review
**When** reviewer открывает review screen
**Then** он видит список измененных объектов
**And** видит изменения атрибутов
**And** видит изменения geometry/association
**And** видит validation status
**And** видит conflict resolution history

Минимальный экран:

```text
WorkOrder: WO-001
Version: V-WO-001-ALEXEY

Changed features:
1. Device D-501
   status: planned -> installed

Changed associations:
1. D-501 connected_to L-1001

Validation:
Passed

Conflicts:
1 resolved
0 unresolved
```

---

## AC-12. После approve post обновляет authoritative state атомарно

**Given** reviewer approved версию
**And** validation passed
**And** unresolved conflicts = 0
**When** выполняется `Post to Default`
**Then** все изменения применяются к authoritative state одной транзакцией
**And** если хотя бы одно изменение не применилось, откатывается весь post
**And** work order не получает статус `Completed`

Ожидаемый успешный результат:

```text
Post result: Success
Applied changes: 2
Authoritative state updated: true
WorkOrder status: Completed
Version status: Posted
```

Ожидаемый неуспешный результат:

```text
Post result: Failed
Applied changes: 0
Authoritative state updated: false
WorkOrder status: ReviewApproved
Version status: PostFailed
```

---

## AC-13. Если Default изменился после reconcile, post требует повторный reconcile

**Given** пользователь уже сделал reconcile
**And** reviewer approved версию
**And** другой пользователь изменил Default после reconcile, но до post
**When** выполняется post
**Then** система запрещает публикацию
**And** требует повторный reconcile
**And** authoritative state не меняется

Ожидаемый результат:

```text
Post rejected.
Reason: Default changed after last reconcile.
Required action: Reconcile again.
Authoritative state changed: false
```

Это один из самых важных критериев, потому что именно здесь часто появляется “у нас вроде работало, но данные потерялись”.

---

## AC-14. После успешного post read-only пользователь видит новое authoritative state

**Given** версия успешно posted
**When** read-only consumer открывает слой сети
**Then** он видит обновленные объекты из authoritative state
**And** не видит draft/change set
**And** данные соответствуют опубликованной версии

Пример:

```text
Read-only view:
Device D-501.status = installed
Association D-501 -> L-1001 exists
```

---

## AC-15. Audit trail показывает всю цепочку

**Given** work order прошел полный путь до authoritative state
**When** admin открывает audit log
**Then** он видит события:

```text
UserLoggedIn
WorkOrderOpened
EditVersionCreated
FeatureUpdated
AssociationCreated
TopologyValidated
ReconcileStarted
ConflictDetected
ConflictResolved
ReviewRequested
ReviewApproved
PostedToDefault
VersionClosed
```

Для каждого события должны быть:

```text
event_id
user_id
timestamp
work_order_id
version_id
feature_id
operation
old_value
new_value
```

Критерий:

> Через audit log можно восстановить, кто, когда и почему изменил сетевой объект.

---

## AC-16. Версия закрывается после успешного post

**Given** изменения опубликованы в Default
**When** post завершился успешно
**Then** edit version получает статус `Closed` или `Posted`
**And** пользователь больше не может редактировать эту версию
**And** повторный post той же версии невозможен

Ожидаемый результат:

```text
Version status: Posted
Can edit: false
Can post again: false
```

---

## AC-17. Повторный запрос post не создает дубликаты

**Given** post уже был выполнен успешно
**When** клиент случайно повторяет тот же запрос post
**Then** система не применяет изменения второй раз
**And** возвращает текущий статус версии
**And** authoritative state остается прежним

Ожидаемый результат:

```text
Post result: AlreadyPosted
Applied changes: 0
Duplicate associations created: 0
Duplicate features created: 0
```

---

## AC-18. Пользователь всегда видит статус своей правки

**Given** пользователь работает с work order
**When** он открывает экран задачи
**Then** система показывает один из понятных статусов:

```text
Draft
ValidationFailed
Validated
Reconciling
Conflicted
ReadyForReview
ReviewRequested
ReviewRejected
Approved
Posting
Posted
PostFailed
Closed
```

Критерий:

> Пользователь не должен гадать, его изменения еще draft или уже authoritative.

---

## AC-19. Synthetic dataset воспроизводит конфликт без закрытых данных

**Given** есть тестовый synthetic utility dataset
**When** запускается сценарий параллельного редактирования
**Then** можно воспроизвести минимум 4 конфликта:

```text
1. Attribute update/update
2. Geometry update/update
3. Update/delete
4. Association conflict
```

И для каждого конфликта система должна:

```text
detect conflict
block post
show diff
allow resolution
write audit log
```

Это важный acceptance criterion для пилота: тест можно показать без реальных закрытых данных.

---

# Сжатый набор DoD для walking skeleton

Walking skeleton считается готовым, если:

```text
1. Utility GIS editor входит в систему и видит назначенный work order.
2. Для work order создается отдельная edit version от Default.
3. Редактор меняет network feature и association без изменения authoritative state.
4. Система сохраняет изменения как change set с old/new values.
5. Topology validation блокирует review при ошибках.
6. Reconcile обнаруживает update/update конфликт с Default.
7. Unresolved conflict блокирует post.
8. Conflict можно разрешить явно: use mine, use Default или manual merge.
9. Reviewer видит diff и approve/reject.
10. Post в Default выполняется только после validation, reconcile и approve.
11. Если Default изменился после reconcile, post требует повторный reconcile.
12. После успешного post read-only пользователь видит новое authoritative state.
13. Audit log показывает всю цепочку от edit version до post.
14. Повторный post не создает дубликаты.
15. Закрытая версия больше не редактируется.
```

---

# Главный критерий

Критерий не такой:

```text
Пользователь может редактировать сеть.
```

А такой:

```text
Пользователь может безопасно подготовить сетевую правку в изолированной версии, пройти validation, обнаружить и разрешить конфликт с Default, получить review approval и опубликовать изменения в authoritative state без silent overwrite и с полным audit trail.
```

Самый главный проверочный критерий:

```text
Ни одна параллельная правка инженерной сети не теряется молча.
```
