# Учебный проект Яндекс-Практикум Yatube

Сообщество для публикаций. Блог с возможностями публикации постов, подписки на группы и авторов, а также комментирования постов.

# Технологии
Python 3.9
Django 2.2.19
pytest 6.2.4

## Инструкции по установке
***- Клонируйте репозиторий:***
```
git clone git@github.com:mishabutters/hw05_final.git
```

***- Установите и активируйте виртуальное окружение:***
- для MacOS
```
python3 -m venv venv
```
- для Windows
```
python -m venv venv
source venv/bin/activate
source venv/Scripts/activate
```

***- Установите зависимости из файла requirements.txt:***
```
pip install -r requirements.txt
```

***- Примените миграции:***
```
python manage.py migrate
```

***- В папке с файлом manage.py выполните команду:***
```
python manage.py runserver
```
