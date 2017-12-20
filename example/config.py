import os

# tornado config
static_path = os.path.join(os.getcwd(), 'templates')
cookie_secret = 'g7892gryo8g348tgo34gtgreglwjeg48t2o3gweiouti2uo3gog'
locale = 'ru_RU.UTF-8'  # locale for everything

# SQL config
pg_user = 'm2core'
pg_db = 'm2core'
pg_password = 'Password1'
pg_host = '192.168.99.100'
pg_port = 5432

# Redis config
redis_host = '192.168.99.100'
redis_port = 6379
redis_db = 0


# some other settings
debug = True
server_port = 9999
