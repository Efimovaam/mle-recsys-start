import requests

# Конфигурация
EVENTS_URL = "http://127.0.0.1:8020"
RECOMMENDATIONS_URL = "http://127.0.0.1:8000"

# 1. Сохраняем тестовое событие (POST запрос)
try:
    resp = requests.post(
        f"{EVENTS_URL}/put",
        params={"user_id": 1291248, "item_id": 17245},
        timeout=5
    )
    print("Event save response:", resp.status_code, resp.text)
except Exception as e:
    print("Error saving event:", str(e))

# 2. Получаем онлайн-рекомендации (POST запрос)
try:
    resp = requests.post(
        f"{RECOMMENDATIONS_URL}/recommendations_online",
        params={"user_id": 1291248, "k": 1},
        timeout=5
    )
    print("Recommendations response:", resp.status_code, resp.text)
    if resp.status_code == 200:
        online_recs = resp.json()
        print("Recommendations:", online_recs)
except Exception as e:
    print("Error getting recommendations:", str(e))