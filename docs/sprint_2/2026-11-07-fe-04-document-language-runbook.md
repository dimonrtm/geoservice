# FE-04 — настройка названия приложения

`VITE_APP_NAME` задаёт общее название во вкладках и интерфейсе. Значение по умолчанию — `GeoService`. Пробелы по краям удаляются; пустая или пробельная строка возвращает default. Язык документа всегда `ru`.

## Production Compose

В используемый при развёртывании env-файл добавить, например:

```dotenv
VITE_APP_NAME='Сети Уфы'
```

Из корня репозитория выполнить с действующим env-файлом развёртывания:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml --profile prod build frontend-prod
docker compose --env-file infra/.env -f infra/docker-compose.yml --profile prod up -d --no-deps frontend-prod
```

Второй шаг предполагает уже работающий backend. Compose передаёт название как build argument, Docker делает его доступным Vite во время сборки. Обычный перезапуск старого образа или environment-переменная запущенного nginx название не изменяют. После обновления проверить вкладку и подсказку кнопки выхода на узком экране.

При прямой сборке Docker:

```powershell
docker build --target prod --build-arg 'VITE_APP_NAME=Сети Уфы' -t geoservice-frontend:local apps/frontend
```

## Demo/dev

Передать тот же параметр через окружение Compose или выбранный env-файл. Пример PowerShell из корня репозитория:

```powershell
$env:VITE_APP_NAME = 'Сети Уфы'
docker compose --env-file infra/demo.env -f infra/docker-compose.yml -f infra/docker-compose.demo.yml --profile dev up -d --no-deps frontend-dev
```

При изменении environment Compose пересоздаёт dev-контейнер. Если изменён env-файл, который читает сам Vite, требуется перезапуск Vite. Локальные `.env` не копируются в Docker context; это намеренное ограничение.

## Локальный frontend

В PowerShell из `apps/frontend`:

```powershell
$env:VITE_APP_NAME = 'Сети Уфы'
npm run dev
# Или создать новую production-сборку:
npm run build
```

Альтернатива — `.env.local` или соответствующий mode-файл Vite. Уже установленная переменная окружения имеет приоритет над env-файлом. После изменения настройки перезапустить dev-сервер. Для возврата к env-файлам удалить только свою переменную `Remove-Item Env:VITE_APP_NAME`.

Название вставляется как текст: кавычки, `&`, `<`, `>` не создают HTML. Цитирование на входе всё равно зависит от инструмента: в PowerShell одинарные кавычки сохраняют `$` буквально, одинарная кавычка внутри такой строки удваивается. В dotenv Vite `$` участвует в подстановках и требует экранирования; синтаксис Compose env-файлов отличается. Для сложного имени проверить уже разрешённый frontend build argument, не публикуя весь Compose config с секретами.

## Границы

Настройка публичная, попадает в клиентскую сборку. Она не меняет storage keys, имена сервисов, роли, favicon и язык интерфейса. Различные вкладки одного развёртывания имеют одинаковый title.
