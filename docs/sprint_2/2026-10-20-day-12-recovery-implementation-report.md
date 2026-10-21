# День 12 — отчёт реализации recovery

Дата выполнения: 2026-10-21. Основание: [принятая спецификация](2026-10-20-day-12-recovery-design.md), [план](2026-10-20-day-12-recovery-plan.md), поручение пользователя приступить к реализации в текущем каталоге.

**Продуктовая часть реализована, оба сценария M4 пройдены 2026-10-21.** После отдельного принятия пользователем Playwright выполнены commit → потеря ответа → restart API → refresh той же вкладки → replay → GET для Save и Revert. [Доказательства M4](2026-10-21-day-12-m4-report.md). S2-X01 не закрывается.

## Поведение

- «Повторить запрос» запускает новую серию из пяти попыток с задержками 0/2/5/10/20 секунд. Identity и payload прежней команды сохраняются; параллельные серии запрещены. Первоначальная отправка по-прежнему допускает пять дополнительных попыток.
- «Повторить загрузку» после известного исхода выполняет один GET без PUT. Дублирующий вызов не начинает второе чтение; storage/access/role/blocked guards действуют и в store action.
- После успешного stale readback доступен явный отказ от отклонённой попытки. Он не вызывает HTTP и позволяет начать с текущего snapshot; automatic reapply отсутствует. Граница refresh из Дня 9 сохранена.
- Revert получает target и baseline из change set, работает без выбранной линии и использует общий с Save pipeline. При dirty нужны два решения; первый отказ окончательно удаляет draft. Подтверждение связано с actor/workspace/feature/token и инвалидируется при смене контекста.
- После успешного Revert/readback выбор снят и маркер скрыт. Unknown Revert повторяет прежнюю команду без нового согласия; новый Revert после stale требует согласия и нового ID.

Основные изменения находятся в `workOrders.ts`, `workspaceCommandPresentation.ts`, `WorkspaceEditCommands.vue` и map composable. Новые endpoint, backend schema и persisted recovery schema не добавлены. Зависимости приложения сохранены; M4 использует отдельный тестовый пакет `infra/m4` с Playwright Test 1.64.1.

## Проверки

| Проверка | Фактический результат |
| --- | --- |
| Полный frontend `npm.cmd test -- --maxWorkers=2` | 287 passed, 34 файла; после исправления review |
| Recovery suite после исправления тестового типа роли | 33 passed |
| `npm.cmd run lint` | Успешно, без предупреждений |
| `npm.cmd run format:check` | Успешно |
| `npm.cmd run build` | Успешно; предупреждение о chunk больше 500 kB |
| `infra/db-tests.cmd` | 270 passed; 2 предупреждения deprecated зависимостей (`crypt`, `BlockingPortal`) |
| Независимое review | Одно P2 замечание воспроизведено и исправлено; других подтверждённых findings не заявлено |
| Wiki lint | 37 missing_frontmatter в старых RAW; исходники RAW не исправлялись |

RED→GREEN и решения записаны в [журнале](2026-10-21-day-12-execution-ledger.md). Замечание review: прямой readback мог обходить storage/role/blocked guards, хотя UI запрещал действие. Два теста воспроизвели обход, после исправления прошла полная регрессия. Старое ожидание ручного обхода cleanup failure заменено по принятой матрице доступности.

Для тестов и сборки потребовался разрешённый запуск вне sandbox: esbuild получал `spawn EPERM`; Docker — отказ доступа к pipe. DB runner использовал отдельный `geoservice-db-tests`, завершился с кодом 0 и очистил своё окружение.

## Проверка в браузере

Исходный demo frontend содержал старый placeholder. Пересобран только `frontend-dev` с `--no-deps`; рабочие backend и БД не перезапускались.

В demo Editor через UI проверены:

1. Revert при отсутствии выбранной линии; безопасный начальный фокус, Tab/Shift+Tab, Escape с возвратом фокуса.
2. Dirty local edit → первый отказ → второй диалог → Escape: локальная правка не восстановилась, команда Revert не отправлялась на отмене.
3. Подтверждённый Revert → readback: сохранённых изменений для сброса нет, выбор снят, marker отсутствует.
4. Новая правка L-003 → Save → refresh той же вкладки: сохранённая геометрия снова отображается, Revert доступен, local draft отсутствует.

Итоговое состояние demo: **L-003 имеет контрольное сохранённое изменение; несохранённой правки и выбранной линии нет**. Baseline не изменялся. Предыдущее demo-изменение было сброшено явным Revert в ходе проверки.

Второй диалог проверен на реальных viewport 1440×900, 1024×768, 768×1024 и reflow-размерах 720×450, 512×384, 384×512. Диалог и кнопки помещаются, горизонтального overflow документа нет. Настоящий browser zoom 200% не проверен; viewport override снят. Автоматические обновления статуса и контекстные guards дополнительно покрыты component/store tests.

Evidence:

- [Первый диалог отказа](evidence/day-12/discard-local-dialog.png).
- [Desktop 1440×900](evidence/day-12/dialog-1440x900.png), [1024×768](evidence/day-12/dialog-1024x768.png), [768×1024](evidence/day-12/dialog-768x1024.png).
- [Reflow 720×450](evidence/day-12/dialog-720x450.png), [512×384](evidence/day-12/dialog-512x384.png), [384×512](evidence/day-12/dialog-384x512.png).
- [Завершённый Revert](evidence/day-12/revert-completed.png).
- [Сохранённая правка после refresh](evidence/day-12/save-after-refresh.png).

Скриншоты подтверждают UI, но не отсутствие duplicate mutation при backend restart.

## Дополнение M4

Задача 5 выполнена после отдельного принятия инструмента пользователем: `npm.cmd test` в `infra/m4` — 2 passed (27.1s), exit code 0. Проверены настоящие commit/restart/refresh/replay, identity/payload, счётчики и baseline. [Отчёт M4](2026-10-21-day-12-m4-report.md) содержит evidence и ограничения. Ранее выполненная регрессия выше не выдаётся за новый прогон.

S2-X01 не расширялся и не закрывался. Новые сведения об общем pipeline, confirmation context и recovery guards отражены узким `repository-change ingest` в существующей ноде `Code_wiki/архитектура/frontend_save_recovery.md`; доменные follow-up не закрывались. Отдельная долговременная память не создавалась: знание уже сохранено в коде, спецификации и технической ноде.

Изменения оставлены unstaged. `git add`, `git commit`, `git push` не выполнялись; `.obsidian/graph.json` не изменялся агентом.
