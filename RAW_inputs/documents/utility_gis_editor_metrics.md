# Utility GIS editor: North Star metric и вторичные метрики

## Контекст

Для варианта использования `Utility GIS editor` успех нельзя измерять только количеством edits или скоростью сохранения объекта.

Этот сценарий связан с редактированием инженерной сети, где пользователь проходит полный путь:

```text
work order
→ named/edit version
→ edit
→ validation / topology check
→ reconcile with Default
→ conflict resolution
→ post to Default
→ authoritative state
```

Поэтому главная метрика должна показывать не просто активность пользователя, а безопасное доведение изменений до официального состояния данных.

---

# 1. North Star metric

## Safe Authoritative Post Rate

**Формулировка:**

> Доля work orders, которые прошли `edit → validation → reconcile → conflict resolution → post in Default` без потери данных, unresolved conflicts, rollback и ручной аварийной сверки.

Короткое название:

```text
Safe Authoritative Post Rate
```

---

## Почему именно эта метрика

Для `Utility GIS editor` успех — это не просто:

- открыть карту;
- сделать edit;
- нажать Save;
- увеличить количество правок.

Настоящая ценность появляется только тогда, когда изменение инженерной сети:

1. сохранено в рабочей версии;
2. прошло validation;
3. не сломало topology;
4. прошло reconcile с Default;
5. не оставило unresolved conflicts;
6. было опубликовано через post;
7. не потребовало последующего rollback или ручного исправления.

Иначе можно получить ситуацию, где edits много, но authoritative network layer стал менее надежным.

---

## Формула North Star metric

```text
Safe Authoritative Post Rate =
Количество work orders, успешно опубликованных в Default без проблем
/
Общее количество work orders, начатых в GeoService
× 100%
```

---

## Work order считается успешно опубликованным, если

1. Edits сохранены в рабочей версии.
2. Validation прошла успешно.
3. Dirty areas закрыты.
4. Reconcile выполнен.
5. Все conflicts разрешены.
6. Post в Default прошел.
7. В течение контрольного окна, например 7 дней, не было:
   - rollback;
   - ручной аварийной правки;
   - повторной сверки из-за ошибки;
   - исправления topology/trace после публикации.

---

## Пример расчета

```text
За неделю начато 100 work orders.

Из них:
- 82 дошли до post в Default;
- 5 были опубликованы, но потом потребовали ручного исправления;
- 8 зависли на validation;
- 3 зависли на conflicts;
- 2 отменены.

Safe Authoritative Post Rate = 77 / 100 × 100% = 77%
```

Почему `77`, а не `82`?

Потому что 5 work orders формально были опубликованы, но качество публикации оказалось плохим.

---

# 2. Обязательные вторичные метрики

Вторичные метрики нужны, чтобы объяснять, почему North Star metric растет или падает.

Для `Utility GIS editor` я бы зафиксировал 5 обязательных вторичных метрик.

---

## 2.1. Time to Safe Post

**Что измеряет:** сколько времени занимает путь от открытия `work order` до успешного `post` в `Default`.

```text
Time to Safe Post =
timestamp(successful_post) - timestamp(work_order_opened)
```

---

### Почему обязательна

North Star metric показывает долю успешно опубликованных задач, но не показывает, насколько долго пользователь до них добирается.

Если `Safe Authoritative Post Rate` высокий, но `Time to Safe Post` слишком большой, значит система безопасная, но неудобная и медленная.

---

### Что считать

```text
P50 Time to Safe Post
P95 Time to Safe Post
Time from first edit to validation
Time from validation to reconcile
Time from reconcile to post
```

---

### Хороший ориентир

Для реального процесса:

```text
P50 <= 15 минут для малого work order
P95 <= 60 минут для сложного work order
```

Для MVP на synthetic dataset:

```text
P95 от первого edit до post <= 5 минут
```

---

## 2.2. Validation Pass Rate

**Что измеряет:** долю work orders, которые проходят validation без критических ошибок topology/network rules.

```text
Validation Pass Rate =
work orders with successful validation
/
work orders where validation was started
× 100%
```

---

### Почему обязательна

Для utility-сети важно не просто сохранить geometry/attributes, а не сломать:

- связность;
- topology;
- associations;
- network rules;
- trace-возможность.

Если пользователь часто сохраняет edits, но validation постоянно падает, значит редактор позволяет легко создавать неверное состояние сети.

---

### Что считать дополнительно

```text
Dirty areas count per work order
Topology errors per work order
Association errors per work order
Repeated validation attempts per work order
Validation failure reasons
```

---

### Плохой сигнал

```text
Пользователь сохраняет edits, но validation часто падает.
```

Это значит, что проблема может быть в UX редактирования, правилах валидации, подсказках или качестве исходных данных.

---

## 2.3. Conflict Resolution Rate

**Что измеряет:** насколько успешно пользователи проходят `reconcile` и разбирают конфликты.

```text
Conflict Resolution Rate =
resolved conflicts
/
detected conflicts
× 100%
```

---

### Почему обязательна

Branch/edit versions изолируют правки, но конфликт проявляется на `reconcile/post`.

Если конфликт нельзя понятно разобрать, пользователь:

- застрянет перед публикацией;
- выберет неправильную версию;
- передаст проблему reviewer/admin;
- начнет обходить систему вручную.

---

### Что считать дополнительно

```text
Average conflicts per reconcile
P95 time to resolve conflict
% unresolved conflicts
% conflicts escalated to reviewer/admin
Conflict type distribution
```

