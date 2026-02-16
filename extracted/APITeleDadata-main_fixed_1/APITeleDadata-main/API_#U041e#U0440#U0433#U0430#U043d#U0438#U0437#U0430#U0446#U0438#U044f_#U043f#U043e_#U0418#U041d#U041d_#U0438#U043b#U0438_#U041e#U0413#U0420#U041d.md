# API: организация по ИНН или ОГРН

Краткая developer-документация по методу DaData `findById/party`.

## Как вызвать

**Endpoint:** `https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party`  
**Method:** `POST`

**Заголовки:**

- `Content-Type: application/json`
- `Accept: application/json`
- `Authorization: Token <DADATA_API_KEY>`

**Тело запроса (UTF-8):**

```json
{
  "query": "7707083893",
  "count": 10,
  "kpp": "540602001",
  "branch_type": "MAIN",
  "type": "LEGAL",
  "status": ["ACTIVE"]
}
```

### Параметры запроса

- `query` *(string, обязательно)* — ИНН или ОГРН.
- `count` *(number, по умолчанию 10)* — количество результатов (максимум 300).
- `kpp` *(string)* — КПП для поиска конкретного филиала.
- `branch_type` *(string)* — `MAIN` (головная организация) или `BRANCH` (филиал).
- `type` *(string)* — `LEGAL` (юрлицо) или `INDIVIDUAL` (ИП).
- `status` *(array[string])* — фильтр по статусу организации.

## Что в ответе

Метод возвращает массив `suggestions`, где каждый элемент содержит:

- `value`, `unrestricted_value` — отображаемое наименование.
- `data` — расширенная карточка компании/ИП.

Ключевые поля в `data`:

- Реквизиты: `inn`, `kpp`, `ogrn`, `okpo`, `oktmo`, `okato`, `hid`.
- Тип и состояние: `type`, `state.status`, `state.code`, `state.registration_date`, `state.liquidation_date`.
- Наименование: `name.full_with_opf`, `name.short_with_opf`.
- Руководство/учредители: `management`, `managers[]`, `founders[]` (зависит от тарифа).
- Адрес: `address.value`, `address.unrestricted_value`, `address.data`.
- Экономика и классификаторы: `okved`, `okveds[]`, `finance`, `opf`.
- Контакты: `phones[]`, `emails[]`.
- Дополнительно: `authorities`, `documents`, `licenses`, `branch_count`, `branch_type`.

## Примеры

### cURL

```bash
curl -X POST \
  "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Token <DADATA_API_KEY>" \
  -d '{"query":"7707083893"}'
```

### Python (`dadata`)

```python
from dadata import Dadata

dadata = Dadata("<DADATA_API_KEY>")
result = dadata.find_by_id("party", "7707083893")
```

### Только головная организация

```json
{
  "query": "7707083893",
  "branch_type": "MAIN"
}
```

### Поиск филиала по КПП

```json
{
  "query": "7707083893",
  "kpp": "540602001"
}
```

### Поиск только среди ИП

```json
{
  "query": "784806113663",
  "type": "INDIVIDUAL"
}
```

## Ограничения

- Длина `query` — до **300** символов.
- Частота запросов — до **30 rps** с одного IP.
- Частота новых соединений — до **60 в минуту** с одного IP.
- Дневной объём — в рамках вашего тарифного плана.

## Стоимость

- До **10 000** запросов/день — бесплатно.
- Сверх лимита — по условиям годовой подписки DaData.
