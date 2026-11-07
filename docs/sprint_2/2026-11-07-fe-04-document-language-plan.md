# FE-04 — план реализации языка документа и названия приложения

> Исполнителю: применять `superpowers:executing-plans` при последовательной реализации либо `superpowers:subagent-driven-development`, если пользователь выберет работу через субагентов. Выполнять задачи по порядку, отмечая проверенные шаги.

**Цель:** русский HTML-документ и единое настраиваемое при сборке название во вкладках и интерфейсе.

**Архитектура:** Vite один раз нормализует `VITE_APP_NAME` и передаёт результат в HTML и клиентскую константу. Docker/Compose явно доставляют параметр до сборки; production nginx отдаёт готовую статику.

**Стек:** Vue 3, TypeScript, Vite 7, Vitest/jsdom, Docker Compose. Новых зависимостей нет.

**Спецификация:** [согласованный дизайн](2026-11-07-fe-04-document-language-design.md). Статус плана: реализован по поручению пользователя; проверка реальной озвучки не выполнена. [Отчёт](2026-11-07-fe-04-document-language-report.md).

## Общие ограничения

- `lang="ru"`; default `GeoService`; trim по краям; пустое значение возвращает default.
- Название — текст. Одинаково в первоначальном HTML и UI; не зависит от роли, наряда и состояния.
- Пересборка production допустима. Runtime-конфигурация nginx и UI настроек не нужны.
- Не менять favicon, API, storage keys, имена сервисов и доменную модель.
- Документация на русском в `docs/sprint_2`; текстовые файлы UTF-8/LF.
- Не выполнять `git add`, `git commit`, `git push`. Не изменять пользовательский стенд ради проверки.

## Особое внимание при проверке

1. Пробельная настройка должна одинаково нормализоваться для HTML и UI — задача 1.
2. `</title>`, кавычки и `&` должны оставаться текстом, без внедрения разметки — задача 1.
3. Первоначальный HTML должен иметь правильные метаданные до исполнения Vue — задачи 1 и 3.
4. Параметр Compose должен попасть в Docker build, несмотря на исключение `.env` из контекста — задача 2.
5. Повторная сборка с новым названием и dev-перезапуск не должны сохранять старое значение — задачи 2 и 3.

## Задача 1. Единый источник названия для HTML и Vue

**Файлы:** создать `apps/frontend/build/appBranding.ts`, `apps/frontend/build/appBranding.test.ts`, `apps/frontend/src/config/app.ts`, `apps/frontend/src/app-env.d.ts`; изменить `apps/frontend/vite.config.ts`, `apps/frontend/index.html`, `apps/frontend/src/App.vue`, `apps/frontend/src/App.test.ts`. При необходимости расширить `tsconfig.node.json` для явного включения build-модуля; существующие режимы проверки сохранить.

**Интерфейсы:** build-модуль экспортирует `resolveAppName(configuredAppName: string | undefined): string` и `createAppBrandingPlugin(appName: string): Plugin` из Vite. Клиентский модуль экспортирует `appName: string`, полученный из типизированной константы `__APP_NAME__`; клиент не повторяет нормализацию.

- [x] Добавить тесты default/trim и результата настоящего `transformIndexHtml` Vite с подключённым plugin и исходным `index.html`. Для каждого значения проверять `documentElement.lang`, единственный title и его `textContent`, а не только строку HTML. Примеры обязательных ожиданий:

```ts
expect(resolveAppName(undefined)).toBe("GeoService");
expect(resolveAppName("")).toBe("GeoService");
expect(resolveAppName("   ")).toBe("GeoService");
expect(resolveAppName("  Сети Уфы  ")).toBe("Сети Уфы");
// Для настроенного имени ниже parsedDocument.title должен равняться имени,
// а элемент #injected должен отсутствовать.
const configuredAppName = 'Сети & "Уфа" </title><div id="injected">';
```

- [x] Выполнить `npm run test -- build/appBranding.test.ts` из `apps/frontend`; подтвердить ожидаемый сбой из-за отсутствующего поведения. Тестовый Vite server создавать без прослушивания порта, с `configFile: false`, закрывать в `finally`.
- [x] Реализовать build-модуль. Экранировать текст title; использовать `transformIndexHtml` после встроенной подстановки env, чтобы текст имени с `%...%` не подвергался дополнительной интерпретации. Исходный HTML содержит ровно один title `GeoService` и `lang="ru"`.
- [x] В `vite.config.ts` через `loadEnv(mode, frontendRoot, "VITE_")` получить параметр; вызвать `resolveAppName` один раз; подключить plugin и `define: { __APP_NAME__: JSON.stringify(appName) }`. Сохранить Vue plugin, aliases и Vitest setup. В `src/app-env.d.ts` объявить строковый тип константы; `src/config/app.ts` экспортирует её значение.
- [x] В `App.test.ts` добавить проверку tooltip для подставленного через mock модуля `config/app` имени `Сети Уфы`; ожидание — `Выйти из Сети Уфы`. Проверить prop реального `UiIconButton` или текст открытой подсказки; не менять общий компонент кнопки. Выполнить тест до правки App, подтвердить сбой, затем заменить literal в `App.vue` на привязку к `appName`.
- [x] Выполнить `npm run test -- build/appBranding.test.ts src/App.test.ts` и `npm run typecheck`; ожидать успешное завершение. Проверить, что существующие App-сценарии восстановления, входа и обеих ролей проходят.

