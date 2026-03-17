# 🚀 Руководство по развертыванию системы

## 📋 Содержание
1. [Подготовка сервера](#подготовка-сервера)
2. [Настройка базы данных](#настройка-базы-данных)
3. [Конфигурация приложения](#конфигурация-приложения)
4. [Развертывание](#развертывание)
5. [Настройка Telegram бота](#настройка-telegram-бота)
6. [Мониторинг и логирование](#мониторинг-и-логирование)
7. [Обновление системы](#обновление-системы)
8. [Резервное копирование](#резервное-копирование)

## 🖥️ Подготовка сервера

### Требования к серверу
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: минимум 2GB, рекомендуется 4GB+
- **CPU**: минимум 2 ядра, рекомендуется 4+
- **Диск**: минимум 20GB SSD
- **Сеть**: стабильное подключение к интернету

### Установка зависимостей

#### Ubuntu/Debian
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip git postgresql postgresql-contrib nginx -y

# Установка дополнительных пакетов
sudo apt install build-essential libpq-dev -y
```

#### CentOS/RHEL
```bash
# Обновление системы
sudo yum update -y

# Установка Python и зависимостей
sudo yum install python3.11 python3.11-devel python3-pip git postgresql-server postgresql-contrib nginx -y

# Установка дополнительных пакетов
sudo yum groupinstall "Development Tools" -y
sudo yum install libpq-devel -y
```

### Настройка PostgreSQL
```bash
# Инициализация базы данных (CentOS/RHEL)
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Создание пользователя и базы данных
sudo -u postgres psql << EOF
CREATE USER cleaning_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE project_cleaning OWNER cleaning_user;
GRANT ALL PRIVILEGES ON DATABASE project_cleaning TO cleaning_user;
\q
EOF
```

## 🗄️ Настройка базы данных

### Конфигурация PostgreSQL
Отредактируйте `/etc/postgresql/*/main/postgresql.conf`:
```ini
# Настройки производительности
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Настройка доступа
Отредактируйте `/etc/postgresql/*/main/pg_hba.conf`:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
```

### Перезапуск PostgreSQL
```bash
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

## ⚙️ Конфигурация приложения

### Клонирование репозитория
```bash
# Создание директории проекта
sudo mkdir -p /opt/cleaning_bot
sudo chown $USER:$USER /opt/cleaning_bot
cd /opt/cleaning_bot

# Клонирование проекта
git clone <repository_url> .
```

### Создание виртуального окружения
```bash
# Создание виртуального окружения
python3.11 -m venv venv

# Активация
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка переменных окружения
Создайте файл `.env`:
```bash
cp .env.example .env
nano .env
```

Заполните конфигурацию:
```env
# Telegram Bot Token
BOT_TOKEN=your_telegram_bot_token_here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://cleaning_user:your_secure_password@localhost:5432/project_cleaning

# Admin Configuration
ADMIN_TELEGRAM_ID=your_admin_telegram_id
ADMIN_USERNAME=your_admin_username

# Payment Configuration (optional)
PAYMENT_PROVIDER_TOKEN=your_payment_provider_token

# File Storage
PHOTOS_PATH=/opt/cleaning_bot/photos
PDF_PATH=/opt/cleaning_bot/pdfs

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/cleaning_bot/logs/bot.log

# Production settings
DEBUG=False
ENVIRONMENT=production
```

### Создание необходимых директорий
```bash
mkdir -p /opt/cleaning_bot/{photos,pdfs,logs}
chmod 755 /opt/cleaning_bot/{photos,pdfs,logs}
```

## 🚀 Развертывание

### Инициализация базы данных
```bash
# Активация виртуального окружения
source /opt/cleaning_bot/venv/bin/activate

# Инициализация базы данных
python scripts/init_database.py
```

### Создание systemd сервиса
Создайте файл `/etc/systemd/system/cleaning_bot.service`:
```ini
[Unit]
Description=Cleaning Bot Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/cleaning_bot
Environment=PATH=/opt/cleaning_bot/venv/bin
ExecStart=/opt/cleaning_bot/venv/bin/python bot/main.py
Restart=always
RestartSec=10

# Environment variables
EnvironmentFile=/opt/cleaning_bot/.env

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/cleaning_bot/{photos,pdfs,logs}

[Install]
WantedBy=multi-user.target
```

### Создание пользователя для сервиса
```bash
sudo useradd -r -s /bin/false botuser
sudo chown -R botuser:botuser /opt/cleaning_bot
```

### Запуск сервиса
```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Запуск сервиса
sudo systemctl start cleaning_bot
sudo systemctl enable cleaning_bot

# Проверка статуса
sudo systemctl status cleaning_bot
```

### Настройка Nginx (опционально)
Для веб-интерфейса или API создайте конфигурацию `/etc/nginx/sites-available/cleaning_bot`:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/cleaning_bot/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Активируйте сайт:
```bash
sudo ln -s /etc/nginx/sites-available/cleaning_bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🤖 Настройка Telegram бота

### Создание бота
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Имя бота: `Cleaning Service Bot`
   - Username: `cleaning_service_bot`
4. Сохраните полученный токен

### Настройка прав администратора
1. Добавьте бота в супергруппу
2. Сделайте бота администратором
3. Создайте темы для каждого города
4. Получите ID тем и добавьте в базу данных

### Тестирование бота
```bash
# Проверка работы бота
source /opt/cleaning_bot/venv/bin/activate
python -c "
from bot.main import bot
import asyncio
async def test():
    me = await bot.get_me()
    print(f'Bot: {me.full_name} (@{me.username})')
asyncio.run(test())
"
```

## 📊 Мониторинг и логирование

### Настройка логирования
Создайте конфигурацию логирования `/opt/cleaning_bot/logging.conf`:
```ini
[loggers]
keys=root,bot

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_bot]
level=INFO
handlers=consoleHandler,fileHandler
qualname=bot
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('/opt/cleaning_bot/logs/bot.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Мониторинг с помощью systemd
```bash
# Просмотр логов в реальном времени
sudo journalctl -u cleaning_bot -f

# Просмотр последних ошибок
sudo journalctl -u cleaning_bot -p err -n 50

# Статистика сервиса
sudo systemctl status cleaning_bot
```

### Настройка logrotate
Создайте `/etc/logrotate.d/cleaning_bot`:
```
/opt/cleaning_bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 botuser botuser
    postrotate
        systemctl reload cleaning_bot
    endscript
}
```

## 🔄 Обновление системы

### Процесс обновления
```bash
#!/bin/bash
# update_bot.sh

# Остановка сервиса
sudo systemctl stop cleaning_bot

# Резервное копирование
sudo cp -r /opt/cleaning_bot /opt/cleaning_bot_backup_$(date +%Y%m%d)

# Обновление кода
cd /opt/cleaning_bot
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Миграция базы данных (если нужно)
python scripts/migrate_database.py

# Перезапуск сервиса
sudo systemctl start cleaning_bot

# Проверка статуса
sudo systemctl status cleaning_bot
```

### Версионирование
Используйте теги для версионирования:
```bash
git tag -a v1.0.0 -m "First stable release"
git push origin v1.0.0
```

## 💾 Резервное копирование

### Автоматическое резервирование
Создайте `/opt/cleaning_bot/backup.sh`:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/cleaning_bot"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Резервное копирование базы данных
pg_dump -h localhost -U cleaning_user project_cleaning > $BACKUP_DIR/db_backup_$DATE.sql

# Резервное копирование файлов
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /opt/cleaning_bot/{photos,pdfs}

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Настройка cron для автоматического бэкапа
```bash
# Добавление в crontab
sudo crontab -e

# Добавить строки:
# 0 2 * * * /opt/cleaning_bot/backup.sh
```

## 🔧 Оптимизация производительности

### Настройка PostgreSQL
```sql
-- Оптимизация запросов
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
CREATE INDEX CONCURRENTLY idx_orders_city ON orders(city_id);
CREATE INDEX CONCURRENTLY idx_orders_manager ON orders(manager_id);
CREATE INDEX CONCURRENTLY idx_orders_cleaner ON orders(cleaner_id);
```

### Настройка Python
```bash
# Увеличение лимита файлов
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

## 🚨 Устранение проблем

### Частые проблемы

#### Бот не запускается
```bash
# Проверка логов
sudo journalctl -u cleaning_bot -n 100

# Проверка конфигурации
sudo -u botuser cat /opt/cleaning_bot/.env

# Проверка Python окружения
sudo -u botuser /opt/cleaning_bot/venv/bin/python --version
```

#### Проблемы с базой данных
```bash
# Проверка подключения
psql -h localhost -U cleaning_user -d project_cleaning -c "SELECT 1;"

# Проверка статуса PostgreSQL
sudo systemctl status postgresql
```

#### Проблемы с правами доступа
```bash
# Исправление прав
sudo chown -R botuser:botuser /opt/cleaning_bot
sudo chmod -R 755 /opt/cleaning_bot
```

## 📞 Поддержка

### Контактная информация
- **Техническая поддержка**: support@yourcompany.com
- **Документация**: https://docs.yourcompany.com
- **GitHub Issues**: https://github.com/yourrepo/issues

### Мониторинг
- **Системные метрики**: CPU, RAM, Disk
- **Бизнес метрики**: заказы, пользователи, платежи
- **Технические метрики**: время отклика, ошибки

---

**Важно:** Всегда тестируйте обновления на тестовом окружении перед развертыванием в production!
