# CloudStorage

Облачное файловое хранилище. Бэкенд — Django + Django REST Framework + PostgreSQL.
Фронтенд — React (Vite) + MobX.

## Возможности

- Регистрация и аутентификация по JWT.
- Иерархическая файловая система с папками, переименованием, перемещением,
  каскадным удалением и контролем размера хранилища.
- Загрузка/скачивание файлов.
- Публичные обезличенные ссылки на файлы (`/api/public/download/<token>`),
  скачивание без авторизации с сохранением оригинального имени.
- Админ-панель: список пользователей, переключение признака «администратор»,
  удаление пользователей, просмотр их хранилища.
- Серверная валидация данных регистрации.
- Логирование всех ключевых событий (auth, файловые операции, ошибки) в
  `backend/logs/app.log`.

## Структура

```
backend/                Django-проект
  config/               настройки, urls, wsgi/asgi
  cloudstorage/         основное приложение (модели, views, auth, миграции)
  requirements.txt
  .env.example
frontend/               React + Vite SPA
```

## Быстрый старт через Docker

Самый простой способ поднять всё локально:

```bash
docker compose up --build
```

Поднимутся три сервиса:
- `db` — PostgreSQL 16 на `localhost:5432` (данные в volume `pg_data`).
- `backend` — Django на `http://localhost:8000` (миграции прогоняются автоматически).
- `frontend` — Vite dev-сервер на `http://localhost:5173` с проксированием `/api` в backend.

Открой `http://localhost:5173` — приложение готово к работе.

Создание администратора:

```bash
docker compose exec backend python manage.py shell -c "from cloudstorage.models import User; \
  from cloudstorage.auth import hash_password; \
  User.objects.create(username='admin', email='admin@example.com', \
  password=hash_password('Admin#123'), is_admin=True)"
```

Остановить контейнеры (данные сохранятся):

```bash
docker compose down
```

Удалить вместе с данными:

```bash
docker compose down -v
```

Переопределить дефолты можно через `.env` в корне репозитория или переменные окружения на запуск:

```bash
DJANGO_SECRET_KEY=mysecret JWT_SECRET_KEY=myjwt docker compose up
```

## Локальная разработка без Docker

### Бэкенд

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # отредактировать под локальный PostgreSQL
python manage.py makemigrations cloudstorage
python manage.py migrate
python manage.py runserver
```

Сервер поднимется на `http://127.0.0.1:8000`.

#### Создание администратора

В Django нет стандартной команды `createsuperuser` для нашей кастомной
модели User. Простейший способ — выставить флаг через Django shell:

```bash
python manage.py shell -c "from cloudstorage.models import User; \
  from cloudstorage.auth import hash_password; \
  User.objects.create(username='admin', email='admin@example.com', \
  password=hash_password('Admin#123'), is_admin=True)"
```

Либо после регистрации обычного пользователя:

```bash
python manage.py shell -c "from cloudstorage.models import User; \
  u = User.objects.get(username='myuser'); u.is_admin = True; u.save()"
```

### Фронтенд

```bash
cd frontend
npm install
npm run dev
```

Приложение будет доступно на `http://localhost:5173`. Запросы на `/api/...`
проксируются на бэкенд (см. `vite.config.js`).

## Переменные окружения

См. `backend/.env.example`. Ключевые:

| Переменная | Назначение |
|---|---|
| `DJANGO_SECRET_KEY` | Секрет Django |
| `DJANGO_DEBUG` | `True`/`False` |
| `DJANGO_ALLOWED_HOSTS` | Через запятую |
| `DB_*` | Параметры PostgreSQL |
| `JWT_SECRET_KEY` / `JWT_ALGORITHM` | Подпись JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена |
| `STORAGE_PATH` | Путь хранения файлов |
| `CORS_ALLOWED_ORIGINS` | Разрешённые источники для CORS |
| `PUBLIC_BASE_URL` | База URL для публичных ссылок |

## Деплой на reg.ru (Ubuntu VPS)

Ниже — типовой сценарий развёртывания на VPS reg.ru.

### 1. Подготовка сервера

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib \
                    nginx git nodejs npm
```

### 2. PostgreSQL

```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE cloudstorage;
CREATE USER cloudstorage WITH PASSWORD 'strong-password';
ALTER ROLE cloudstorage SET client_encoding TO 'utf8';
ALTER ROLE cloudstorage SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE cloudstorage TO cloudstorage;
SQL
```

### 3. Код и зависимости

```bash
sudo mkdir -p /var/www/cloudstorage && sudo chown $USER /var/www/cloudstorage
cd /var/www/cloudstorage
git clone <repository-url> .

# Бэкенд
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env    # выставить продовские значения, DJANGO_DEBUG=False, реальный домен в ALLOWED_HOSTS

python manage.py migrate
python manage.py collectstatic --noinput

# Фронтенд
cd ../frontend
npm install
npm run build         # билд попадёт в frontend/dist
```

### 4. systemd-юнит для gunicorn

`/etc/systemd/system/cloudstorage.service`:

```ini
[Unit]
Description=CloudStorage Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cloudstorage/backend
EnvironmentFile=/var/www/cloudstorage/backend/.env
ExecStart=/var/www/cloudstorage/backend/.venv/bin/gunicorn \
          --workers 3 --bind 127.0.0.1:8001 config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cloudstorage
```

### 5. Nginx

`/etc/nginx/sites-available/cloudstorage`:

```nginx
server {
    listen 80;
    server_name your-domain.ru;
    client_max_body_size 1024M;

    # Фронтенд
    root /var/www/cloudstorage/frontend/dist;
    index index.html;

    # API и публичные ссылки -> Django
    location ~ ^/(api|static)/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA fallback
    location / {
        try_files $uri /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/cloudstorage /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 6. HTTPS (опционально)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.ru
```

### 7. Логи

- Приложение: `/var/www/cloudstorage/backend/logs/app.log`
- Gunicorn:  `journalctl -u cloudstorage -f`
- Nginx:    `/var/log/nginx/{access,error}.log`
