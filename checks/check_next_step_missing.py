from datetime import datetime, timedelta
import pytz
from bitrix24_api import call_api
from utils.user_utils import get_user_names


def get_completed_tasks():
    """
    Функция для получения завершенных задач за последние 2 часа.
    """
    TASKS_METHOD = 'tasks.task.list'

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
            'STATUS': 5,  # Завершенные задачи (STATUS = 5 означает завершено)
            '>=CLOSED_DATE': two_hours_ago_str,  # Время закрытия задачи >= 2 часа назад
            '<=CLOSED_DATE': now_str,            # Время закрытия задачи <= сейчас
        },
        'select': ['ID', 'TITLE', 'RESPONSIBLE_ID', 'CLOSED_DATE']
    }

    all_tasks = []
    start = 0

    while True:
        params['start'] = start
        data = call_api(TASKS_METHOD, params=params, http_method='POST')
        
        if data and 'result' in data:
            tasks = data['result']['tasks']
            all_tasks.extend(tasks)

            if 'next' in data['result']:
                start = data['result']['next']
            else:
                break
        else:
            print("Ошибка при получении завершенных задач.")
            break

    return all_tasks


def check_next_step_missing():
    """
    Проверка отсутствия следующего шага (дела) в течение 2 часов после завершения предыдущей задачи.
    """
    completed_tasks = get_completed_tasks()
    print(f"[Проверка 2] Завершенные задачи за последние 2 часа: {len(completed_tasks)}")

    missing_next_steps = []

    # Текущее время и время 2 часа назад в часовом поясе Europe/Moscow
    timezone = pytz.timezone('Europe/Moscow')
    now = datetime.now(timezone)

    # Проверяем для каждой завершенной задачи наличие следующего шага
    for task in completed_tasks:
        task_id = task['id']
        title = task['title']
        responsible_id = task['responsibleId']
        closed_date_str = task['closedDate']

        # Преобразуем closedDate в datetime
        try:
            closed_date = datetime.strptime(closed_date_str, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            print(f"Неверный формат даты в задаче ID {task_id}: {closed_date_str}")
            continue

        # Проверяем, есть ли незавершенные задачи по этому ответственному
        params = {
            'filter': {
                'RESPONSIBLE_ID': responsible_id,
                'STATUS': '<5'  # Незавершенные задачи (все статусы меньше 5 считаются незавершенными)
            },
            'select': ['ID', 'TITLE', 'STATUS']
        }
        data = call_api('tasks.task.list', params=params, http_method='POST')

        if data and 'result' in data and data['result']['tasks']:
            # Есть незавершенные задачи — следующий шаг проставлен
            continue
        else:
            # Проверяем, прошло ли более 2 часов с момента завершения задачи
            time_diff = now - closed_date.astimezone(timezone)
            if time_diff > timedelta(hours=2):
                missing_next_steps.append({
                    'task_id': task_id,
                    'title': title,
                    'closed_date': closed_date_str,
                    'responsible_id': responsible_id
                })

    print(f"Задач без проставленного следующего шага более 2 часов: {len(missing_next_steps)}")

    if missing_next_steps:
        # Получаем имена ответственных
        user_ids = [item['responsible_id'] for item in missing_next_steps]
        user_names = get_user_names(user_ids)

        # Выводим информацию
        print("\nСписок задач без проставленного следующего шага:")
        for item in missing_next_steps:
            responsible_name = user_names.get(item['responsible_id'], f"ID {item['responsible_id']}")
            print(f"Задача ID: {item['task_id']}, Название: {item['title']}, Ответственный: {responsible_name}, Завершена: {item['closed_date']}")
    else:
        print("Все задачи имеют проставленный следующий шаг.")

    # Если потребуется, можно вернуть список для дальнейшей обработки
    return missing_next_steps