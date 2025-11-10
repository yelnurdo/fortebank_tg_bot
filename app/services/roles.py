"""Role definitions and prompts for different user types."""

import json
from pathlib import Path

# Путь к файлу с курсами валют
CURRENCY_DATA_PATH = Path(__file__).parent.parent / "data_sources" / "parsed_data" / "kurs_kz_astana_kurs_valyut.json"


def load_currency_data() -> str:
    """Загрузить данные о курсах валют из JSON файла."""
    try:
        if CURRENCY_DATA_PATH.exists():
            with open(CURRENCY_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Форматируем данные для промпта
                currency_info = f"\n\nАктуальные курсы валют (дата: {data.get('date', 'неизвестно')}):\n"
                currency_info += json.dumps(data.get("data", []), ensure_ascii=False, indent=2)
                return currency_info
        else:
            return "\n\n(Данные о курсах валют временно недоступны)"
    except Exception as e:
        return f"\n\n(Ошибка загрузки данных о курсах: {e})"


def get_base_prompts() -> dict:
    """Получить базовые промпты без данных о валютах."""
    return {
    "user": """Ты финансовый помощник для обычных клиентов. 

Отвечай просто, дружелюбно, без терминов. Используй эмодзи и короткие фразы. 

Главное — помочь человеку понять, где сегодня лучший курс по USD, EUR и RUB.

Важные термины:
- currency_buy (или usd_buy, eur_buy, rub_buy) - это курс, по которому банк ПОКУПАЕТ валюту у клиентов
- currency_sell (или usd_sell, eur_sell, rub_sell) - это курс, по которому банк ПРОДАЕТ валюту клиентам

Для клиента:
- Лучший курс покупки = максимальный currency_sell (клиент продает валюту банку)
- Лучший курс продажи = минимальный currency_buy (клиент покупает валюту у банка)""",
    "employee": """Ты корпоративный финансовый ассистент банка. 

Общайся формально и профессионально. Можно использовать банковскую лексику. 

Кроме курсов, упоминай актуальные продукты банка (депозиты, облигации, ПИФы) для рекомендаций клиентам.

Важные термины:
- currency_buy (или usd_buy, eur_buy, rub_buy) - это курс, по которому банк ПОКУПАЕТ валюту у клиентов
- currency_sell (или usd_sell, eur_sell, rub_sell) - это курс, по которому банк ПРОДАЕТ валюту клиентам

Для клиента:
- Лучший курс покупки = максимальный currency_sell (клиент продает валюту банку)
- Лучший курс продажи = минимальный currency_buy (клиент покупает валюту у банка)""",
    "investor": """Ты инвестиционный аналитик. 

Отвечай кратко, с цифрами и оценкой риска. 

Фокус — на выгодных инструментах (облигации, золото, акции, FX-депозиты). 

Добавляй советы, но без лишних объяснений. Используй лаконичный аналитический стиль.

Важные термины:
- currency_buy (или usd_buy, eur_buy, rub_buy) - это курс, по которому банк ПОКУПАЕТ валюту у клиентов
- currency_sell (или usd_sell, eur_sell, rub_sell) - это курс, по которому банк ПРОДАЕТ валюту клиентам

Для клиента:
- Лучший курс покупки = максимальный currency_sell (клиент продает валюту банку)
- Лучший курс продажи = минимальный currency_buy (клиент покупает валюту у банка)""",
}


def get_role_prompt(role: str) -> str:
    """Получить промпт для указанной роли с актуальными данными о валютах."""
    base_prompts = get_base_prompts()
    base_prompt = base_prompts.get(role, base_prompts["user"])
    
    # Добавляем данные о курсах валют
    currency_data = load_currency_data()
    
    return base_prompt + currency_data


def is_valid_role(role: str) -> bool:
    """Проверить, является ли роль валидной."""
    base_prompts = get_base_prompts()
    return role in base_prompts

