# 🚀 Быстрый запуск системы

## 📋 Ваши данные для настройки

### 🔑 Токен и доступы:
- **BOT_TOKEN**: `8607512419:AAH8OTETCXHALbr5SRMtaRo0wfaJV4UW7ng`
- **ADMIN_TELEGRAM_ID**: `864433722`
- **База данных**: `postgres:postgres@localhost:5432/project_cleaning`

### 🏙️ Города и Telegram темы:
- Краснодар - `3824746585_27`
- Красноярск - `3824746585_25`
- Пермь - `3824746585_23`
- Самара - `3824746585_21`
- Нижний Новгород - `3824746585_19`
- Воронеж - `3824746585_17`
- Казань - `3824746585_13`
- Уфа - `3824746585_11`
- Омск - `3824746585_9`
- Ростов-на-Дону - `3824746585_4`
- Новосибирск - `3824746585_2`

## ⚙️ Настройка и запуск

### 1. Создайте .env файл:
```bash
# Скопируйте этот текст в файл .env
BOT_TOKEN=8607512419:AAH8OTETCXHALbr5SRMtaRo0wfaJV4UW7ng
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/project_cleaning
ADMIN_TELEGRAM_ID=864433722
ADMIN_USERNAME=admin
PHOTOS_PATH=./photos
PDF_PATH=./pdfs
LOG_LEVEL=INFO
LOG_FILE=./logs/bot.log
DEBUG=False
ENVIRONMENT=production
```

### 2. Установите зависимости:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Настройте базу данных:
```bash
# Создайте базу данных project_cleaning в PostgreSQL
# Затем выполните:
python scripts/init_database.py
python scripts/setup_cities.py
```

### 4. Запустите бота:
```bash
python bot/main.py
```

## 🎞️ Первые шаги

1. **Администратор**: Запустите бота и отправьте `/start`
2. **Добавьте менеджеров**: Через админ-панель добавьте менеджеров
3. **Настройте группы**: Убедитесь что бот имеет права администратора в супергруппе
4. **Тестирование**: Создайте тестовый заказ и проверьте работу системы

## 📞 Поддержка

Если возникнут проблемы:
1. Проверьте логи в `logs/bot.log`
2. Убедитесь что PostgreSQL запущен
3. Проверьте права доступа к файлам

---

**Система готова к работе! 🎉**
