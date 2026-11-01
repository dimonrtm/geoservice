# Журнал исполнения — план: docs/sprint_2/2026-11-01-inf-05-save-size-plan.md

Основание: принятый дизайн; пользователь поручил реализацию в текущем чате.
BASE: c85360f2c98548df9d24eabf9d857c860c801659. Ветка: first-edit-save.

- Ruling: работа в текущем checkout, журнал в Sprint 2 — принятый план и требование
  сохранять здесь артефакты; Git commits запрещены. Вместо commit-based helpers
  skill используется этот журнал и проверка unstaged diff. Стоимость ошибки:
  смешение изменений, поэтому исходный status зафиксирован и чужие файлы не заменяются.
- Pre-flight: задачи 1 и 2 используют общий runner; задача 2 добавляет fixture и
  browser workflow, proxy-only остаётся самостоятельным. Конфликтов интерфейсов нет.
- Docker доступен после sandbox escalation; Node v24.12.0, Docker 28.1.1.
- Задача 1: RED `geoservice-inf05-9a18a593`: 413 вместо 200 на обоих geometry cases,
  остальные контроли верны; exit 1, cleanup passed.
- Задача 1: GREEN `geoservice-inf05-9ad6b299`: 7/7 cases, exit 0, cleanup passed.
- Ruling: fixture сохраняет первые две исходные координаты, уплотняет дальнюю
  половину последнего сегмента — исходная L-003 имеет всего 3 точки, поэтому
  сохранение первых трёх плюс добавление после endpoint несовместимо с простотой
  и прежними endpoints. Проверяется доступность вершины 1 и доменные guards;
  стоимость ошибки — провал fixture, а не ослабление продукта.
- Задача 2: в работе; локальный runner использует текущий build context и `.dockerignore`.
- Задача 1: failure-path `geoservice-inf05-a8b2e141`: ожидаемый exit 1 после
  успешной matrix, cleanup passed.
- Задача 2: первый полный запуск `geoservice-inf05-471b2180` собрал production
  targets и подготовил БД. Диагностика pg_stat_activity показала >53 секунд
  на проверке соседних точек через повторный ST_PointN. Отменена только эта
  read-only проверка собственной БД; exit 1, cleanup passed. Проверка заменена
  на ST_DumpPoints + lag; условия валидности не ослаблены.
- Задача 2: запуск `geoservice-inf05-f25c0a15` прошёл подготовку fixture и дошёл
  до browser workflow, затем получил timeout ожидания маркера. Причина найдена:
  `workspaceLineInteraction.ts:23,120` разрешает ровно 3 вершины. Этот guard
  пропущен при исходном анализе и противоречит запланированной большой UI fixture.
  Продуктовые guards не изменялись. Полный browser proof не получен.
- Пользователю задан вопрос о корректировке приёмки: большой API/DB цикл через
  nginx + обычный browser cycle либо отдельное расширение UI.
- Задача 2: failure-path `geoservice-inf05-84d2a5f1` прошёл подготовку большой
  fixture, намеренно завершился exit 1; cleanup passed, включая отдельный DB volume.
- Пользователь выбрал узкий объём: большая линия проверяется настоящим API через
  nginx с БД; browser Save/Revert — на обычной линии. UI не расширяется.
- Ruling: фазы API и browser используют последовательно пересозданную собственную
  БД, чтобы не менять immutable baseline уже открытой версии. Цена — дополнительный
  seed/start; это сохраняет независимость доказательств двух сценариев.
- Полный run `geoservice-inf05-0752c577`: большой API Save/readback/replay/Revert/readback
  прошёл; 60 003 вершины, Save и Revert по 1 654 616 байт. Baseline и network hash
  неизменны. Обычный browser cycle остановился до Save на ожидании marker;
  запущен повтор с screenshot/DOM диагностикой. Задача 2 пока не закрыта.
- Независимое review: дефектов продукта нет. Important — завершить browser proof;
  Minor — cleanup при неизвестном аргументе и устаревшая формулировка плана.
  Проверка неизвестного аргумента: до исправления exit 1 и один лишний temp dir;
  после переноса validation перед mkdtemp — exit 1 и ноль новых каталогов.
  Найденный каталог теста удалён после проверки абсолютного пути. Текст плана исправлен.
- Final Ruling: UI больших линий, внешняя инфраструктура, нагрузочные пределы,
  buffering/timeouts, forced OS termination и CI, отложенные reviewer, остаются
  согласованными границами. Их отсутствие в проверке явно раскрывается; риск —
  локальный успех нельзя трактовать как валидацию этих сценариев. Пользовательские
  прежние review-документы меняются только в части статуса INF-05.
- Повтор `geoservice-inf05-09b38612`: API снова прошёл; screenshot/DOM обычной
  browser-фазы показали загруженную карту и отсутствие ошибок, но линия не выбрана.
  Вычисление click по текущему canvas предполагало fitBounds по его же размеру,
  хотя панель меняет высоту. Smoke теперь ищет линию реальными кликами в окрестности
  оценки и записывает найденное смещение; store/map API не подменяются.
  Добавлен ручной --browser-only для диагностики этой фазы, не для полной приёмки.
- Диагностика `geoservice-inf05-66ff8a99/map-target.json` уточнила причину:
  canvas снимался до появления панели (`y=229.39`, `height=739`), оценка клика
  была `[957.02,510.53]`; screenshot после панели показывает вершину около
  `[957,584]`. Ожидание одной видимости canvas недостаточно. Smoke теперь ждёт
  видимость Save (контракт FE-02 о готовности карты) до расчёта координат.
- GREEN browser-only `geoservice-inf05-f0052c25`: exit 0, Save/reload/Revert/reload,
  401/422, нет page errors, baseline/network неизменны, cleanup passed.
  Найденное смещение клика [-16,-16] записано в evidence. Функциональная правка
  только в smoke; nginx не менялся после первоначального GREEN.
- Итоговый запуск `& docs/sprint_2/verify-inf-05.ps1`:
  `geoservice-inf05-fc9eedcf`, exit 0, proxy 7/7, большой API Save/readback/replay/
  Revert/readback и обычный browser Save/reload/Revert/reload прошли. 401/422
  подтверждены, baseline/network обеих фаз неизменны, cleanup passed.
- Задачи 1–3: завершены. UTF-8/LF, Prettier, syntax checks и git diff --check
  пройдены. CI не изменён. Independent review замечания устранены; отложенных нет.
  Изменения оставлены unstaged, Git add/commit/push не выполнялись.
