# EcoReceipt API

---

This project was created to minimize the number of paper receipts issued by stores for purchases.
API side it is only part of project, also will be created client web service, mobile application and working model of paying terminal, for full working cycle.

## API setup

- Clone project
- Add .env file near to django applications and fill it with variables:

```bash
DEBUG=true
SECRET_KEY=secret_key
DB_HOST=database_host
DB_PORT=database_port
DB_NAME=database_name
DB_USER=database_user
DB_PASSWORD=database_user_password

SERVER_API_DOMAIN=domain_or_ip
BOT_TOKEN=telegram_bot_token
```

- Create virtual environment
- Install all dependencies from **_requirements.txt_**
- Apply project migrations

```bash
$ python manage.py migrate
```

- Start dev server

```bash
$ python manage.py runserver 0.0.0.0:8000
```

## Run tests
```bash
$ python manage.py test
```

## Ruff linter and formatter start checking
```bash
$ ruff check
$ ruff format
```

## Service setup on production

