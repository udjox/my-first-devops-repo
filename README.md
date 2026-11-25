# Практика GitHub Actions

Используется Go-сайт из практики 2 с простым оформлением и PostgreSQL. Workflow запускает Docker Compose на Mac через self-hosted runner, создаёт `.env` из GitHub Secrets, проверяет приложение и сохраняет артефакты.

## Файлы

- `.github/workflows/deploy.yml` — запуск по push в main и вручную, self-hosted macOS ARM64 runner.
- `scripts/create-env.mjs` — создание рабочего `.env` из окружения без вывода пароля.
- `tests/application.spec.cjs` — проверки приложения и прямое сравнение БД, API и видимого списка в браузере.
- `scripts/collect-artifacts.mjs` — логи, состояние контейнеров, сведения об образе, отчёт и `.env` без значений.
- `scripts/configure-github.mjs` — загрузка локальных параметров БД в GitHub Secrets и регистрация подготовленного runner.

## Локальный запуск

Требуются Docker Desktop, Node.js и npm.

```sh
cd /Users/egor/Documents/Codex/2026-11-11/gj/outputs/github-actions-practice
docker compose config -q
docker compose up -d --build --wait
npm ci
npx playwright install chromium
npm test
node scripts/collect-artifacts.mjs
```

Страница: http://localhost:8080/. API: http://localhost:8080/api/items. Проверка готовности: http://localhost:8080/healthz.

Рабочий `.env` уже создан на этом Mac. При переносе создайте собственный файл по `.env.example`. Существующий пароль БД привязан к тому: изменение `.env` само по себе не меняет пароль в существующей PostgreSQL.

## Репозиторий и runner

Репозиторий: https://github.com/udjox/my-first-devops-repo. Runner `MacBook-Pro-Egor-practice` зарегистрирован на этом Mac с меткой `practice-actions` и установлен как пользовательская служба. Секреты `DB_USER`, `DB_PASSWORD`, `DB_NAME` настроены.

## Повторная настройка GitHub на другом компьютере

1. Войдите через GitHub CLI: `gh auth login --web --git-protocol https`. Завершите вход в браузере. Пароли и токены не нужно отправлять в чат.
2. Создайте репозиторий для проекта, предпочтительно приватный, или выберите существующий.
3. В этой папке уже инициализирован отдельный Git-репозиторий с веткой main. Рабочий `.env`, артефакты и node_modules исключены из Git.
4. Настройте secrets и зарегистрируйте runner:

```sh
node scripts/configure-github.mjs OWNER/REPO
```

Скрипт берёт параметры из локального Compose и создаёт секреты `DB_USER`, `DB_PASSWORD`, `DB_NAME`. Пароль не печатается. Runner должен быть распакован в `~/Library/Codex/practice-actions-runner` — на этом Mac это уже выполнено. Можно задать другой путь через `PRACTICE_RUNNER_DIR`.

В Settings > Actions > Runners должен появиться runner со статусом Idle/Online и меткой `practice-actions`. Для выполнения jobs Docker Desktop должен работать, компьютер должен оставаться включённым.

После загрузки проекта в ветку main workflow запускается автоматически. Повторный ручной запуск: Actions > Deploy and test fullstack application > Run workflow.

## Что демонстрировать

1. Runner со статусом Online и job на нём.
2. Успешный шаг Create .env from GitHub Secrets; значения секретов не выводятся.
3. Успешный Deploy: `docker compose up -d --build --wait`; оба контейнера healthy.
4. Два успешных теста: health/API/БД и соответствие видимой страницы прямому SQL.
5. Артефакт `deployment-<run_id>`: `test-report.md`, JSON результатов, скриншот, логи, состояние Docker, `.env` со значениями `***`.

Используется современная команда `docker compose`, соответствующая `docker-compose` из методички. В примерах PDF встречаются другие маршруты: в этом проекте используются реальные `/healthz` и `/api/items`.

После job рабочий `.env` удаляется из checkout runner; контейнеры продолжают работать. Скачиваемый артефакт содержит только замаскированный `.env`. Локальный исходный `.env` в папке проекта остаётся на месте.

Остановить локальный стек с сохранением базы: `docker compose down`. Не используйте `-v`, если данные нужны.
