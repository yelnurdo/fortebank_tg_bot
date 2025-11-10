import requests


API_URL = "https://82a42ed9035d.ngrok-free.app//chat/message"

response = requests.post(API_URL, json={
    "user_id": 1,
    "message": "Привет помнишь меня?",
    "role": "user"
})
result = response.json()
print(result)

print("--------------------------------")

answer = result["response"]
print(answer)