from datetime import datetime, timedelta
import pytz
from bitrix24_api import call_api
from utils.user_utils import get_user_names

def get_overdue_tasks():
    """
    Функция для получения задач, которые просрочены более чем на 1 час.
    """
    TASKS_METHOD = 'tasks.task.list'

    # Текущее время и время 1 час назад в часовом поясе Europe/Moscow
    timezone = pytz.timezone('Europe/Moscow')
    now = datetime.now(timezone)
    one_hour_ago = now - timedelta(hours=1)

    # Форматируем дату в строку в формате ISO 8601
    one_hour_ago_str = one_hour_ago.strftime('%Y-%m-%dT%H:%M:%S%z')

    # Параметры запроса
    params = {
        'select': ['id', 'title', 'status', 'deadline', 'createdDate', 'createdBy', 'responsibleId'],
        'filter': {
            '!status': [5, 7],  # Исключаем отклоненные (5) и завершенные (7) задачи
            '<=DEADLINE': one_hour_ago_str,  # Дедлайн меньше или равен времени 1 час назад
            '!DEADLINE': None  # Исключаем задачи без дедлайна
        }
    }

    all_tasks = []
    start = 0

    while True:
        params['start'] = start
        data = call_api(TASKS_METHOD, params=params, http_method='POST')
        if data and 'result' in data and 'tasks' in data['result']:
            tasks = data['result']['tasks']
            all_tasks.extend(tasks)

            if 'next' in data:
                start = data['next']
            else:
                break
        else:
            print("Ошибка при получении задач.")
            break

    return all_tasks

def check_overdue_tasks():
    """
    Проверка просроченных задач и вывод результатов.
    """
    overdue_tasks = get_overdue_tasks()
    print(f"[Проверка 1] Просроченных задач более чем на 1 час: {len(overdue_tasks)}")

    if overdue_tasks:
        # Собираем уникальные ID пользователей (постановщиков и исполнителей)
        user_ids = [task['createdBy'] for task in overdue_tasks] + [task['responsibleId'] for task in overdue_tasks]
        user_names = get_user_names(user_ids)

        print("\nСписок просроченных задач:")
        for task in overdue_tasks:
            creator_id = task['createdBy']
            responsible_id = task['responsibleId']
            creator_name = user_names.get(creator_id, f"ID {creator_id}")
            responsible_name = user_names.get(responsible_id, f"ID {responsible_id}")

            print(f"ID: {task['id']}, Название: {task['title']}, Постановщик: {creator_name}, Исполнитель: {responsible_name}, Дедлайн: {task['deadline']}")
    else:
        print("Нет просроченных задач.")

    # Если потребуется, можно вернуть список просроченных задач для дальнейшей обработки
    return overdue_tasks
