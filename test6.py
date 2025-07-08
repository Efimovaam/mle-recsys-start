import requests

# Конфигурация
RECOMMENDATIONS_URL = "http://127.0.0.1:8000"

# 2. Получаем онлайн-рекомендации (POST запрос)
resp = requests.post(
        f"{RECOMMENDATIONS_URL}/recommendations_online",
        params={"user_id": 1291248, "k": 1}
    )
print("Recommendations response:", resp.status_code, resp.text)
print("Recommendations response:",resp.json())