import os
import time
import glob
import logging


def get_last_char(s: str) -> int:
    if s:  # проверка на пустую строку
        return s[-1]
    else:
        return 0


def delete_oldScreens():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Предполагается, что скрипт находится в корне проекта
    # Если скрипт находится внутри поддиректории, используйте os.path.join() для поднятия на уровень выше
    project_dir = script_dir  # Или os.path.abspath(os.path.join(script_dir, '..')) если нужно подняться выше

    folder_path = project_dir
    
    # Поиск всех файлов, содержащих "screen" в имени
    files_to_delete = glob.glob(os.path.join(folder_path, '*screen*'))

    # Удаление найденных файлов
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            logging.info(f'deleted: {file_path}')
        except Exception as e:
            logging.info(f'error deleting {file_path}: {e}')



LOCK_FILE = 'locked_accounts.txt'


def is_account_locked(account_id):
    """Проверяет, заблокирован ли аккаунт"""
    if not os.path.exists(LOCK_FILE):
        return False
    with open(LOCK_FILE, 'r') as f:
        locked_accounts = f.read().splitlines()

    
    return any(f"{account_id}:" in entry for entry in locked_accounts)

def lock_account(account_id, SCRIPT_ID):
    """Блокирует аккаунт, добавляя его в файл с идентификатором скрипта"""
    with open(LOCK_FILE, 'a') as f:
        f.write(f"{account_id}:{SCRIPT_ID}\n")
    print(f"Аккаунт {account_id} заблокирован скриптом {SCRIPT_ID}.")

def unlock_account(account_id, SCRIPT_ID):
    """Разблокирует аккаунт, удаляя только записи с идентификатором текущего скрипта"""
    if not os.path.exists(LOCK_FILE):
        return
    with open(LOCK_FILE, 'r') as f:
        locked_accounts = f.read().splitlines()

    # Удаляем только те записи, которые принадлежат текущему скрипту
    locked_accounts = [entry for entry in locked_accounts if entry != f"{account_id}:{SCRIPT_ID}"]

    with open(LOCK_FILE, 'w') as f:
        f.write('\n'.join(locked_accounts) + '\n')
    print(f"Аккаунт {account_id} разблокирован скриптом {SCRIPT_ID}.")


def remove_key_lines(file_path, key):
    try:
        # Чтение всех строк из файла
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Проходим по списку с конца и удаляем элементы, которые содержат ключ
        for i in range(len(lines) - 1, -1, -1):
            if key in lines[i]:
                lines.pop(i)  # Удаляем строку, если она содержит ключ

        # Записываем обновленный список обратно в файл
        with open(file_path, 'w') as file:
            file.writelines(lines)
            file.write(f"\n")

        print(f"Все строки, содержащие '{key}', были удалены из файла {file_path}.")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")


def remove_empty_lines(file_path):
    try:
        # Открываем файл и читаем все строки
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Фильтруем строки, исключая пустые строки (или строки, состоящие только из пробелов)
        non_empty_lines = [line for line in lines if line.strip()]

        # Записываем непустые строки обратно в файл
        with open(file_path, 'w') as file:
            file.writelines(non_empty_lines)

        print(f"Все пустые строки удалены из файла {file_path}.")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")


#написать функцию для очистки файла от пустых строчек
