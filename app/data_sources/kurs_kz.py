from requests_html import HTMLSession
import json
import os
from datetime import datetime

session = HTMLSession()
r = session.get("https://kurs.kz/site/index?city=astana")
r.html.render(timeout=20)
# print(r.html.html[:1000])

rows = r.html.find("tbody tr")
data = []

for row in rows:
    name_tag = row.find("a.tab", first=True)
    if not name_tag:
        continue
    # usd_buy = row.find('span[title="USD - покупка"]', first=True)
    # usd_sell = row.find('span[title="USD - продажа"]', first=True)
    # if name_tag and usd_buy and usd_sell:
    #     data.append({
    #         "name": name_tag.text.strip(),
    #         "usd_buy": usd_buy.text.strip(),
    #         "usd_sell": usd_sell.text.strip()
    #     })

    usd_buy = usd_sell = None
    for td in row.find("td"):
        if td.find('span[title="USD - покупка"]', first=True):
            buy_el = td.find('span[title="USD - покупка"]', first=True)
            sell_el = td.find('span[title="USD - продажа"]', first=True)
            if buy_el:
                usd_buy = buy_el.text.strip()
            if sell_el:
                usd_sell = sell_el.text.strip()
            break
    eur_buy = eur_sell = None
    for td in row.find("td"):
        if td.find('span[title="EUR - покупка"]', first=True):
            buy_el = td.find('span[title="EUR - покупка"]', first=True)
            sell_el = td.find('span[title="EUR - продажа"]', first=True)
            if buy_el:
                eur_buy = buy_el.text.strip()
            if sell_el:
                eur_sell = sell_el.text.strip()
    rub_buy = rub_sell = None
    for td in row.find("td"):
        if td.find('span[title="RUB - покупка"]', first=True):
            buy_el = td.find('span[title="RUB - покупка"]', first=True)
            sell_el = td.find('span[title="RUB - продажа"]', first=True)
            if buy_el:
                rub_buy = buy_el.text.strip()
            if sell_el:
                rub_sell = sell_el.text.strip()
    data.append({
        "name": name_tag.text.strip(),
        "usd_buy": usd_buy,
        "usd_sell": usd_sell,
        "eur_buy": eur_buy,
        "eur_sell": eur_sell,
        "rub_buy": rub_buy,
        "rub_sell": rub_sell
    })

os.makedirs("parsed_data", exist_ok=True)
output = {
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "data": data
}

with open("parsed_data/kurs_kz_astana_kurs_valyut.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
    print("Data saved to parsed_data/kurs_kz_astana_kurs_valyut.json")


print(f"Data saved with date: {output['date']}")
