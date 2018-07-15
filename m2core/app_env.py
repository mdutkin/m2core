from m2core.common.options import options


# project options:
# - tornado config
options.define('debug', default=False, help='Tornado debug mode', type=bool)
options.define('debug_orm', default=False, help='SQLAlchemy debug mode', type=bool)
options.define('allow_test_users', default=False, help='Allows decorator `user_can` work with test users\' data', type=bool)
options.define('parse_cli_options', default=True, help='Enables/disables options setup via cli', type=bool)
options.define('config_name', default='config.py', help='Config name', type=str)
options.define('admin_role_name', default='admins', help='Admin group name', type=str)
options.define('default_role_name', default='users', help='Default user group with login permissions', type=str)
options.define('default_permission', default='authorized', help='Default permission', type=str)
options.define('xsrf_cookie', default=False, help='Enable or disable XSRF-cookie protection', type=str)
options.define('cookie_secret', default='gfqeg4t023ty724ythweirhgiuwehrtp', type=str)
options.define('server_port', default=8888, help='TCP server bind port', type=int)
options.define('server_listen_ip', default='0.0.0.0', help='TCP server bind ip', type=str)
options.define('locale', default='ru_RU.UTF-8', help='Server locale for dates, times, currency and etc', type=str)
options.define('log_file', default='/logs.txt', help='Path to log file', type=str)
options.define('json_indent', default=2,
       help='Number of `space` characters, which are used in json responses after new lines', type=int)
options.define('thread_pool_size', default=10, help='Pool size for background executor', type=int)
options.define('gen_salt', default=12, help='Argument for gen_salt func in bcrypt module', type=int)

# - database config
options.define('pg_host', default='127.0.0.1', help='Database host', type=str)
options.define('pg_port', default=5432, help='Database port', type=int)
options.define('pg_db', default='m2core', help='Database name', type=str)
options.define('pg_user', default='postgres', help='Database user', type=str)
options.define('pg_password', default='password', help='Database password', type=str)
options.define('pg_pool_size', default=40, help='Pool size for bg executor', type=int)
options.define('pg_pool_recycle', default=-1, help='Pool recycle time in sec, -1 - disable', type=int)
options.define('expire_on_connect', default=True, help='Expire sqlalchemy inner cache when initializing BaseHandler '
                                               'for incoming client', type=bool)
# - redis config
options.define('redis_host', default='127.0.0.1', help='Redis host', type=str)
options.define('redis_port', default=6379, help='Redis port', type=int)
options.define('redis_db', default=0, help='Redis database number (0-15)', type=int)

# - additional kwargs for different kind of classes
options.define('redis_connection_pool_kwargs', default={}, help='Additional kwargs used when initializing Connection Pool '
                                                        'for Redis', type=dict)
options.define('engine_kwargs', default={}, help='Additional kwargs used when initializing SQLAlchemy engine',
       type=dict)
options.define('session_kwargs', default={}, help='Additional kwargs used when initializing SQLAlchemy session',
       type=dict)
options.define('tornado_application_kwargs', default={}, help='Additional kwargs used when initializing Tornado app',
       type=dict)
options.define('http_server_kwargs', default={'xheaders': True}, help='Additional kwargs used when initializing HTTP server',
       type=dict)
options.define('access_token_update_on_check', default=False, help='When checking access token in Redis, resets it\'s TTL to '
                                                           'default value', type=bool)
