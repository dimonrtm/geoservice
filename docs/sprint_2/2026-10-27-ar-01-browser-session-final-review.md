# AR-01: итоговый обзор всей интеграции

Дата: 2026-10-28. Reviewer: /root/ar01_final_review.

Итог после исправлений: оба Minor ниже устранены одной волной и проверены отдельным scoped re-review; открытых замечаний нет. Исходный текст общего обзора сохранён, закрытие замечаний приведено в конце.

Основание: принятый `docs/sprint_2/2026-10-27-ar-01-browser-session-design.md`, план, implementation report и `docs/sprint_2/evidence/ar-01/verification.md`. Base/HEAD: `615ccef7f86a8b686da8e4cf3fafd0c677295f24`; предмет обзора — unstaged tracked delta и новые файлы из `final-review-diff.md`, а не пустой committed range.

Обзор выполнен проходами по production backend/frontend, интеграционным границам, существенным unit/DB/browser тестам, миграции, harness и документации. Особое внимание: отсутствие доступа после отзыва, независимость другого sid, поздние ответы, свежесть resume-проверки, сохранность отправленной команды и достоверность acceptance outcome. Полные suites не повторялись; результаты ниже взяты из сохранённого evidence, а не заявлены как собственный новый прогон. В ходе обзора отдельно выполнены read-only `git diff --check`, проверка пустого staged diff и HEAD — без ошибок/изменения Git-состояния.

## Strengths

- **Серверный отзыв имеет согласованную точку линеаризации.** Refresh перечитывает credential и время после parent lock; replacement login и logout используют тот же порядок блокировок. Отозванный parent не продлевается. См. `apps/backend/utility_service/use_cases/services/auth_session_service.py:101`, `apps/backend/utility_service/use_cases/services/auth_session_access_service.py:161`. DB race tests действительно наблюдают PostgreSQL blocking и проверяют оба порядка refresh/logout, rollback и единственного winner refresh/refresh.
- **Proof не смешивает разные права.** Access требует действительного JWT и активного владельца/parent; status допускает expired JWT только для собственного sid; matching cookie является независимым proof. Logout не возвращает Set-Cookie. Короткие auth transactions и `populate_existing=True` исключают прежний ORM snapshot из следующей проверки. См. `apps/backend/utility_service/use_cases/services/auth_session_access_service.py:65`, `apps/backend/utility_service/infrastructure/postgresql/repositories/browser_auth_session_repository.py:44`.
- **Realtime привязан к тому же sid.** Ticket consume проверяет parent, manager повторяет свежую проверку admission/send; закрытие соединений ограничено по времени и не откатывает commit logout. Уже допущенные действия отделены от новых, граница single worker явно описана. См. `apps/backend/utility_service/use_cases/services/realtime_connection_manager.py:40`.
- **Разные виды актуальности разделены.** Web Lock сериализует cookie mutations; durable revision защищает намерение; `restoreGeneration` защищает продолжение restore; `sessionEpoch` меняется при новом sid даже того же actor. Resume generation и `requireFreshRequest` препятствуют использованию status, начатого до resume, сохраняя один HTTP status на вкладку. См. `apps/frontend/src/auth/browserSessionCoordinator.ts:123`, `apps/frontend/src/auth/browserSessionMonitor.ts:96`, `apps/frontend/src/api/auth.ts:110`, `apps/frontend/src/stores/auth.ts:284`.
- **Подготовка выхода сохраняет identity отправленного намерения.** `prepareActorLogout` проверяет durable command без преждевременной suspension; workspace блокируется на время попытки, неотправленный logout оставляет контекст, подтверждённая потеря доступа запускает прежние recovery guards. См. `apps/frontend/src/stores/workspaceRecovery.ts:450`, `apps/frontend/src/stores/workOrders.ts:615`.
- **Миграция и evidence учитывают последствия выпуска.** Composite FK связывает credential/ticket с владельцем parent; upgrade/downgrade завершают credentials, тест сравнивает бизнес-данные до/после. Runbook требует согласованного выпуска и смены JWT secret при возврате к старому backend. Реальные браузерные проверки не подменяют backend rotation mock-ответами; последнее исправление harness запрещает false PASS после аварии setup/cleanup/persist.

## Issues

### Critical (Must Fix)

Не обнаружены.

### Important (Should Fix)

Не обнаружены. Существенных отступлений production-реализации от принятого дизайна в проверенных связях не найдено.

### Minor (Nice to Have)

1. **Неограниченное ожидание сигнала может подвесить acceptance и отложить cleanup.**
   - Файл: `docs/sprint_2/ar-01/smoke.mjs:372`; такие же `entered.promise` на строках 542, 594, 864, а также `observed.promise` на строке 550.
   - Если нужный запрос/ответ перестанет происходить, либо route handler упадёт до `resolve`, await не завершится. Playwright assertion timeout не распространяется на обычный Promise; `acceptance()` вызывается из `run.mjs` напрямую, поэтому timeout subprocess helper его также не ограничивает.
   - Это ухудшает диагностику будущей регрессии и оставляет disposable Compose environment до ручного завершения. Текущие завершённые успешные manifests этим не опровергаются; product-поведение не затронуто.
   - Исправление: bounded ожидание сигналов с безопасным сообщением об ошибке и гарантированным освобождением удерживаемых route barriers. Проверить коротким focused тестом, что отсутствующий сигнал приводит к failed outcome и выполнению cleanup, без повторения всех browser suites.

