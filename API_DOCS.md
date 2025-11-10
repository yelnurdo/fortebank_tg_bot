# API Документация для Telegram бота

Этот API предназначен для обработки запросов от отдельного Telegram бота.

## Базовый URL

```
http://localhost:8000
```

## Эндпоинты

### 1. Обработка сообщения

**POST** `/chat/message`

Обработать сообщение от пользователя Telegram и получить ответ от Gemini модели.

#### Запрос

```json
{
  "user_id": 123456789,
  "message": "Привет, какой курс доллара?",
  "role": "user"
}
```

#### Параметры

- `user_id` (int, обязательный) - ID пользователя Telegram
- `message` (string, обязательный) - Текст сообщения от пользователя
- `role` (string, опциональный) - Роль пользователя: `user`, `employee`, `investor`. По умолчанию: `user`

#### Ответ

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

#### Пример использования (Python)

```python
import requests

url = "http://localhost:8000/chat/message"
data = {
    "user_id": 123456789,
    "message": "Какой курс евро?",
    "role": "user"
}

response = requests.post(url, json=data)
result = response.json()

print(result["response"])  # Ответ от модели
```

#### Пример использования (cURL)

```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "message": "Какой курс евро?",
    "role": "user"
  }'
```

---

### 2. Очистка истории

**POST** `/chat/clear`

Очистить историю чата для пользователя.

#### Запрос

```json
{
  "user_id": 123456789,
  "role": "user"
}
```

#### Параметры

- `user_id` (int, обязательный) - ID пользователя Telegram
- `role` (string, опциональный) - Роль для очистки. Если не указана, очищается вся история пользователя

#### Ответ

```json
{
  "success": true,
  "message": "История для пользователя 123456789 и роли user очищена"
}
```

---

### 3. Получение статистики

**GET** `/chat/stats/{user_id}?role=user`

Получить статистику использования токенов для пользователя.

#### Параметры URL

- `user_id` (int, обязательный) - ID пользователя Telegram
- `role` (string, query параметр, опциональный) - Роль для получения статистики

#### Ответ

```json
{
  "total_messages": 10,
  "system_tokens": 150,
  "history_tokens": 1200,
  "total_tokens": 1350,
  "max_context_tokens": 30000,
  "usage_percent": 4.5
}
```

#### Пример использования

```bash
curl "http://localhost:8000/chat/stats/123456789?role=user"
```

---

## Роли

API поддерживает 3 роли с разными стилями общения:

1. **user** (по умолчанию) - Обычный клиент
   - Простой язык, дружелюбный тон
   - Эмодзи и короткие фразы

2. **employee** - Сотрудник банка
   - Формальный и профессиональный стиль
   - Банковская лексика

3. **investor** - Инвестор
   - Аналитический стиль
   - Цифры и оценка риска

---

## Интеграция с Telegram ботом

### Пример обработки сообщений в Telegram боте

```python
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import requests

API_URL = "http://localhost:8000/chat/message"

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Отправляем запрос в API
    response = requests.post(API_URL, json={
        "user_id": user_id,
        "message": user_message,
        "role": "user"  # или получать из базы данных
    })
    
    result = response.json()
    
    # Отправляем ответ пользователю
    await update.message.reply_text(result["response"])

# Регистрация обработчика
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)
```

### Обработка команды /role

```python
async def role_command(update: Update, context):
    user_id = update.effective_user.id
    role = context.args[0] if context.args else "user"
    
    # Сохраняем роль (можно в БД)
    # При следующем сообщении передаем role в API
    await update.message.reply_text(f"Роль изменена на: {role}")

# При обработке сообщения используем сохраненную роль
async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Получаем сохраненную роль для пользователя
    user_role = get_user_role(user_id)  # из БД или кеша
    
    response = requests.post(API_URL, json={
        "user_id": user_id,
        "message": user_message,
        "role": user_role
    })
    
    result = response.json()
    await update.message.reply_text(result["response"])
```

---

## Запуск API

```bash
python main.py
```

API будет доступен по адресу: `http://localhost:8000`

Для продакшена используйте:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Обработка ошибок

API возвращает стандартные HTTP коды:

- `200` - Успешный запрос
- `400` - Неверные параметры запроса
- `500` - Внутренняя ошибка сервера

При ошибке ответ будет содержать:
```json
{
  "detail": "Описание ошибки"
}
```

