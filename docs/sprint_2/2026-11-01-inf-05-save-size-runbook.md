# INF-05: локальная проверка большого Save/Revert

Основание: [дизайн](2026-11-01-inf-05-save-size-design.md).
Проверка запускается вручную, в CI и автоматические suites не включена.

## Подготовка и запуск

Нужны Docker Desktop с Linux engine и Compose v2, Node.js, зависимости
`infra/m4` и Chromium Playwright. Если они ещё не установлены, выполнить
`npm ci --prefix infra/m4`, затем из `infra/m4` — `npx playwright install chromium`.
Используется уже закреплённая проектом версия Playwright; новых зависимостей нет.
Docker должен иметь доступ к registry при отсутствии нужных образов/слоёв.

Из корня репозитория:

```powershell
# Весь локальный цикл: proxy + большой API/DB + штатный browser.
& docs/sprint_2/verify-inf-05.ps1

# Только границы proxy, без API/БД и сборки приложения.
& docs/sprint_2/verify-inf-05.ps1 --proxy-only

# Диагностика штатного browser cycle, без большого API-сценария.
& docs/sprint_2/verify-inf-05.ps1 --browser-only
```

Успех: exit 0, `status=passed`, `cleanup=passed` в
`docs/sprint_2/evidence/inf-05/<run-id>/verification.json`.
Полный запуск дополнительно содержит `largeApi.saveReadbackRevertReadback=true`,
два больших API-тела больше 1 048 576 байт, `workflow.saveReloadRevertReload=true`
на обычной линии, проверки baseline и authoritative network обеих фаз.
Один proxy-only успех не заменяет browser/API/DB proof.
Аналогично browser-only не доказывает прохождение большой линии.

Runner создаёт уникальный Compose project и временный config. Только frontend
публикуется на свободном loopback port. API остаётся внутри сети; БД отдельная,
с собственным volume. Сборка использует текущие исходники и `.dockerignore`.
Production API запускается с `DEV_MODE=false` и Secure cookie; seed выполняется
отдельно только в тестовой БД. `http://localhost` проверяет localhost-поведение
Secure cookie, а не внешний HTTPS.

Синтетическая L-003 содержит много вершин на дальней части последнего сегмента.
Большой цикл выполняется через API: текущий UI разрешает ровно три вершины.
После API-фазы собственная БД удаляется и создаётся заново для browser cycle
на штатной линии. Большое тело образуется из реальных координат, без padding.
Fixture не является производственным dataset.
Продуктовые seed-файлы и рабочая БД не изменяются.

## Проверка очистки после ошибки

Эти команды намеренно завершаются exit 1:

```powershell
& docs/sprint_2/verify-inf-05.ps1 --proxy-only --fail-after-proxy
& docs/sprint_2/verify-inf-05.ps1 --fail-after-db
```

Ожидается `Injected failure ...`, `cleanup=passed` и отсутствие контейнеров,
сетей и volumes с Compose label данного project. `finally` выполняет удаление
только своих ресурсов; evidence остаётся. При принудительном завершении самого
runner со стороны ОС выполнение `finally` не гарантируется: проверить ресурсы
по project ID из evidence и удалить только принадлежащие этому запуску.

При ошибке читать `verification.json`: отказ сборки/readiness не считается
воспроизведением INF-05; 413 на geometry path свидетельствует о старой/неверной
конфигурации; доменный rejection требует проверки fixture, а не ослабления guards.
В evidence запрещено сохранять bearer, cookie, JWT secret и полные auth-ответы.

## Production-развёртывание

В образ frontend копируется `apps/frontend/nginx.conf`: пересобрать target `prod`
и пересоздать frontend по принятой процедуре развёртывания. Изменение файла на host
не обновляет уже работающий контейнер. После пересоздания backend с другим IP
перезапустить frontend nginx, как принято в INF-02.

Исключение тела относится к каноническому пути:

```text
/api/v1/work-orders/<id>/edit-versions/<id>/features/<id>/geometry
```

Для него frontend nginx не ограничивает размер тела; остальные API сохраняют
прежний предел. Авторизация, методы, JSON и доменные guards проверяются backend.
Save и Revert отправляются на один endpoint. Query string не меняет выбор location.

Внешний HTTPS proxy/WAF/ingress должен пропускать полное тело на этом пути:
конечная квота, запрещающая Save уже редактируемой линии, нарушает требование.
Пути, тело, Content-Type, Authorization и cookie должны доходить без изменения.
Согласовать исключение на каждом внешнем звене; настройка этих компонентов
в INF-05 не выполняется. Не переносить исключение на все endpoints без необходимости.

Снятие квоты не отключает существующие таймауты и buffering. Следить за ресурсами
развёртывания, включая диск временных тел nginx; это не обещание обработки
бесконечного объёма. Локальная приёмка не проверяет внешнюю инфраструктуру
и не устанавливает новый норматив производительности.
