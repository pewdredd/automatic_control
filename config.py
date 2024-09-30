import os
from dotenv import load_dotenv

load_dotenv()

# Настройки
WEBHOOK_URL = os.getenv('BITRIX24_WEBHOOK_URL')
SCHEDULE_HOURS = os.getenv('SCHEDULE_HOURS', '10,12,14,16,18')
SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE', '0'))
SCHEDULE_DAYS = os.getenv('SCHEDULE_DAYS', 'mon-fri') 

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL не установлен. Пожалуйста, проверьте файл .env.")
