from datetime import datetime, timedelta
import pytz
from bitrix24_api import call_api
from utils.user_utils import get_user_names

def get_contacts_without_name():
    """
    Функция для получения контактов без заполненного имени.
    """
    CONTACTS_METHOD = 'crm.contact.list'

    # Параметры запроса
    params = {
        'filter': {
            'NAME': 'Без имени',  # Имя не указано 
            '!PHONE': ''  # У контакта есть телефон
        },
        'select': ['ID', 'NAME', 'LAST_NAME', 'PHONE', 'ASSIGNED_BY_ID', 'CREATED_BY_ID']
    }

    all_contacts = []
    start = 0

    while True:
        params['start'] = start
        data = call_api(CONTACTS_METHOD, params=params, http_method='POST')

        if data and 'result' in data:
            contacts = data['result']
            all_contacts.extend(contacts)

            if 'next' in data:
                start = data['next']
            else:
                break
        else:
            print("Ошибка при получении списка контактов.")
            break

    return all_contacts


def get_first_call_time(contact_id):
    """
    Функция для получения времени первого исходящего звонка клиенту
    и данных о пользователе, совершившем звонок.
    """
    ACTIVITIES_METHOD = 'crm.activity.list'

    params = {
        'filter': {
            'TYPE_ID': 2,         # Тип активности: звонок
            'DIRECTION': 2,       # Направление: исходящий звонок
            'COMPLETED': 'Y',     # Завершенные звонки
            '>=START_TIME': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S%z')
        },
        'order': {
            'START_TIME': 'ASC'   # Сортируем по времени начала (от старых к новым)
        },
        'select': ['ID', 'START_TIME', 'RESPONSIBLE_ID']
    }

    start = 0
    while True:
        params['start'] = start
        data = call_api(ACTIVITIES_METHOD, params=params, http_method='POST')

        # Проверяем, есть ли результат в данных
        if data and 'result' in data and data['result']:
            activities = data['result']
            
            # Перебираем все активности, чтобы найти первую подходящую
            for activity in activities:
                # Проверяем, что активность имеет поле 'START_TIME' и 'RESPONSIBLE_ID'
                first_call_time_str = activity.get('START_TIME')
                responsible_id = activity.get('RESPONSIBLE_ID')  # ID пользователя, совершившего звонок
                
                if first_call_time_str and responsible_id:
                    try:
                        first_call_time = datetime.strptime(first_call_time_str, '%Y-%m-%dT%H:%M:%S%z')
                        return first_call_time
                    except ValueError:
                        print(f"Неверный формат даты для звонка контакта ID {contact_id}: {first_call_time_str}")
                        return None
            
            # Переходим к следующей странице, если есть
            if 'next' in data:
                start = data['next']
            else:
                break
        else:
            # Нет данных или произошла ошибка
            print(f"Ошибка при получении активностей: {data.get('error_description', 'Неизвестная ошибка')}")
            break
    # Если не нашли подходящей активности
    return None    

def check_contact_name_missing():
    """
    Проверка контактов, у которых не заполнено имя клиента и прошло более 3 часов с момента первого звонка.
    """
    contacts = get_contacts_without_name()
    print(f"[Проверка 4] Контактов без имени: {len(contacts)}")

    contacts_to_notify = []

    timezone = pytz.timezone('Europe/Moscow')
    now = datetime.now(timezone)

    for contact in contacts:
        contact_id = contact['ID']
        phone_numbers = contact.get('PHONE', [])

        # Пропускаем контакт, если нет номера телефона
        if not phone_numbers:
            continue

        assigned_by_id = contact.get('ASSIGNED_BY_ID')
        created_by_id = contact.get('CREATED_BY_ID')

        # Проверяем, был ли звонок этому контакту
        first_call_time = get_first_call_time(contact_id)

        if first_call_time:
            time_since_first_call = now - first_call_time.astimezone(timezone)

            if time_since_first_call > timedelta(hours=3):
                contacts_to_notify.append({
                    'contact_id': contact_id,
                    'phone_numbers': [phone['VALUE'] for phone in phone_numbers],
                    'first_call_time': first_call_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'hours_since_first_call': time_since_first_call.total_seconds() / 3600,
                    'assigned_by_id': assigned_by_id,
                    'created_by_id': created_by_id
                })
        else:
            # Если звонков не было, пропускаем контакт
            continue

    print(f"Контактов без имени, у которых прошло более 3 часов с момента первого звонка: {len(contacts_to_notify)}")

    if contacts_to_notify:
        # Собираем уникальные ID пользователей
        user_ids = set()
        for item in contacts_to_notify:
            if item['assigned_by_id']:
                user_ids.add(item['assigned_by_id'])
            if item['created_by_id']:
                user_ids.add(item['created_by_id'])

        # Получаем имена пользователей
        user_names = get_user_names(list(user_ids))

        # Выводим информацию
        print("\nСписок таких контактов:")
        for item in contacts_to_notify:
            assigned_by_id = item['assigned_by_id']
            created_by_id = item['created_by_id']
            assigned_by_name = user_names.get(assigned_by_id, f"ID {assigned_by_id}")
            created_by_name = user_names.get(created_by_id, f"ID {created_by_id}")

            print(
                f"Контакт ID: {item['contact_id']}, "
                f"Телефон: {', '.join(item['phone_numbers'])}, "
                f"Первый звонок: {item['first_call_time']}, "
                f"Часов с момента первого звонка: {item['hours_since_first_call']:.2f}, "
                f"Ответственный: {assigned_by_name} (ID {assigned_by_id}), "
                f"Создал: {created_by_name} (ID {created_by_id})"
            )
    else:
        print("Нет контактов, соответствующих условиям.")

    # Если потребуется, можно вернуть список для дальнейшей обработки
    return contacts_to_notify