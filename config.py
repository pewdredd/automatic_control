import os
from dotenv import load_dotenv

load_dotenv()

# Настройки
WEBHOOK_URL = os.getenv('BITRIX24_WEBHOOK_URL') 

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL не установлен. Пожалуйста, проверьте файл .env.")