2. **Старое объяснение same-actor epoch противоречит новому sid-контракту.**
   - Файл: `Code_wiki/архитектура/frontend.md:64`.
   - Фраза о новом входе того же actor, при котором `sessionEpoch` может не измениться, больше не описывает успешный replacement login: он получает новый sid, а `setAuth` повышает epoch. Ниже, на строках 76–77, уже дано верное правило.
   - Противоречие может привести следующего разработчика к неверному выбору stale guard.
   - Исправление: объяснить, что `restoreGeneration` нужен для инвалидирования попытки до её завершения, в том числе при неуспешном login; успешный новый sid меняет epoch, refresh прежнего sid — нет. Согласовать два соседних абзаца.

Оба замечания совпадают с переданными deferred minor; новых дефектов сверх них не выявлено. Прежний minor про `expires_at` отозванного parent исправлен и включён в focused PostgreSQL evidence.

## Recommendations

- Устранить два minor одной небольшой правкой; проверять только изменённую логику harness и согласованность текста, без повторения неизменённых полных suites.
- При закрытии плана обновить финальные статусы/checklist и сохранить ограничения evidence. Сейчас документы честно помечают итоговый review как ожидающий; это ожидаемая работа контроллера после данного отчёта, не отдельный дефект.
- Не смешивать исходные предупреждения passlib/crypt, AnyIO/Starlette и frontend chunk size с регрессиями AR-01. Новых dependency-изменений для их устранения этот обзор не рекомендует.

## Evidence и пределы проверки

Сохранённое evidence сообщает: frontend 438 tests, typecheck/lint/build PASS; backend 675 standard tests и отдельный DB lane 310 passed/0 skipped; focused PostgreSQL delta 18 passed; browser основной прогон 36/36, history 3/3 и дополнительные SLA cases 6/6; focused исправление acceptance outcome 7/7. Результаты и происхождение описаны в `docs/sprint_2/evidence/ar-01/verification.md` и `backend-final-checks.md`.

Измеренные dispatch → login соседней вкладки значения укладываются в 5 секунд; такая метрика консервативна относительно commit → UI. Максимальная параллельность status в browser evidence равна 1; protected requests до fresh resume gate — 0. Firefox — Playwright patched build, Chrome/Edge — установленные branded channels. Последнее изменение lifecycle helper отдельно проверено focused regression; прежние browser manifests относятся к своим runner hashes. Это достаточное основание для технического verdict в принятом объёме, но не заявление о повторном исполнении всего пакета reviewer-ом.

## Declined to judge

- Native BFCache с сохранением прежнего JavaScript runtime и OS suspend: имеющееся evidence этого не доказывает. Требуемую интеграцию resume guard я оценил по коду, lifecycle injection с реальным status и настоящему history back; отдельный native gate не был согласованным требованием. Не объявляю его пройденным и не добавляю новый blocker.
- Немедленное закрытие WebSocket во всех процессах, распределённый broker и AR-02: явно вне принятой single-worker границы; свежие admission/send checks в текущем объёме рассмотрены.
- Нагрузочная ёмкость polling, внешнее HTTPS production deployment, мобильные/старые браузеры и stock Firefox вне проверенного build: не подтверждены текущим локальным evidence; они не входят в выполненные gates и не выдаются за проверенные свойства.
- Глобальный logout пользователя, технический WorkOrder lock, offline mode, автосохранение dirty и автоматический replay mutation после login: явно исключены дизайном; их отсутствие не считается дефектом. Сохранность sent identity и действующие stale guards проверены в текущем объёме.
- Гарантированное сохранение нового cookie при произвольном позднем Set-Cookie после сетевой неопределённости: дизайн допускает повторный login при фактической потере credential. Проверены sid fencing и запрет восстановления отозванного входа; новая гарантия порядка cookie не требуется.
- Исправление исходных warnings и иных неизменённых технических проблем репозитория: не относится к AR-01; не классифицировано как новая регрессия.

## Assessment

**Ready to merge? Yes — технически, с двумя неблокирующими minor.** Это verdict готовности изменения к пользовательскому review, а не разрешение агенту выполнять Git-операции.

**Reasoning:** Реализация согласует sid, revoke/rotation, browser coordination, freshness и workspace recovery; сохранённые DB/browser evidence покрывают существенные гонки и отрицательные сценарии. Блокирующих дефектов в проверенной интеграции не обнаружено; замечания касаются устойчивости будущего acceptance-прогона и непротиворечивости wiki.

Checkout/index/HEAD не изменялись, кроме этого отдельно разрешённого отчёта. Agent memory не обновлялась: причины решений уже сохранены дизайном, runbook и Code_wiki; review findings принадлежат этому отчёту.

## Закрытие замечаний — 2026-10-28

Оба замечания получили ADDRESSED в scoped re-review /root/ar01_final_fix_review; новых дефектов не найдено. Signal waits ограничены 15000 ms, все удерживаемые route barriers освобождаются в finally до context cleanup. Текст frontend wiki согласован с новым sid/epoch контрактом.

Focused verification: `node --test docs/sprint_2/ar-01/acceptanceResult.test.mjs docs/sprint_2/ar-01/acceptanceSignals.test.mjs` — 10 passed, 0 failed/cancelled/skipped. Syntax, локальный Prettier, diff-check и UTF-8/LF прошли. Application production не менялся; прежние browser manifests сохраняют исходные hashes и не выдаются за новый прогон. Git add/commit/push не выполнялись.