Типы конфликтов:

```text
attribute/update conflict
geometry/update conflict
update/delete conflict
conflict by object
conflict by attribute
```

---

### Хороший ориентир

```text
>= 95% конфликтов разрешаются без ручного вмешательства администратора
```

---

## 2.4. Post Failure / Reconcile Retry Rate

Эту метрику лучше считать в двух частях.

---

### Post Failure Rate

**Что измеряет:** как часто `post` не проходит.

```text
Post Failure Rate =
failed post attempts
/
all post attempts
× 100%
```

---

### Reconcile Retry Rate

**Что измеряет:** как часто пользователю нужно повторять reconcile перед post.

```text
Reconcile Retry Rate =
work orders requiring repeated reconcile
/
work orders that reached post stage
× 100%
```

---

### Почему обязательна

В versioned workflow возможна ситуация:

1. пользователь сделал reconcile;
2. другой пользователь успел изменить Default;
3. первый пользователь пытается сделать post;
4. система должна отказать и потребовать повторный reconcile.

Это нормальный защитный механизм.

Но если такое происходит часто, значит:

- пользователи слишком часто конкурируют за одни и те же объекты;
- рабочие версии слишком долго живут;
- AOI плохо разделены;
- workflow не помогает избежать пересечений;
- post происходит слишком поздно.

---

### Плохой сигнал

```text
Post Failure Rate > 5–10%
```

Это значит, что пользователи слишком часто сталкиваются с изменившимся Default перед публикацией.

---

## 2.5. Rework / Manual Correction Rate

**Что измеряет:** сколько опубликованных work orders потом пришлось исправлять вручную.

```text
Rework Rate =
posted work orders requiring manual correction within 7 days
/
posted work orders
× 100%
```

---

### Почему обязательна

Это главная guardrail-метрика качества.

Можно успешно пройти:

```text
save → validation → reconcile → post
```

Но через день обнаружить, что:

- trace работает неправильно;
- объект потерял связь;
- association неверная;
- topology формально прошла, но сеть стала некорректной;
- reviewer или downstream-потребитель нашел ошибку;
- бригада сообщает, что опубликованное состояние не соответствует факту.

---

### Что считать как rework

```text
rollback после post
ручная аварийная правка
повторное открытие work order из-за ошибки данных
исправление trace/topology проблемы после публикации
ручная сверка с нарядом из-за недоверия к данным
```

---

### Хороший ориентир

```text
Rework Rate <= 2–5%
```

---

# 3. Итоговый набор метрик

## North Star metric

```text
Safe Authoritative Post Rate
```

Доля work orders, которые безопасно дошли до authoritative state.

---

## Обязательные вторичные метрики

```text
1. Time to Safe Post
   Время от открытия work order до успешного post в Default.

2. Validation Pass Rate
   Доля задач, прошедших validation/topology check без критических ошибок.

3. Conflict Resolution Rate
   Доля обнаруженных конфликтов, которые были успешно и понятно разрешены.

4. Post Failure / Reconcile Retry Rate
   Частота неудачного post и повторного reconcile из-за изменившегося Default.

5. Rework / Manual Correction Rate
   Доля опубликованных задач, которые потом потребовали ручного исправления.
```

---

# 4. Если оставить только 3 вторичные метрики

Если нужно оставить только 3 самые важные вторичные метрики, я бы выбрал:

```text
1. Time to Safe Post
2. Validation Pass Rate
3. Rework / Manual Correction Rate
```

Почему именно они:

- `Time to Safe Post` показывает скорость доведения работы до результата.
- `Validation Pass Rate` показывает, насколько хорошо система помогает не ломать сеть.
- `Rework / Manual Correction Rate` показывает реальное качество после публикации.

---

# 5. Как эти метрики покрывают workflow

```text
Открытие задачи       → Time to Safe Post
Редактирование        → Save/Edit вспомогательные latency-метрики
Validation            → Validation Pass Rate
Reconcile             → Conflict Resolution Rate
Post                  → Post Failure / Reconcile Retry Rate
После публикации      → Rework / Manual Correction Rate
Authoritative outcome → Safe Authoritative Post Rate
```

---

# 6. Что не должно быть North Star metric

## Количество edits

Плохая главная метрика, потому что можно сделать много edits и при этом сломать сеть.

```text
Много edits ≠ успешная инженерная сеть
```

---

## Время сохранения edit

Важная техническая метрика, но не North Star.

```text
Быстро сохранить неправильную сеть ≠ успех
```

Ее лучше держать как performance guardrail:

```text
Save single edit <= 2 sec P95
Validation <= 15 sec P95
Reconcile <= 10–20 sec P95
Post <= 15 sec P95
```

---

## Количество пользователей

Тоже не подходит как главная метрика.

Пользователей может быть много, но если они не доводят work orders до безопасной публикации, продукт не решает главную задачу.

---

# 7. Финальная формулировка

> Для `Utility GIS editor` North Star metric — это `Safe Authoritative Post Rate`: доля work orders, которые были безопасно доведены от edit до post в Default с успешной validation, resolved conflicts и без последующей ручной аварийной коррекции.

> Обязательные вторичные метрики: `Time to Safe Post`, `Validation Pass Rate`, `Conflict Resolution Rate`, `Post Failure / Reconcile Retry Rate`, `Rework / Manual Correction Rate`.

Такой набор покрывает весь рискованный путь `Utility GIS editor`:

```text
скорость
→ корректность сети
→ конфликты
→ публикация
→ качество после публикации
```
