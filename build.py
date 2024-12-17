import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv(".env")

# Список переменных, которые нужно включить
env_variables = {
    "APP_KEY": os.getenv("APP_KEY"),
    "APP_SECRET": os.getenv("APP_SECRET"),
    "REFRESH_TOKEN": os.getenv("REFRESH_TOKEN")
}

# Генерация временного файла с переменными
with open("env_data.py", "w") as f:
    for key, value in env_variables.items():
        if value is None:
            raise ValueError(f"Переменная {key} не найдена в .env")
        f.write(f'{key} = "{value}"\n')

print("Переменные окружения встроены в env_data.py.")
