from datetime import datetime, timedelta
import pytz
from bitrix24_api import call_api
from utils.user_utils import get_user_names


def get_completed_activities():
    """
    Функция для получения завершенных дел (активностей) внутри сделок за последние 2 часа.
    """
    ACTIVITIES_METHOD = 'crm.activity.list'

    # Текущее время и время 2 часа назад в часовом поясе Europe/Moscow
    timezone = pytz.timezone('Europe/Moscow')
    now = datetime.now(timezone)
    two_hours_ago = now - timedelta(hours=2)

    # Форматируем даты в строки в формате ISO 8601
    now_str = now.strftime('%Y-%m-%dT%H:%M:%S%z')

    two_hours_ago_str = two_hours_ago.strftime('%Y-%m-%dT%H:%M:%S%z')

    # Параметры запроса
    params = {
        'filter': {
            'COMPLETED': 'Y',      # Завершенные дела
            '<=LAST_UPDATED': two_hours_ago_str,
            'OWNER_TYPE_ID': 2,    # 2 соответствует DEAL (сделка)
            'TYPE_ID': 6,          # 6 соответствует TASK
        },
        'select': ['ID', 'SUBJECT', 'RESPONSIBLE_ID', 'OWNER_ID', 'OWNER_TYPE_ID', 'LAST_UPDATED']
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
            print("Ошибка при получении завершенных дел.")
            break

    return all_activities

def check_next_step_missing():
    """
    Проверка отсутствия следующего шага (дела) в течение 2 часов после завершения предыдущего дела в сделке.
    """
    completed_activities = get_completed_activities()
    print(f"[Проверка 2] Завершенных дел за последние 2 часа: {len(completed_activities)}")

    missing_next_steps = []

    # Текущее время в часовом поясе Europe/Moscow
    timezone = pytz.timezone('Europe/Moscow')
    now = datetime.now(timezone)

    for activity in completed_activities:
        activity_id = activity['ID']
        subject = activity['SUBJECT']
        responsible_id = activity['RESPONSIBLE_ID']
        last_updated_str = activity['LAST_UPDATED']
        owner_id = activity['OWNER_ID']  # ID сделки

        # Преобразуем END_TIME в datetime
        try:
            end_time = datetime.strptime(last_updated_str, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            print(f"Неверный формат даты в деле ID {activity_id}: {last_updated_str}")
            continue

        # Проверяем, есть ли незавершенные дела по этой сделке
        params = {
            'filter': {
                'OWNER_ID': owner_id,
                'OWNER_TYPE_ID': 2,  # Сделка
                'COMPLETED': 'N',    # Незавершенные дела
            },
            'select': ['ID', 'SUBJECT', 'START_TIME', 'LAST_UPDATED']
        }
        data = call_api('crm.activity.list', params=params, http_method='POST')

        if data and 'result' in data and data['result']:
            # Есть незавершенные дела — следующий шаг проставлен
            continue
        else:
            # Проверяем, прошло ли более 2 часов с момента завершения предыдущего дела

            time_diff = now - end_time.astimezone(timezone) 
            if time_diff > timedelta(hours=2):
                missing_next_steps.append({
                    'activity_id': activity_id,
                    'subject': subject,
                    'last_updated': last_updated_str,
                    'responsible_id': responsible_id,
                    'deal_id': owner_id,
                    'hours_since_completion': time_diff.total_seconds() / 3600
                })

    print(f"Дел без проставленного следующего шага более 2 часов: {len(missing_next_steps)}")

    if missing_next_steps:
        # Получаем имена ответственных
        user_ids = [item['responsible_id'] for item in missing_next_steps]
        user_names = get_user_names(user_ids)

        # Получаем названия сделок
        deal_ids = [item['deal_id'] for item in missing_next_steps]
        deal_info = get_deal_titles(deal_ids)

        # Выводим информацию
        print("\nСписок дел без проставленного следующего шага:")
        for item in missing_next_steps:
            responsible_name = user_names.get(item['responsible_id'], f"ID {item['responsible_id']}")
            deal_title = deal_info.get(item['deal_id'], f"ID {item['deal_id']}")
            print(f"Дело ID: {item['activity_id']}, Тема: {item['subject']}, Ответственный: {responsible_name}, Завершено: {item['last_updated']}, Сделка: {deal_title}, Часов с момента завершения: {item['hours_since_completion']:.2f}")
    else:
        print("Все дела имеют проставленный следующий шаг.")

    # Если потребуется, можно вернуть список для дальнейшей обработки
    return missing_next_steps

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
