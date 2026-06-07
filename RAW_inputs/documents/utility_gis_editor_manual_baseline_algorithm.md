# Utility GIS editor: алгоритм измерения ручного baseline

## Контекст

Для варианта использования `Utility GIS editor` ручной baseline — это текущее время, трудозатраты и качество процесса **без GeoService**, когда команда доводит `work order` до безопасного опубликованного состояния существующими инструментами и ручными проверками.

Baseline нужен не для того, чтобы измерить один клик или скорость отрисовки карты, а чтобы понять текущую стоимость полного безопасного workflow:

```text
получили work order
→ нашли нужный участок сети
→ внесли изменения
→ проверили topology/associations
→ сверили с нарядом
→ разобрали конфликты
→ получили review
→ сделали post
→ убедились, что не нужна аварийная коррекция
```

Главная идея:

> Ручной baseline должен измерять не скорость редактирования геометрии, а стоимость безопасного доведения изменения инженерной сети до authoritative state.

---

# 1. Что сравниваем

GeoService нужно сравнивать не с абстрактным ощущением “стало удобнее”, а с текущим ручным процессом.

Сравниваем полный путь:

```text
work order start
→ first edit
→ validation / manual check
→ reconcile / conflict handling
→ review
→ post to Default
→ 7-day correction window
```

---

# 2. Выбор work orders для baseline

Для первого замера достаточно:

```text
10–20 work orders
```

Желательно взять задачи разной сложности:

```text
low complexity
medium complexity
high complexity
```

## Low complexity

Примеры:

```text
изменение одного атрибута;
обновление статуса устройства;
исправление описания;
изменение, не влияющее на topology/trace.
```

## Medium complexity

Примеры:

```text
изменение геометрии линии;
изменение устройства и связанного атрибута;
создание или изменение association;
небольшой work order на 3–10 объектов.
```

## High complexity

Примеры:

```text
изменение участка сети;
несколько связанных линий и устройств;
изменение, влияющее на trace;
конфликт с другой версией;
обязательный reviewer approval.
```

---

# 3. Что фиксировать по каждому work order

Минимальный набор полей:

```text
work_order_id
complexity: low / medium / high
objects_changed_count
associations_changed_count
conflicts_count
validation_errors_count
review_errors_count
returned_to_editor: yes/no
manual_review_minutes
manual_reconcile_minutes
time_to_safe_post_minutes
post_problem_within_7_days: yes/no
post_problem_type
comments
```

---

# 4. Временные точки

По каждому work order нужно фиксировать timestamps.

## 4.1. Start time

Когда редактор получил work order.

```text
work_order_started_at
```

Пример:

```text
2026-06-07 09:15
```

---

## 4.2. First edit time

Когда началась фактическая правка сети.

```text
first_edit_started_at
```

Это показывает, сколько времени уходит на:

```text
поиск задачи;
поиск нужного участка;
открытие проекта;
ориентацию в данных;
подготовку к редактированию.
```

---

## 4.3. Save/edit completion time

Когда редактор закончил первичное внесение изменений.

```text
edits_completed_at
```

---

## 4.4. Validation / manual check time

Сколько времени ушло на проверку:

```text
topology;
associations;
connectivity;
trace;
dirty areas;
соответствия work order.
```

Фиксируем:

```text
validation_started_at
validation_completed_at
manual_validation_minutes
```

---

## 4.5. Reconcile / conflict handling time

Сколько времени ушло на:

```text
reconcile;
поиск конфликтов;
сравнение своей версии и Default;
выбор правильной версии;
повторный reconcile после исправлений.
```

Фиксируем:

```text
reconcile_started_at
reconcile_completed_at
manual_reconcile_minutes
conflicts_count
```

---

## 4.6. Review time

Сколько времени reviewer потратил на проверку.

Фиксируем:

```text
review_started_at
review_completed_at
manual_review_minutes
review_errors_count
returned_to_editor
```

---

## 4.7. Post time

Когда изменения попали в `Default` / `authoritative state`.

```text
posted_at
```

---

## 4.8. Correction window

Наблюдаем 7 дней после post.

Фиксируем:

```text
post_problem_within_7_days
post_problem_type
correction_minutes
```

---

# 5. Какие baseline-метрики получить

## 5.1. Manual Time to Safe Post

Показывает, сколько сейчас занимает путь от получения задачи до безопасного опубликованного состояния.

```text
Manual Time to Safe Post =
posted_at - work_order_started_at
```

---

## 5.2. Manual Review Time

Показывает стоимость контроля качества.

```text
Manual Review Time =
review_completed_at - review_started_at
```

---

## 5.3. Manual Reconcile / Conflict Time

Показывает боль совместного редактирования.

```text
Manual Reconcile Time =
reconcile_completed_at - reconcile_started_at
```

---

## 5.4. Manual Return Rate

Показывает, как часто reviewer возвращает задачи редактору на доработку.

```text
Manual Return Rate =
returned_work_orders
/
submitted_for_review
× 100%
```

---

## 5.5. Manual Rework Rate

Показывает качество после post.

```text
Manual Rework Rate =
posted_work_orders_with_correction_within_7_days
/
posted_work_orders
× 100%
```

