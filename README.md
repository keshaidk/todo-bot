# Todo Bot

Telegram бот для управления задачами с напоминаниями и поддержкой повторяющихся задач.

## Возможности

-  Добавление задач с названием, описанием, датой и временем
-  Удобный календарь для выбора даты
-  Выбор времени через inline клавиатуру
-  Поддержка повторяющихся задач (ежедневные напоминания)
-  Редактирование задач (название, описание, дата, время)
-  Удаление задач
-  Отметка задач как выполненные
-  Автоматические напоминания за 30 минут до дедлайна
-  Список текущих задач

## Технологии

- Python 3.11+
- python-telegram-bot 21.5
- aiosqlite (асинхронная работа с SQLite)
- pydantic-settings (управление настройками)
- pytest (тестирование)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd todo-bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Заполните `.env`:
```
BOT_TOKEN=your_telegram_bot_token_here
DB_PATH=data/tasks.db
LOG_LEVEL=INFO
TZ=Europe/Moscow
```

## Получение BOT_TOKEN

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env`

## Запуск

```bash
python main.py
```

Бот запустится и начнет получать обновления. Нажмите `Ctrl+C` для остановки.

## Команды бота

- `/start` - Приветствие и справка
- `/add` - Добавить новую задачу
- `/tasks` - Показать список текущих задач
- `/cancel` - Отменить текущее действие

## Структура проекта

```
todo-bot/
├── bot/
│   ├── config.py          # Настройки приложения
│   ├── db/                # Работа с базой данных
│   │   ├── connection.py  # Подключение к SQLite
│   │   ├── repository.py # CRUD операции
│   │   └── migrations.py  # Миграции БД
│   ├── handlers/          # Обработчики команд
│   │   ├── add_task.py    # Добавление задач
│   │   ├── edit_task.py   # Редактирование задач
│   │   ├── tasks_list.py  # Список задач
│   │   ├── start.py       # Команда /start
│   │   └── errors.py      # Обработка ошибок
│   ├── keyboards.py       # Inline клавиатуры
│   ├── reminders.py       # Напоминания
│   └── utils/             # Утилиты
│       ├── datetime_helpers.py
│       └── formatters.py
├── data/                  # Директория для БД
├── tests/                 # Тесты
├── main.py                # Точка входа
├── requirements.txt       # Зависимости
└── .env.example           # Пример конфигурации
```

## Тестирование

```bash
pytest
```

## Docker (опционально)

Сборка образа:
```bash
docker build -t todo-bot .
```

Запуск контейнера:
```bash
docker run -d --env-file .env -v $(pwd)/data:/app/data todo-bot
```

## Безопасность

- Используются параметризованные SQL-запросы для защиты от SQL Injection
- Валидация всех входных данных (даты, время)
- Настройки хранятся в переменных окружения
- Отсутствие hardcoded секретов

## Лицензия

MIT
