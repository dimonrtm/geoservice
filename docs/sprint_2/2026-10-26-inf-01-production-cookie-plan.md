# План реализации INF-01: безопасный старт API

> Для исполнителя: применять `superpowers:executing-plans` при исполнении в текущем чате либо `superpowers:subagent-driven-development`, если пользователь выберет исполнение субагентами. Читать план вместе со спецификацией. Шаги отмечать по фактическому выполнению.

**Цель:** базовый API запускается с Secure cookie, а явный HTTP demo сохраняет свои настройки.

**Архитектура:** политика Secure фиксируется строковыми значениями в двух Compose слоях. Backend Settings и startup scripts не меняются. Изолированная локальная проверка запускает реальный production API и проверяет отрицательный сценарий.

**Стек:** Docker Compose v2, существующий Python backend Dockerfile, PowerShell 7, существующие pytest suites.

**Спецификация:** [принята 2026-10-26](2026-10-26-inf-01-production-cookie-design.md).

## Общие ограничения

- Base: `DEV_MODE=false`, Secure=true; demo: `DEV_MODE=true`, Secure=false.
- Не менять Settings/defaults, auth-контракты, CORS, migrations, seeds, CI и frontend.
- HTTPS и исправления INF-02/03/04 не входят в задачу.
- Не использовать рабочие БД/volumes; не запускать demo seed chain для приёмки INF-01.
- Не выполнять `git add`, `git commit`, `git push`; оставить изменения unstaged.
- Все новые материалы — в `docs/sprint_2`, русский язык, UTF-8 с LF; `.ps1` также LF.
- Существующие изменения README и материалы ревью сохранять. Agent memory не дублировать: устойчивые основания уже записаны в анализе и спецификации.

## Особое внимание при проверке

1. Host env или локальный `.env` не должны скрыть отсутствие Secure в YAML — изолировать входы Compose, положительный запуск без `run -e`.
2. Существующий контейнер `utility_service` не должен быть принят за проверяемый — уникальные project/name, запрос внутри конкретного контейнера.
3. Demo наследует base environment — проверять результат merge, а не только две строки исходных файлов.
4. Запущенный, но неготовый API и зависший отрицательный запуск не означают успех — bounded wait, HTTP/body assertions, проверка exit code и причины отказа.
5. Ошибка на любом этапе не должна оставлять проверочные контейнеры или удалять чужие ресурсы — `try/finally`, журнал созданных ресурсов и проверка project label перед cleanup.

## Файлы и ответственность

| Файл | Изменение |
| --- | --- |
| `infra/docker-compose.yml` | Одна настройка Secure=true для API |
| `infra/docker-compose.demo.yml` | Одна настройка Secure=false для API |
| `docs/sprint_2/verify-inf-01.ps1` | Создать локальную проверку конфигурации/startup и изолированный cleanup |
| `docs/sprint_2/2026-10-26-inf-01-production-cookie-runbook.md` | Создать инструкцию запуска и описание ограничений |
| `docs/sprint_2/2026-10-26-inf-01-production-cookie-implementation-report.md` | Создать отчёт с фактическими результатами |
| `docs/sprint_2/README.md` | Добавить ссылки на результаты, сохранив исходные изменения |

## Задача 1. Исправить Compose и подтвердить локальным запуском

**Вход:** два существующих Compose-файла, backend Dockerfile и принятая спецификация.

**Выход:** исправленная конфигурация и исполняемая проверка `verify-inf-01.ps1` с параметром `[int] $TimeoutSeconds = 60` (допустимо 10–300). Запуск из любого cwd; корень репозитория вычисляется относительно `$PSScriptRoot`. Exit 0 только при выполнении всей матрицы, иначе exit 1. На экран выводятся имена проверок, результат, Docker/Compose versions и image ID, без полного environment.

