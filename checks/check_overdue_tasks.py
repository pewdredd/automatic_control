from datetime import datetime, timedelta
import pytz
from bitrix24_api import call_api
from utils.user_utils import get_user_names

def get_overdue_activities():
    """
    Функция для получения дел (активностей) внутри сделок CRM, которые просрочены более чем на 1 час.
    """
    ACTIVITIES_METHOD = 'crm.activity.list'

    # Текущее время и время 1 час назад в часовом поясе Europe/Moscow
    timezone = pytz.timezone('Europe/Moscow')
    now = datetime.now(timezone)
    one_hour_ago = now - timedelta(hours=1)

    # Форматируем дату в строку в формате ISO 8601
    one_hour_ago_str = one_hour_ago.strftime('%Y-%m-%dT%H:%M:%S%z')

    # Параметры запроса
    params = {
        'filter': {
            'COMPLETED': 'N',  # Незавершенные дела
            '<=DEADLINE': one_hour_ago_str, # Дедлайн меньше или равен времени 1 час назад
            'OWNER_TYPE_ID': 2,  # 2 соответствует сделке
            # Здесь можно добавить фильтр по воронке, если требуется
        },
        'select': ['ID', 'SUBJECT', 'DEADLINE', 'RESPONSIBLE_ID', 'CREATED', 'OWNER_ID', 'OWNER_TYPE_ID']
    }

    all_activities = []
    start = 0

    while True:
        params['start'] = start
        data = call_api(ACTIVITIES_METHOD, params=params, http_method='POST')
        if data and 'result' in data and data['result']:
            activities = data['result']
            all_activities.extend(activities)

            if 'next' in data:
                start = data['next']
            else:
                break
        else:
            print("Ошибка при получении дел.")
            break

    return all_activities

def check_overdue_activities():
    """
    Проверка просроченных дел (активностей) внутри сделок и вывод результатов.
    """
    overdue_activities = get_overdue_activities()
    print(f"[Проверка 1] Просроченных дел более чем на 1 час: {len(overdue_activities)}")

    if overdue_activities:
        # Собираем уникальные ID ответственных
        user_ids = [activity['RESPONSIBLE_ID'] for activity in overdue_activities]
        user_names = get_user_names(user_ids)

        # Получаем информацию о сделках
        deal_ids = [activity['OWNER_ID'] for activity in overdue_activities if activity['OWNER_TYPE_ID'] == '2']
        deal_info = get_deal_titles(deal_ids)

        print("\nСписок просроченных дел:")
        for activity in overdue_activities:
            responsible_id = activity['RESPONSIBLE_ID']
            responsible_name = user_names.get(responsible_id, f"ID {responsible_id}")
            deadline = activity['DEADLINE']
            subject = activity['SUBJECT']
            activity_id = activity['ID']
            deal_id = activity['OWNER_ID']
            deal_title = deal_info.get(deal_id, f"ID {deal_id}")

            print(f"Дело ID: {activity_id}, Тема: {subject}, Ответственный: {responsible_name}, Дедлайн: {deadline}, Сделка: {deal_title}")
    else:
        print("Нет просроченных дел.")

    # Если потребуется, можно вернуть список просроченных дел для дальнейшей обработки
    return overdue_activities

def get_deal_titles(deal_ids):
    """
    Функция для получения названий сделок по их ID.
    """
    DEALS_METHOD = 'crm.deal.list'
    deal_titles = {}

    unique_deal_ids = list(set(deal_ids))
    batch_size = 50  # Ограничение на количество элементов в одном запросе

    for i in range(0, len(unique_deal_ids), batch_size):
        batch_ids = unique_deal_ids[i:i + batch_size]
        params = {
            'filter': {
                'ID': batch_ids
            },
            'select': ['ID', 'TITLE']
        }
        data = call_api(DEALS_METHOD, params=params, http_method='POST')
        if data and 'result' in data:
            deals = data['result']
            for deal in deals:
                deal_id = deal['ID']
                deal_title = deal['TITLE']
                deal_titles[deal_id] = deal_title
        else:
            print("Ошибка при получении информации о сделках.")
            continue

    return deal_titles
