STATUS: DOWN

CRITICAL (блокеры запуска)
- Блокер 1: невозможно выполнить black-box проверку, так как входные параметры не переданы (URL приложения, OpenAPI, креды, ожидаемые флоу представлены как плейсхолдеры `<APP_URL>`, `<OPENAPI_URL_OR_FILE>`, `<CREDS>`, `<EXPECTED_FLOWS>`).
  - Репродьюс:
    1) Взять входные данные задачи.
    2) Попытаться выполнить сетевые/функциональные проверки по URL.
  - Фактическое: отсутствует валидный URL/контракт для тестирования; проверка недетерминирована.
  - Ожидаемое: передан реальный URL и (опционально) OpenAPI/креды/сценарии.

MAJOR
- [[TBD]] После предоставления реального URL.

MINOR
- [[TBD]] После предоставления реального URL.

EVIDENCE
- Подтверждение отсутствия входных данных:
  - `APP_URL=<APP_URL>` (плейсхолдер, невалидный target).
  - `OPENAPI=<OPENAPI_URL_OR_FILE>` (плейсхолдер).
  - `CREDS=<CREDS>` (плейсхолдер).
  - `EXPECTED_FLOWS=<EXPECTED_FLOWS>` (плейсхолдер).
- Команды, которые будут выполнены сразу после получения данных:
  - `curl -I -L -o /dev/null -s -w 'code=%{http_code} ttfb=%{time_starttransfer} total=%{time_total} ip=%{remote_ip}\n' <APP_URL>`
  - `curl -sS -D - <APP_URL>/health`
  - `curl -sS -D - <APP_URL>/<key_endpoint>`
  - `curl -sS -X POST <APP_URL>/<key_post_endpoint> -H 'Content-Type: application/json' -d '<payload>'`

RECOMMENDED FIX
- Передать полный набор входных параметров:
  1) Реальный `APP_URL` (схема + хост),
  2) `OPENAPI_URL_OR_FILE` (если есть),
  3) тестовые `CREDS` (если требуется авторизация),
  4) 3–5 ожидаемых бизнес-флоу в `EXPECTED_FLOWS`.
- ASSUMPTION: после получения параметров проверка будет выполнена в том же формате с фактическими `curl`-доказательствами и классификацией CRITICAL/MAJOR/MINOR.

NEXT
- После получения входных данных проверить:
  1) DNS/HTTPS/редиректы/TTFB,
  2) `/health` или эквивалент,
  3) 3–5 ключевых пользовательских шагов,
  4) 5–10 API-методов (GET/POST) с валидацией схем/ошибок,
  5) негативные кейсы (4xx без 500),
  6) базовые security headers/CORS/утечки.
