from checks.check_overdue_tasks import check_overdue_tasks

def main():
    print("Запуск проверок...\n")
    
    # Проверка 1: Просрочена задача (дело) более чем на 1 час
    check_overdue_tasks()


if __name__ == "__main__":
    main()