- [x] **1. Подготовить проверку без изменения runtime YAML.** Использовать уникальный project `geoservice-inf01-<случайный суффикс>`, отдельный временный env-файл с синтетическими обязательными значениями, только явные `-f` и `--env-file`. Сохранить и временно убрать влияющие на Compose значения окружения процесса, затем восстановить в `finally`. Не читать приватные `.env`. Получать base/demo resolved config через `config --format json` в память, не сохранять полный вывод.
- [x] **2. Реализовать действительный startup probe.** Собрать `utility_service` target `prod` через base Compose в уникальном project. Запустить `run --no-deps -d --name <уникальное имя> utility_service` без env overrides и service ports. Проверить реальное завершение/работу контейнера и запросить `/health` через контейнерный Python с HTTP timeout=2; ждать не дольше `TimeoutSeconds`. Ожидать HTTP 200 и JSON `{"ok": true}`. Отдельным импортом внутри работающего контейнера проверить `dev_auth_enabled=False` и Secure=true. Проверка должна дойти до startup даже при отсутствии Secure в исходном YAML, чтобы RED был runtime-сбоем, а не только сравнением config.
- [x] **3. Выполнить RED на текущем base.** Команда: `pwsh -NoProfile -File docs/sprint_2/verify-inf-01.ps1`. Ожидать exit 1 и конкретную ошибку обязательной Secure cookie при production startup. Ошибки build/network/Docker permission не считать доказательством дефекта. Проверить cleanup после этого отказа; исходную рабочую среду не останавливать.
- [x] **4. Внести выбранную политику.** Добавить `AUTH_SESSION_COOKIE_SECURE: "true"` в base API environment и `AUTH_SESSION_COOKIE_SECURE: "false"` в demo API environment. Другие runtime-файлы не менять.
- [x] **5. Завершить матрицу скрипта.** Проверять resolved base settings/target/command; для demo — merged DEV_MODE=true, Secure=false, target dev и прежний demo command. Импортировать Settings с environment из demo-конфигурации в одноразовом контейнере собранного образа, без demo startup/seeds. Отдельно запускать base API с `run --no-deps -d --name <другое уникальное имя> -e AUTH_SESSION_COOKIE_SECURE=false utility_service`; ожидать bounded завершение с ненулевым exit code и точным сообщением cookie validator. Успех другого падения не засчитывать. Не выводить полный traceback с входными env-значениями.
- [x] **6. Выполнить GREEN.** Повторить команду шага 3. Ожидать exit 0: base startup/HTTP/runtime settings, отрицательный startup и demo merge/settings прошли. Проверить отсутствие созданных контейнеров/сети после выполнения. Cleanup удаляет только собственные ресурсы, сохраняя исходную ошибку при дополнительной ошибке очистки. Свежесобранный образ можно оставить для повторной проверки и указать его tag/ID в отчёте.
- [x] **7. Выполнить существующую регрессию.** Собрать отдельный test image командой `docker build --target dev -t geoservice-inf01-tests:local apps/backend`. Запустить команду ниже. Ожидать exit 0 и отсутствие skips в двух repo-dependent contract modules; БД и браузер не требуются.

```powershell
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 --mount "type=bind,source=$((Get-Location).Path),target=/repo,readonly" -w /repo/apps/backend --entrypoint python geoservice-inf01-tests:local -m pytest -p no:cacheprovider -rs utility_service/utils/tests/test_settings.py utility_service/web_api/tests/test_auth_api.py tests/test_compose_security_contract.py tests/test_compose_startup_contract.py
```

Команда запускается из корня checkout. Это test image; положительный startup smoke шага 6 обязан использовать собранный target `prod`, а не этот образ.

- [x] **8. Сохранить runbook и отчёт.** Runbook описывает prerequisites, команду, отсутствие DB/browser coverage, таймауты и cleanup. Отчёт фиксирует RED/GREEN, версии Docker/Compose, prod image ID, результаты матрицы и pytest, ограничения. Добавить ссылки в README. Проверить `git diff --check`, LF в новых файлах, итоговый diff и отсутствие изменений вне согласованного объёма. Не создавать отдельную memory-запись или wiki ingest без нового уникального знания.

## Самопроверка плана

Спецификация покрыта шагами 1–8: runtime-конфигурация — 4; startup и изоляция — 1–3/6; negative/demo — 5; regression — 7; воспроизводимость и артефакты — 8. Все пять рисков раздела проверки включены в соответствующие шаги. Дополнительные текстовые tests, повторяющие строки YAML, не добавляются. Результаты выполнения сохранены в отчёте реализации: startup smoke прошёл, 51 regression test прошёл.

Рекомендуемое исполнение: последовательно в текущем чате. Изменение небольшое, все шаги образуют один связанный цикл проверки. Пользователь поручил реализовать план; он выполнен в текущем чате.