---

## 5.6. Manual Review Error Count

Показывает, сколько ошибок reviewer находит до post.

```text
Manual Review Error Count =
количество ошибок, найденных reviewer'ом до post
```

Ошибки лучше классифицировать по severity:

```text
critical
high
medium
minor
```

---

## 5.7. Manual Touch Count

Показывает операционную сложность процесса.

Считаем количество ручных действий и переходов между инструментами:

```text
открыть проект;
найти объект;
сверить с нарядом;
переключиться в другой инструмент;
сделать скриншот;
экспортировать таблицу;
написать reviewer'у;
запустить ручную проверку;
сравнить версии;
повторить validation;
повторить reconcile.
```

---

# 6. Что обязательно считать ручной работой

В baseline нужно учитывать не только редактирование на карте, но и всю ручную работу вокруг безопасной публикации.

Считать как ручную работу:

```text
сверку с нарядом;
сравнение своей версии и Default;
ручной просмотр измененных объектов;
ручную проверку ассоциаций;
ручную проверку trace;
переписку с диспетчером;
переписку с полевой бригадой;
переписку с reviewer'ом;
повторный запуск validation после исправлений;
повторный reconcile;
ручную коррекцию после post;
экспорт/скриншоты/таблицы для проверки;
ручную проверку downstream-систем после публикации.
```

---

# 7. Что не смешивать с baseline

Не стоит смешивать в одну метрику:

```text
чистое время редактирования geometry;
время ожидания reviewer'а в очереди;
время согласования вне системы;
время полевого выезда;
время из-за внешних организационных задержек.
```

Но их можно фиксировать отдельно как комментарии.

Главное разделять:

```text
active work time
waiting time
external delay
```

---

# 8. Таблица наблюдения

Минимальный шаблон:

| Поле | Описание |
|---|---|
| `work_order_id` | Идентификатор задачи |
| `complexity` | `low`, `medium`, `high` |
| `objects_changed_count` | Сколько объектов изменено |
| `associations_changed_count` | Сколько связей изменено |
| `conflicts_count` | Сколько конфликтов найдено |
| `validation_errors_count` | Сколько ошибок validation найдено |
| `review_errors_count` | Сколько ошибок нашел reviewer |
| `returned_to_editor` | Был ли возврат на доработку |
| `manual_review_minutes` | Время review |
| `manual_reconcile_minutes` | Время reconcile/conflict handling |
| `time_to_safe_post_minutes` | Время от получения work order до post |
| `post_problem_within_7_days` | Была ли проблема после post |
| `post_problem_type` | Тип проблемы после post |
| `comments` | Комментарии наблюдателя |

---

# 9. Пример заполнения

```text
work_order_id: WO-001
complexity: medium
objects_changed_count: 6
associations_changed_count: 2
conflicts_count: 1
validation_errors_count: 2
review_errors_count: 1
returned_to_editor: yes
manual_review_minutes: 18
manual_reconcile_minutes: 12
time_to_safe_post_minutes: 74
post_problem_within_7_days: no
post_problem_type: none
comments: reviewer вернул из-за сомнительной association
```

---

# 10. Как потом сравнивать с GeoService

После внедрения прототипа GeoService те же work orders или аналогичные synthetic work orders прогоняются через новый workflow.

Сравнение должно быть таким:

```text
Manual Time to Safe Post: 45 мин → GeoService: 20 мин
Manual Reconcile Time: 15 мин → GeoService: 5 мин
Manual Review Time: 20 мин → GeoService: 10 мин
Manual Return Rate: 18% → GeoService: 10%
Manual Rework Rate: 7% → GeoService: 3%
Manual Touch Count: 30 действий → GeoService: 12 действий
```

---

# 11. Минимальный алгоритм измерения

```text
1. Выбрать 10–20 типовых work orders.
2. Разделить их по сложности: low / medium / high.
3. Для каждого work order зафиксировать start time.
4. Наблюдать фактическую работу editor'а.
5. Зафиксировать first edit time.
6. Зафиксировать время ручной validation/topology/trace проверки.
7. Зафиксировать время reconcile/conflict handling.
8. Зафиксировать время review.
9. Зафиксировать факт return на доработку, если он был.
10. Зафиксировать post time.
11. Наблюдать 7 дней после post.
12. Зафиксировать rollback/manual correction/rework, если они были.
13. Посчитать Manual Time to Safe Post.
14. Посчитать Manual Review Time.
15. Посчитать Manual Reconcile Time.
16. Посчитать Manual Return Rate.
17. Посчитать Manual Rework Rate.
18. Посчитать Manual Review Error Count.
19. Посчитать Manual Touch Count.
20. Использовать эти значения как baseline для сравнения с GeoService.
```

---

# 12. Итоговая формулировка

> Ручной baseline для `Utility GIS editor` измеряется на 10–20 типовых work orders как текущий путь от получения наряда до безопасного post в Default: время редактора, время reviewer'а, время reconcile/conflict-разбора, количество возвратов, review errors и доля аварийных коррекций в течение 7 дней после post.

Главное:

> Baseline должен измерять не скорость редактирования геометрии, а стоимость безопасного доведения изменения инженерной сети до authoritative state.
