from bitrix24_api import call_api

def get_user_names(user_ids):
    """
    Функция для получения имен пользователей по их ID.
    """
    user_names = {}
    unique_user_ids = list(set(user_ids))

    for user_id in unique_user_ids:
        params = {'ID': user_id}
        data = call_api('user.get', params=params, http_method='GET')
        if data and 'result' in data and data['result']:
            user = data['result'][0]
            user_names[user_id] = f"{user['NAME']} {user['LAST_NAME']}"
        else:
            print(f"Не удалось получить данные для пользователя ID {user_id}")
            user_names[user_id] = f"ID {user_id}"

    return user_names
