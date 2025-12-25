# geoservice

Учебно-практический проект: универсальный картографический веб-сервис (on-prem).
На текущем этапе репозиторий содержит базовую структуру и договорённости.

## Быстрый старт

Клонировать репозиторий:

```bash
git clone https://github.com/dimonrtm/geoservice.git
cd geoservice```

## Статус

Проект в активной разработке. Сейчас настроена базовая структура репозитория и Git-процессы.

##Сборка образа:
docker build -t my-backend .
Запуск контейнера: docker run -p 3000:3000 my-backend
Проверка работоспособности сервера: curl http://localhost:3000/health

## Проверка работоспособности (smoke test)

docker compose up -d --build → оба контейнера Up, у postgis healthy

curl -i http://localhost:3000/ → HTTP/1.1 200 OK и Hello World!

Подключение к БД localhost:5432 (любым клиентом) → база geo существует

docker compose exec postgis psql -U postgres -d geo -c "SELECT PostGIS_Full_Version();"
Ожидаемый результат: одна строка с версией PostGIS (любая, главное что запрос выполнился).


## Документы

- [День 1 — чеклист](docs/day-01-checklist.md)