## Задача 2. Передача настройки при развёртывании

**Файлы:** изменить `apps/frontend/Dockerfile`, `infra/docker-compose.yml`, `infra/docker-compose.demo.yml`, `infra/.env.example`; создать `docs/sprint_2/2026-11-07-fe-04-document-language-runbook.md`.

**Интерфейсы:** единственный внешний параметр `VITE_APP_NAME`; потребитель — конфигурация Vite из задачи 1. Нормализация остаётся только там.

- [x] В build stage Dockerfile объявить `ARG VITE_APP_NAME` и сделать его доступным процессу `npm run build`. Не переносить настройку в runtime nginx и не снимать исключения `.dockerignore`.
- [x] В production Compose добавить `build.args.VITE_APP_NAME: ${VITE_APP_NAME:-GeoService}`; в demo/dev environment передать такой же параметр. В `infra/.env.example` добавить `VITE_APP_NAME=GeoService` с пояснением пересборки.
- [x] Проверить разрешённую Compose-конфигурацию с временным несекретным env-файлом и нестандартным именем; вывести только frontend build arg и dev environment, не полный config с секретами. Ожидать точную доставку строки к соответствующим сервисам.
- [x] Собрать только frontend через production Compose с временным env-файлом: `docker compose --env-file <test-env> -f infra/docker-compose.yml --profile prod -p <уникальный-fe04-проект> build frontend-prod`. Не запускать backend/БД. Из созданного образа извлечь `/usr/share/nginx/html/index.html` и проверить title/lang. Повторить с другим названием в том же проекте, без принудительного отключения кэша; результат должен обновиться. Проверить dev после перезапуска Vite с изменённым параметром.
- [x] Записать в runbook способы задания параметра для локального Vite, production Compose и demo/dev, default/trim, необходимость пересборки или dev-перезапуска. Объяснить корректное цитирование специальных символов в выбранном env-формате; не обещать, что синтаксис shell, dotenv и Compose одинаков. Удалять только собственные временные ресурсы по точным именам.

## Задача 3. Итоговая проверка и фиксация результатов

**Файлы:** создать `docs/sprint_2/2026-11-07-fe-04-document-language-report.md`; обновить `docs/sprint_2/frontend-review.md`, `docs/sprint_2/2026-10-26-deep-code-review.md`, `docs/sprint_2/README.md` после подтверждения результата. При необходимости evidence хранить в `docs/sprint_2/evidence/fe-04/`.

- [x] Проверить настоящий production build с default и настроенным именем, включая строку со спецсимволами. Разобрать HTML, подтвердить точный title, `lang="ru"`, отсутствие лишних элементов и шаблонных маркеров. Проверить клиентское отображение имени из этой же сборки, чтобы тест mock-модуля не скрывал ошибку передачи `define`.
- [x] В браузере пройти вход и выход на изолированном стенде, проверить постоянство title и настроенную подсказку выхода. Допустимо использовать существующие browser fixtures без изменений бизнес-логики. Проверить первоначальный HTTP-ответ отдельно от DOM после загрузки JavaScript.
- [ ] Выполнить screen reader smoke русского текста при доступном средстве озвучивания. Записать средство, браузер и наблюдения; при недоступности явно оставить эту проверку невыполненной, не заменять её DOM-assertions.
- [x] Из `apps/frontend` выполнить `npx prettier --check <изменённые frontend-файлы>`, `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`. Ожидать exit code 0; новые сбои устранить, существующие ограничения отличить от регрессий.
- [x] Выполнить `git diff --check`, проверить LF также у новых untracked-файлов и просмотреть diff на отсутствие изменений storage keys, API и посторонних файлов.
- [x] Сохранить фактические результаты и ограничения в отчёт; обновить статус FE-04 и ссылки в реестре/README без заявления о непроверенной озвучке или полном соответствии WCAG. Новая agent memory не нужна. Repository-change ingest нужен только при выявлении самостоятельного долговременного технического знания, не из-за завершения задачи.

## Самопроверка плана

Все критерии дизайна покрыты: метаданные и текстовые значения — задача 1; сборка и развёртывание — задача 2; артефакт, браузер, озвучка и проектные проверки — задача 3. Внешний параметр и клиентский интерфейс согласованы между задачами. Выполнение последовательное, поскольку задачи 2 и 3 проверяют результаты задачи 1. Для небольшого изменения рекомендуется выполнение основным агентом с итоговым независимым ревью.

Уточнения исполнения: в задачу 1 включены LoginScreen.vue и его тест для русского названия; frontend .gitignore разрешает два source-файла в build/. Реальная озвучка не запускалась, это ограничение сохранено в отчёте.
