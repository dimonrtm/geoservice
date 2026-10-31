# AR-01: отчёт реализации сессии браузера

Дата артефактов: 2026-10-27. Фактическая проверка: 2026-10-28, Asia/Qyzylorda.
Статус: реализация и локальные gates выполнены; итоговый review и re-review исправлений пройдены без открытых замечаний.
Изменения оставлены unstaged. Пользователь выполняет review, staging и commit.

## Результат

Стабильный sid объединяет JWT, одноразовые refresh generations и WebSocket
tickets одного входа. Logout commit немедленно запрещает новые проверки этого
sid, сохраняя другие входы того же пользователя. Web Locks сериализует auth
HTTP вкладок; marker/BroadcastChannel/status сводят их UI. Logout не меняет
cookie и не очищает workspace до подтверждения. Resume требует свежей status
проверки; поздние ответы старого sid не меняют новый вход.

Managed logout проверяет durable sent identity и временно блокирует новые
локальные действия инициатора. External ended приостанавливает workspace без
dirty autosave. Старые frozen команды остаются за access barrier; login не
повторяет mutation автоматически. WorkOrder lock, global logout, replay grace,
AR-02 и общий рефакторинг workOrders не добавлены.

Миграционный порядок и эксплуатационные ограничения — [runbook](2026-10-27-ar-01-browser-session-runbook.md).
Спецификация — [дизайн](2026-10-27-ar-01-browser-session-design.md).

## Настоящие браузеры и изоляция

Использован существующий `@playwright/test` 1.64.1 из `infra/m4`; production
frontend/nginx, проверенный production backend image и отдельная tmpfs
PostgreSQL/PostGIS. Уникальные Compose projects, loopback ports, случайные
credentials в памяти, чистые frontend build contexts и временные profiles.
Рабочие demo volumes и пользовательские profiles не использовались.

| Browser | Фактическая версия | Executable |
| --- | --- | --- |
| Installed Chrome, channel `chrome` | 156.0.8078.48 | `C:/Program Files/Google/Chrome/Application/chrome.exe` |
| Installed Edge, channel `msedge` | 156.0.4314.42 | `C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe` |
| Playwright patched Firefox, revision1555 | 157.0 | `C:/Repositories/geoservice/.tmp-tests/ar01-browsers/firefox-1555/firefox/firefox.exe` |

