# geoservice

Учебно-практический проект: универсальный картографический веб-сервис (on-prem).
На текущем этапе репозиторий содержит базовую структуру и договорённости.

## Быстрый старт

Клонировать репозиторий:

git clone https://github.com/dimonrtm/geoservice.git
cd geoservice

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

## Definition of Done (Неделя 1)

docker compose up -d --build поднимает backend + postgis без ошибок

curl -i http://localhost:3000/ → HTTP/1.1 200 OK и Hello World!

PostGIS отвечает на SELECT PostGIS_Full_Version();

репозиторий чистый (git status clean), есть финальный коммит, всё запушено

docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend
docker compose down


## Документы

- [День 1 — чеклист](docs/day-01-checklist.md)
