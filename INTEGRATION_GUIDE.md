# Руководство по интеграции Telegram бота с API

## Обзор

Ваш проект предоставляет REST API для обработки сообщений от Telegram бота. Telegram бот (отдельный проект) отправляет запросы в ваш API и получает ответы.

## Архитектура

```
Telegram Bot (отдельный проект)
    ↓ HTTP POST
Ваш API (FastAPI)
    ↓
Gemini Chat Manager
    ↓
Gemini API
    ↑
Ответ возвращается обратно в Telegram бот
```

## Запуск вашего API

```bash
python main.py
```

API будет доступен по адресу: `http://localhost:8000`

Для продакшена:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Основной эндпоинт для Telegram бота

### POST `/chat/message`

Этот эндпоинт обрабатывает сообщения от пользователей Telegram.

**Запрос:**
```json
{
  "user_id": 123456789,
  "message": "Привет, какой курс доллара?",
  "role": "user"
}
```

**Ответ:**
```json
{
  "response": "Привет! Сегодня лучший курс доллара...",
  "role": "user",
  "stats": {
    "total_messages": 5,
    "system_tokens": 150,
    "history_tokens": 500,
    "total_tokens": 650,
    "max_context_tokens": 30000,
    "usage_percent": 2.17
  }
}
```

## Пример интеграции в Telegram боте

### Минимальный пример:

```python
import requests

API_URL = "http://localhost:8000/chat/message"

async def handle_message(update, context):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Отправляем запрос в ваш API
    response = requests.post(API_URL, json={
        "user_id": user_id,
        "message": user_message,
        "role": "user"  # или получать из БД/кеша
    })
    
    result = response.json()
    
    # Отправляем ответ пользователю
    await update.message.reply_text(result["response"])
```

## Роли

API поддерживает 3 роли:

- `user` (по умолчанию) - Обычный клиент
- `employee` - Сотрудник банка  
- `investor` - Инвестор

Каждая роль имеет свой стиль общения и отдельную историю.

## Дополнительные эндпоинты

### Очистка истории: POST `/chat/clear`
```json
{
  "user_id": 123456789,
  "role": "user"  // опционально
}
```

### Статистика: GET `/chat/stats/{user_id}?role=user`

## Важные моменты

1. **История сохраняется автоматически** - каждый пользователь и роль имеют отдельную историю
2. **Автоматическая обрезка** - история обрезается при превышении лимита токенов
3. **Роли сохраняются** - при указании роли она сохраняется для пользователя
4. **Таймауты** - Gemini может обрабатывать запросы долго, установите таймаут ~30 секунд

## Тестирование API

### С помощью curl:

```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "message": "Привет!",
    "role": "user"
  }'
```

### С помощью Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/chat/message",
    json={
        "user_id": 123456789,
        "message": "Какой курс доллара?",
        "role": "user"
    }
)

print(response.json()["response"])
```

## Документация API

После запуска API доступна автоматическая документация:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Переменные окружения

Убедитесь, что в `.env` файле есть:
```
GEMINI_API_KEY=ваш_ключ
```

## Обработка ошибок

API возвращает стандартные HTTP коды:
- `200` - Успех
- `400` - Неверный запрос
- `500` - Ошибка сервера

При ошибке ответ содержит:
```json
{
  "detail": "Описание ошибки"
}
```

## Советы для Telegram бота

1. **Кеширование ролей** - сохраняйте выбранную роль пользователя в БД или памяти
2. **Обработка таймаутов** - Gemini может обрабатывать запросы 10-30 секунд
3. **Индикатор печати** - используйте `send_chat_action` для UX
4. **Обработка ошибок** - всегда обрабатывайте исключения при запросах к API