Firefox — реальный отдельный Gecko engine, не Chromium и не установленный
stock Firefox. [Официальная документация](https://playwright.dev/docs/browsers#firefox)
указывает на patches Playwright и отсутствие поддержки branded Firefox binary.
Браузеры запускались headless, с собственными temporary profiles.

Network interception задерживает/теряет настоящие ответы backend. Rotation
всегда выполняется сервером на PostgreSQL; mock auth/rotation и production
debug endpoints отсутствуют. Proxy использует Node fetch в памяти: Playwright
`route.fetch` сам применяет Set-Cookie через shared APIRequestContext, поэтому
для проверки потерянного credential он не подходит.

## Browser evidence

Основной прогон: [verification.json](evidence/ar-01/geoservice-ar01-d19c8b14/verification.json),
12 cases × 3 браузера, все 36 PASS. Дополнение настоящего history resume:
[verification.json](evidence/ar-01/geoservice-ar01-2650573a/verification.json),
1 case × 3, все PASS. Уточнение консервативного SLA:
[verification.json](evidence/ar-01/geoservice-ar01-fa950f3c/verification.json),
2 cases × 3, все PASS. Дополнения содержат runner SHA-256 и явный `scope`.
Охвачены 13 различных cases в каждом из трёх браузеров; timing supplement
повторяет только две проверки, не создаёт новые сценарии.

| Сценарий | Подтверждённый результат во всех трёх браузерах |
| --- | --- |
| Две одновременные reload/restore, новая вкладка | Две реальные ротации сохраняют sid; обе вкладки работают |
| Закрытие инициатора после server rotation | Auth lock освобождается; при потерянном credential требуется явный login, после него работа восстанавливается |
| Logout, два pages, независимый context и другой browser | Соседняя вкладка показывает login; другой sid того же user остаётся 200 |
| Скопированные в память JWT/refresh/ticket | После commit access 401, refresh 401, неиспользованный ticket не допускается к WebSocket |
| Потерянный marker и отсутствие BroadcastChannel | Реальный status сводит UI; старый active ответ задержан на 1100 ms |
| Resume при pre-resume active status | Новый status выполняется до protected action; защищённых requests до допуска — 0; одновременно status — 1 |
| Настоящий history back после remote logout | Login, защищённых requests — 0; BFCache не использован |
| Потеря logout до backend через abort | Auth и открытый workspace сохраняются; клиент корректно считает network outcome неопределённым |
| Достоверно недоставленный logout: lock timeout | 30 s ожидание, logout HTTP — 0; auth сохраняется с failed сообщением |
| Commit logout с потерянным ответом | Status подтверждает ended, автоматического повторного logout нет |
| Старый logout после нового login | Новый sid/cookie не затронуты, reload успешно восстанавливает новый вход |
| Lost rotated response | Старый credential отвергается; явный login восстанавливает работу без replay grace |
| FE-01 retry и поздний настоящий Set-Cookie | Retry удерживает экран ожидания; поздняя cookie может перезаписать текущую, но revoked sid не устанавливается; явный login восстанавливает credential |
| Web Locks отсутствует | Refresh HTTP — 0, явный retry/error screen |
| Один WorkOrder в двух вкладках | Два независимых drafts; после первого Save второй получает 409 `DRAFT_VERSION_STALE`, Save disabled; первый Revert возвращает fixture |

Последние строки группируют отдельные ветви внутри cases: таблица не является
подсчётом различных runner cases.

SLA измерен консервативно **от начала UI dispatch logout** до наблюдаемого login
UI другой вкладки. Commit не может предшествовать dispatch, поэтому это верхняя
граница commit → UI, включающая ожидание UI/lock/HTTP. Старый показатель
response → UI сохранён отдельно в основном evidence и не выдаётся за commit-time.

| Browser | Обычный logout, dispatch → login | Потерянный marker + старый active, dispatch → login | Max одновременно status |
| --- | ---: | ---: | ---: |
| Chrome | 1994 ms | 2647 ms | 1 |
| Edge | 1976 ms | 3036 ms | 1 |
| Firefox | 161 ms | 2549 ms | 1 |

Все измерения ниже 5000 ms. Реальное ожидание auth lock в основном прогоне:
Chrome 30898 ms, Edge 31869 ms, Firefox 30170 ms; сверх 30000 ms входит browser
action/assertion overhead. Принудительного захвата lock и logout HTTP не было.

## Найденный и исправленный production дефект

Browser lock timeout выявил неверное сообщение достоверно недоставленного
logout. До входа в callback coordinator выбрасывал `AuthCoordinationError`,
который общий parser относил к unknown; catch ошибочно запускал reconciliation
и показывал «Не удалось подтвердить выход», хотя logout HTTP не начинался.
Воспроизведение: [RED browser evidence](evidence/ar-01/geoservice-ar01-1f5a62d9/chrome/browser.json),
case `auth_lock_timeout_known_undelivered_logout`: requests=0,
uncertainMessage=true, authRetained=true.

После согласования добавлен локальный `logoutStarted` fence: true ставится
непосредственно перед `logoutSession`. До него ошибка достоверно недоставлена;
после него прежние network/timeout/unknown/401 правила uncertain сохранены.
Ошибка такого же типа после dispatch всё ещё требует reconciliation.
Поглощение marker publication error после успешного server commit сохранено.

TDD: `auth.multitab.test.ts` RED — 1 failed/14 passed (неверный summary);
focused GREEN auth/logout/monitor — 25/25. Browser real 30 s timeout затем PASS
во всех трёх браузерах. Это единственный production delta Task8, backend не менялся.

## Регрессионные проверки и PostgreSQL

| Проверка | Итог |
| --- | --- |
| Final frontend `npm test` | 52 files, 438 passed, 53.50 s, exit 0 |
| `npm run typecheck` | PASS |
| `npm run lint` | PASS |
| `npm run build` | PASS; baseline warning chunk >500 kB |
| Локальный Prettier всех изменённых TS/Vue, tracked + untracked | 26 files, PASS |
| Node syntax checks runner | PASS |
| Backend полный Black/Ruff/pytest/prod build | PASS, [evidence контроллера](evidence/ar-01/backend-final-checks.md) |
| Штатный `infra/db-tests.cmd` | 310 passed, 0 skipped; clean/legacy migration и downgrade, cleanup PASS |
| Focused PostgreSQL repository + races с новым deferred assertion | 18 passed, 0 skipped, ~8.8 s на fresh отдельной `_test` БД |
| Black/Ruff единственного изменённого backend test | PASS |
| Wiki lint после ingest/correction | Только 37 прежних `missing_frontmatter` в неизменённых RAW; новых ошибок нет |

SQL races реально проверяют refresh/refresh с одним winner, оба порядка
refresh/logout без активного потомка, rollback неудачной rotation/login,
переоценку parent/user/time после lock, ожидаемый sid и старую историю cookie.
Дополнительный repository assert подтверждает неизменный `expires_at` после
попытки продлить отозванного parent. Оптимистический stale guard WorkOrder не
отключался. Полные backend lanes не повторялись после неизменённого production
backend; перенесено проверенное контроллером evidence, focused delta проверен заново.

Warnings сохранены: backend passlib/crypt; в свежем full DB image Starlette/AnyIO
deprecated alias; frontend build большой chunk. npm печатал собственное
уведомление об обновлении CLI. Эти исходные предупреждения не исправлялись
изменением зависимостей или посторонних файлов.

## Ограничения и неудачные промежуточные запуски

Fresh-resume проверка использует injected `pageshow.persisted` в настоящем
document, настоящие HTTP/status и реальные guards. Дополнительный настоящий
history back пересоздал document: `bfcacheRestored=false` во всех браузерах.
OS suspend/native BFCache прежнего JavaScript runtime этим не подтверждены.
Headless `bringToFront` оставлял оба pages visible. Одна диагностическая попытка
отключить Playwright `--disable-back-forward-cache` на disposable static page
завершилась Playwright `goBack` timeout ожидания load; это не product failure и
не успешный frozen-resume gate. Дополнительного подбора среды не выполнялось.

Остальные границы: desktop localhost вместо внешнего HTTPS, single worker для
немедленного active WS close, отсутствие нагрузочного/production deployment
прогона. Эти ограничения не скрыты как successful real production validation.

Промежуточные manifests сохранены: sandbox subprocess failure; `_test` suffix и
PostGIS extension setup; harness side effect route.fetch; неверные runner stale
method/code и async response capture; RED lock-timeout defect; supplemental tmpfs
inspection через `.Mounts` вместо `.HostConfig.Tmpfs`. Все после первого sandbox
сбоя собственные Compose projects очищены. Первый sandbox запуск не создал
Docker resources; его cleanup не был подтверждён инструментом. `npx prettier`
из корня ошибочно попытался обратиться к registry и завершился cache EEXIST;
использован установленный локальный Prettier, dependencies не менялись.

## Знание, статус и приватность

Repository-change ingest создал [browser_auth_sessions](../../Code_wiki/архитектура/browser_auth_sessions.md).
Отдельно зарегистрирован `FU-2026-10-28-001`, затем post-ingest correction
обновила только auth-факты трёх Code_wiki нод; follow-up разрешён. Доменные Wiki,
DDD_Wiki, RAW и прежняя история не менялись. Agent memory не дублировалась:
устойчивые причины и ограничения сохранены кодом, runbook и Code_wiki.

Evidence содержит только статусы, booleans, counts, timings, версии, paths и
hashes. Raw tokens/cookie/password/ticket/body/HAR/trace не сохранялись.
Итоговые `git diff --check`, UTF-8/LF и privacy/diff проверки отражены в
[сводке evidence](evidence/ar-01/verification.md). Checklist всех восьми задач
закрыт после review; отдельный итоговый обзор сохранён по ссылке ниже.

Review correction 2026-10-28: устранён false PASS при аварии acceptance runner
после уже успешного case. Общий lifecycle фиксирует `completed/aborted`, а
исключения setup/cleanup/persist принудительно делают browser outcome failed;
Compose catch не доверяет stale `passed: true` JSON после исключения. Focused
Node regression: RED 5 failed/2 passed → GREEN 7/7. Application production и
browser actions не менялись, полные suites не повторялись. Ранее завершённые
browser manifests не опровергнуты; их hashes относятся к исполненным тогда
runner versions. Подробности — в сводке evidence.

Final review correction 2026-10-28: ожидания entered/observed и однотипных
committed/pending сигналов ограничены 15000 ms; завершение сценария, включая
timeout/ошибку, освобождает все удерживаемые route barriers до context cleanup.
Focused Node regression: функциональный RED — 1 timeout/2 passed; GREEN вместе
с прежним lifecycle suite — 10/10, skipped0. Проверены failed outcome/cleanup,
успешный сигнал и освобождение barriers при другой ошибке. По существующему
`FU-2026-10-28-001` узко согласован абзац Code_wiki о restoreGeneration и
sessionEpoch. Application production и browser actions не менялись; browser
suites не повторялись, прежние manifests остаются evidence своих runner hashes.
Исправления прошли scoped re-review; открытых замечаний нет.

## Завершение review

Все восемь задач прошли проверку. [Общий обзор и закрытие замечаний](2026-10-27-ar-01-browser-session-final-review.md): Critical/Important не найдено; два Minor устранены и прошли точечный re-review. Изменения остаются unstaged для пользовательского review; commit, push и развёртывание не выполнялись.
