# EcoReceipt API

---

This project was created to minimize the number of paper receipts issued by stores for purchases.
API side it is only part of project, also will be created client web service, mobile application and working model of paying terminal, for full working cycle.

## Development setup

* Clone project
* Add .env file near to django applications and fill it with variables:

```text
DEBUG=true
SECRET_KEY=secret_key
DB_HOST=database_host
DB_PORT=database_port
DB_NAME=database_name
DB_USER=database_user
DB_PASSWORD=database_user_password

SERVER_API_DOMAIN=domain_or_ip
REDIS_HOST=ip_or_domain
REDIS_PORT=port
BOT_TOKEN=telegram_bot_token
```

* Create virtual environment
* Install all dependencies from **_requirements.txt_**
* Apply project migrations

```bash
$ python manage.py migrate
```

* Start dev server

```bash
$ python manage.py runserver 0.0.0.0:8000
```

* Start telegram bot:
```bash
python telegram_bot/bot.py
```

## Run tests
```bash
$ python manage.py test
```

## Ruff linter and formatter start checking
```bash
$ ruff check  # Lint all files in the current directory.
$ ruff check --fix  # Lint all files in the current directory, and fix any fixable errors.
$ ruff format  # Format all files in the current directory.
```

## Production setup
***
* Set static IP(on raspberry os using nmcli): 
```bash 
$ nmcli con show
$ nmcli con mod [connection name] ipv4.addresses 192.168.0.100/24
$ nmcli con mod [connection name] ipv4.gateway 192.168.0.1
$ nmcli con mod [connection name] ipv4.dns 8.8.8.8
$ nmcli con mod [connection name] ipv4.method manual
$ nmcli con up [connection name]
```

* Clone project
```bash
$ cd /home/raspberry/Documents
$ git clone https://github.com/Nikita-Goncharov/EcoReceipt-API.git
```
* Add .env file near to django applications and fill it with variables(as in development setup)
* Create virtual environment
* Install all dependencies from **_requirements.txt_**
* If error with postgres lib, then install system packs and try to install it again:
```bash
$ sudo apt install libpq-dev python3-dev -y
```
* Install postgresql
```bash
$ sudo apt install postgresql -y
```
* Create DB and user + grand to user privileges, do user as owner of DB, extend user for db creation
```bash
$ sudo -u postgres psql
-> create database ecoreceipt;
-> create user myuser with encrypted password 'mypass';
-> grant all privileges on database ecoreceipt to myuser;
-> ALTER DATABASE ecoreceipt OWNER TO myuser;
-> ALTER USER myuser CREATEDB;
```
* Init venv and change dir to project dir
* Apply migrations
```bash
$ python manage.py migrate
```
* Check working of service
```bash
$ python manage.py runserver 0.0.0.0:8000
```
* Run tests
```bash
$ python manage.py test
```
* Create superuser
```bash
$ python manage.py createsuperuser
```
* Open settings.py from project and change:
```text
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "192.168.0.222"]  # your IP or domain
DEBUG = False
```
* Collect static files
```bash
$ python manage.py collectstatic
```

#### Nginx and gunicorn setup
* Check site running with gunicorn:
```bash
$ gunicorn --bind 0.0.0.0:8000 ecoreceipt_api.wsgi
```
* Add gunicorn socket:
```bash
$ sudo nano /etc/systemd/system/gunicorn.socket
```
Put:
```text
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

* Add gunicorn service:
```bash
$ sudo nano /etc/systemd/system/gunicorn.service
```
Put:
```text
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=raspberry
Group=www-data
WorkingDirectory=/home/raspberry/Documents/EcoReceipt-API
ExecStart=/home/raspberry/Documents/environments/env-ecoreceipt/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          ecoreceipt_api.wsgi:application

[Install]
WantedBy=multi-user.target
```
* Start socket:
```bash
$ sudo systemctl start gunicorn.socket
$ sudo systemctl enable gunicorn.socket
```

* Test socket activation:
```bash
$ sudo systemctl status gunicorn  # not active
$ curl --unix-socket /run/gunicorn.sock localhost
$ sudo systemctl status gunicorn  # active
```

* Restart gunicorn:
```bash
$ sudo systemctl daemon-reload
$ sudo systemctl restart gunicorn
```

* Install nginx and create nginx conf for site:
```bash
$ sudo apt install nginx -y
$ sudo nano /etc/nginx/sites-available/ecoreceipt 
```
Put:
```text
server {
    listen 80;
    server_name 127.0.0.1;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/raspberry/Documents/EcoReceipt-API;  # path to main static folder in project
    }

    location /media/ {
        root /home/raspberry/Documents/EcoReceipt-API;  # path to media folder in project
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

* Add conf in enabled folder, remove default conf and restart service
```bash
$ sudo ln -s /etc/nginx/sites-available/ecoreceipt /etc/nginx/sites-enabled
$ sudo rm /etc/nginx/sites-enabled/default
$ sudo systemctl restart nginx.service 
```

* Change user at first line in nginx.conf from www-data to your OS user:

    Example from ***user www-data;*** to ***user raspberry;***
```bash
$ sudo nano /etc/nginx/nginx.conf 
```
* Again restart nginx service:
```bash
$ sudo systemctl restart nginx.service
```
* Add CURRENT_SITE_DOMAIN to django model ServiceSetting using admin panel
```text
Name: CURRENT_SITE_DOMAIN
Value: http://192.168.0.222
Desc: domain or ip of current site
```

* Install redis for telegram bot
```bash
$ sudo apt install redis -y
```
* Create system service for telegram bot:
```bash
$ sudo nano /etc/systemd/system/ecoreceipt_bot.service 
```
Put:
```text
[Unit]
Description=Ecoreceipt telegram bot
After=syslog.target
After=network.target


[Service]
Type=simple
User=root
WorkingDirectory=/home/raspberry/Documents/EcoReceipt-API/telegram_bot
ExecStart=/home/raspberry/Documents/environments/env-ecoreceipt/bin/python3 /home/raspberry/Documents/EcoReceipt-API/telegram_bot/bot.py

RestartSec=10
Restart=always

[Install]
WantedBy=multi-user.target
```
* Start and enable service
```bash
$ sudo systemctl start ecoreceipt_bot.service
$ sudo systemctl enable ecoreceipt_bot.service 
```