from tornado.options import define


# project options:
# - tornado config
define('debug', default=False, help='Tornado debug mode', type=bool)
define('debug_orm', default=False, help='SQLAlchemy debug mode', type=bool)
define('config_name', default='config.py', help='Config name', type=str)
define('admin_role_name', default='admins', help='Admin group name', type=str)
define('default_role_name', default='users', help='Default user group with login permissions', type=str)
define('default_permission', default='authorized', help='Default permission', type=str)
define('xsrf_cookie', default=False, help='Enable or disable XSRF-cookie protection', type=str)
define('cookie_secret', default='gfqeg4t023ty724ythweirhgiuwehrtp', type=str)
define('server_port', default=8888, help='TCP server bind port', type=int)
define('server_listen_ip', default='0.0.0.0', help='TCP server bind ip', type=str)
define('locale', default='ru_RU.UTF-8', help='Server locale for dates, times, currency and etc', type=str)
define('log_file', default='/logs.txt', help='Path to log file', type=str)
define('json_indent', default=2,
       help='Number of `space` characters, which are used in json responses after new lines', type=int)
define('thread_pool_size', default=10, help='Pool size for background executor', type=int)
define('gen_salt', default=12, help='Argument for gen_salt func in bcrypt module', type=int)

# - database config
define('pg_host', default='127.0.0.1', help='Database host', type=str)
define('pg_port', default=5432, help='Database port', type=int)
define('pg_db', default='m2core', help='Database name', type=str)
define('pg_user', default='postgres', help='Database user', type=str)
define('pg_password', default='password', help='Database password', type=str)
define('pg_pool_size', default=40, help='Pool size for bg executor', type=int)
define('pg_pool_recycle', default=-1, help='Pool recycle time in sec, -1 - disable', type=int)
define('expire_on_connect', default=True, help='Expire sqlalchemy inner cache when initializing BaseHandler '
                                               'for incoming client', type=True)
# - redis config
define('redis_host', default='127.0.0.1', help='Redis host', type=str)
define('redis_port', default=6379, help='Redis port', type=int)
define('redis_db', default=0, help='Redis database number (0-15)', type=int)

# - additional kwargs for different kind of classes
define('redis_connection_pool_kwargs', default={}, help='Additional kwargs used when initializing Connection Pool '
                                                        'for Redis', type=dict)
define('engine_kwargs', default={}, help='Additional kwargs used when initializing SQLAlchemy engine',
       type=dict)
define('session_kwargs', default={}, help='Additional kwargs used when initializing SQLAlchemy session',
       type=dict)
define('tornado_application_kwargs', default={}, help='Additional kwargs used when initializing Tornado app',
       type=dict)
define('http_server_kwargs', default={'xheaders': True}, help='Additional kwargs used when initializing HTTP server',
       type=dict)
