import requests
from env_data import APP_KEY, APP_SECRET, REFRESH_TOKEN

def authenticate_dropbox():
    # URL для обновления Access Token
    TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"

    # Выполняем POST-запрос для обновления токена
    response = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }, auth=(APP_KEY, APP_SECRET))

    # Обрабатываем ответ
    if response.status_code == 200:
        new_tokens = response.json()
        print(new_tokens)
        return new_tokens["access_token"]
    else:
        print("Ошибка обновления токена:", response.status_code, response.text)
        return response.text

