import config
import pytz

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from checks import *


def run_checks():
    """
    Функция для запуска всех проверок.
    """
    timezone = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nЗапуск проверок в {current_time}\n")

    try:
        # Проверка 1
        check_overdue_tasks()
        # Проверка 2
        check_next_step_missing()
        # Проверка 3
        check_deal_not_moved()

    except Exception as e:
        raise Exception(f"Произошла ошибка во время выполнения проверок: {str(e)}")


def main():
    """
    Главная функция, устанавливающая планировщик для запуска проверок.
    """

    schedule_hours = config.SCHEDULE_HOURS
    schedule_minute = config.SCHEDULE_MINUTE
    schedule_days = config.SCHEDULE_DAYS

    # Создаем планировщик
    scheduler = BlockingScheduler(timezone='Europe/Moscow')

    # # Создаем триггер для запуска в 10:00, 12:00, 14:00, 16:00, 18:00 по Москве в будние дни
    # trigger = CronTrigger(hour=schedule_hours, minute=schedule_minute, day_of_week=schedule_days)

    print("Тестовый запуск проверок...\n")
    run_checks()  # Directly call run_checks for testing purposes

    # # Добавляем задачу в планировщик
    # scheduler.add_job(run_checks, trigger)

    # print("Планировщик проверок запущен.")
    # print("Проверки будут выполняться каждые 2 часа с 10:00 до 18:00 МСК в будние дни.")

    # try:
    #     # Запускаем планировщик
    #     scheduler.start()
    # except (KeyboardInterrupt, SystemExit):
    #     print("Планировщик остановлен.")

if __name__ == "__main__":
    main()
