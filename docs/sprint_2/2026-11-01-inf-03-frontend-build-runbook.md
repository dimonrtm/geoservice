# INF-03: проверка изоляции frontend Docker build

## Контракт

Контекст apps/frontend исключает локальные зависимости, env, результаты сборки и служебные артефакты через .dockerignore. Dockerfile и targets не меняются. Dev получает VITE_API_BASE_URL явно при запуске; production использует origin страницы и nginx proxy. Локальный npm run dev по-прежнему читает env-файлы. Изоляция не означает побайтовую идентичность образов в разные дни.

## Запуск

Из корня репозитория, с Node.js 20+ и доступным Linux Docker daemon/Buildx:

~~~powershell
node --test docs/sprint_2/inf-03/fixtures.test.mjs docs/sprint_2/inf-03/run.test.mjs
node docs/sprint_2/inf-03/run.mjs
~~~

Обычный режим — тот же сценарий, который запускает CI frontend_docker_isolation. Он собирает dev/prod из временной копии текущих исходников, загрязнённой 15 искусственными файлами. Реальные env, зависимости и старый dist при подготовке копии не читаются; symlink/junction вне исключённых артефактов отклоняются. После добавления fixtures очистки context нет: фильтрацию выполняет Docker.

Проверяются наличие всех fixtures перед сборкой, отсутствие маркеров в общем /app, сохранение установленных Linux-зависимостей и необходимых исходников, production assets без старого dist/чужого API URL, HTTP-ответ Vite и явный API URL в преобразованном модуле. nginx не запускается ради чтения статики: backend, БД и Compose-стенд не нужны.

Расширенная локальная приёмка:

~~~powershell
node docs/sprint_2/inf-03/run.mjs --acceptance
node --test docs/sprint_2/inf-03/failure.integration.test.mjs
~~~

--acceptance добавляет чистую копию, отрицательный контроль без ignore и прямую dev/prod-сборку из apps/frontend. Реальные локальные env не выводятся. Перед прямой сборкой проверяется совпадение ignore с прошедшей проверку копией и отсутствие Dockerfile.dockerignore. Отрицательный контроль успешен только при обнаружении всех искусственных маркеров: ошибка npm/сети не считается доказательством чувствительности.

failure.integration.test.mjs меняет команду build только во временной копии на exit 37, проверяет failed, отсутствие оставшихся контейнеров/образов/context и сохранность исходной копии и соседнего файла. Статус failed в его summary.json ожидаем; сам Node test должен пройти.

## Evidence и диагностика

По умолчанию summary.json сохраняется в docs/sprint_2/evidence/inf-03/<уникальный-id>. Для заданного каталога использовать --evidence-dir PATH; повторный запуск перезаписывает summary.json в этом каталоге. CI использует RUNNER_TEMP/inf-03 и сохраняет артефакт на 7 дней, в том числе при ошибке.

Успех: exit 0, status=passed, cleanupErrors пуст. Отсутствующий Docker, ошибка build/проверки/cleanup дают ненулевой exit. Команды ограничены 2 минутами, build — 10 минутами, readiness Vite — 60 секундами. При ошибке рабочего context подробный вывод не сохраняется, чтобы не раскрыть вывод пользовательских build scripts. Синтетические build errors могут содержать короткий технический хвост Docker.

Runner использует уникальные имена, динамический loopback port и удаляет только свои контейнеры, теги и временный каталог. Общий BuildKit cache не чистится; Docker prune не выполняется. При принудительном завершении самого Node-процесса средствами ОС выполнение finally не гарантируется: оставшиеся ресурсы искать по id из вывода и удалять адресно после проверки принадлежности. Не очищать весь Docker ради INF-03.

## CI и границы гарантии

Workflow выполняет unit tests runner и обычный загрязнённый сценарий без установки frontend dependencies на host job. Старые npm jobs продолжают работать. Образы не публикуются. Workflow с ошибкой получает failed; блокирование merge требует отдельно настроенного required status check frontend_docker_isolation в GitHub branch protection. Настройки репозитория эта задача не меняет.

Проверка подтверждает действие исключений на общем COPY и итоговом продукте, а не полный аудит BuildKit cache exports. Не запускает полный Save/readback/Revert smoke, не проверяет TLS и не меняет INF-04. Новый неизвестный вид локальных файлов требует дополнения исключений и fixtures.

[Дизайн](2026-11-01-inf-03-frontend-build-design.md), [план](2026-11-01-inf-03-frontend-build-plan.md).
