__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import functools
import locale
import logging
import redis
import tornado.ioloop
import tornado.web
import warnings
# needed for env initialization
from m2core.app_env import *
from m2core.bases.base_model import MetaBase, EnchantedMixin
from m2core.common.permissions import Permission, PermissionsEnum
from m2core.common.rules import Rules
from m2core.data_schemes.redis_system_scheme import redis_scheme
from m2core.data_schemes.db_system_scheme import M2Role
from m2core.data_schemes.db_system_scheme import M2RolePermission
from m2core.data_schemes.db_system_scheme import M2Permission
from random import randint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from m2core.common.options import options
from tornado.web import HTTPError, RequestHandler
from tornado.websocket import WebSocketHandler
from tornado.web import StaticFileHandler
from concurrent.futures import ThreadPoolExecutor
from typing import Type
from voluptuous.error import Error as VoluptuousError
from m2core.bases.base_handler import http_statuses
from m2core.utils.url_parser import UrlParser
from m2core.utils.session_helper import SessionHelper
from m2core.utils.permissions import HandlerPermissions
from m2core.utils.error import M2Error


logger = logging.getLogger(__name__)


class M2Core:
    handler_permissions = HandlerPermissions()
    rules = Rules(lambda: {'validator': None, 'docs': {}, 'permissions': {}, 'group': None})

    @staticmethod
    def requires_permission(handler_method_func):
        """
        Decorator which launches permission system for specified method of specified route.
        It means you can have the same handler `ExampleHandler` with `GET` method, use it with different routes
        and set different permissions on each `GET` on each route. Cool, isn't it?
        """
        warnings.warn('The `requires_permission` decorator is deprecated, use `user_can` decorator instead though it '
                      'works with new permissions realisation',
                      DeprecationWarning)
        # TODO: maybe add check function support in arguments ? and pass user and handler data here
        # get handler name and method name
        func_info = handler_method_func.__qualname__.split('.')
        method = func_info[1]

        @functools.wraps(handler_method_func)
        def decorated(handler_instance, *args, **kwargs):
            module_name = handler_instance.human_route
            method_permissions = M2Core.handler_permissions.get_handler_method_permissions(module_name, method)
            # restricted method
            if method_permissions is None:
                raise HTTPError(http_statuses['METHOD_NOT_ALLOWED']['code'],
                                http_statuses['METHOD_NOT_ALLOWED']['msg'])
            # method with no restrictions (permissions) where len == 0 just passes by
            if len(method_permissions):
                # didn't get user from Redis
                if not handler_instance.current_user:
                    raise HTTPError(http_statuses['WRONG_CREDENTIALS']['code'],
                                    http_statuses['WRONG_CREDENTIALS']['msg'])
                user_permissions = handler_instance.current_user['permissions']
                # user's rights are not enough to get into method
                if len(set(method_permissions) - set(user_permissions)):
                    raise HTTPError(http_statuses['WRONG_CREDENTIALS']['code'],
                                    http_statuses['WRONG_CREDENTIALS']['msg'])
            return handler_method_func(handler_instance, *args, **kwargs)

        return decorated

    @staticmethod
    def user_can(handler_method):
        # get handler name and method name
        method_info = handler_method.__qualname__.split('.')
        method = method_info[1]

        @functools.wraps(handler_method)
        def decorated(handler_instance, *args, **kwargs):
            permissions = M2Core.rules.permissions(handler_instance.human_route, method.upper())
            # restricted method
            if permissions is None:
                raise HTTPError(http_statuses['METHOD_NOT_ALLOWED']['code'],
                                http_statuses['METHOD_NOT_ALLOWED']['msg'])

            if issubclass(type(permissions), Permission) or callable(permissions):
                # didn't get user from Redis
                if not handler_instance.current_user:
                    # maybe it's permissions == PermissionsEnum.SKIP?
                    if permissions({}):
                        return handler_method(handler_instance, *args, **kwargs)
                    else:
                        raise HTTPError(http_statuses['WRONG_CREDENTIALS']['code'],
                                        http_statuses['WRONG_CREDENTIALS']['msg'])

                user_generic_perms = handler_instance.current_user['permissions']

                check_result = permissions(user_generic_perms)
                if check_result:
                    return handler_method(handler_instance, *args, **kwargs)
                else:
                    # user's rights are not enough to get into method
                    raise HTTPError(http_statuses['WRONG_CREDENTIALS']['code'],
                                    http_statuses['WRONG_CREDENTIALS']['msg'])
            else:
                raise HTTPError(http_statuses['SRV_INTERNAL_ERR'],
                                'Handler permissions must be instance of `Permissions` or `callable`')

        return decorated

    @staticmethod
    def tryex(*errors):
        """
        Decorator which reacts on exceptions, raised in handler method.
        As arguments it accepts tuple of 2 elements, first is exception type and second is dict() with
        HTTP response code and message. Check out a few examples:

        exceptions_list = [
            (JSONDecodeError, http_statuses['WRONG_REQUEST']),
            (exc.SQLAlchemyError, http_statuses['WRONG_PARAM']),
            (TypeError, {'code': 500, 'msg': 'Some error occurred on server side'})
        ]


        class UsersHandler(BaseHandler):
            @gen.coroutine
            @M2Core.tryex(*exceptions_list)
            @M2Core.requires_permission
            def get(self, *args, **kwargs):
                # validate url params and do nothing
                self.validate_url_params(kwargs)
                self.write_json(data='ok')
        """

        def decorator(func):
            @functools.wraps(func)
            def new_func(handler, *args, **kwargs):
                try:
                    return func(handler, *args, **kwargs)
                except tuple([error[0] for error in errors]) as e:
                    # get exception HTTP status for exception
                    http_status = None
                    for exception in errors:
                        if isinstance(e, exception[0]):
                            http_status = exception[1]
                            break
                    logger.error("%s in %s: %s" % (func.__qualname__, handler.__module__, repr(e)))
                    error_msg = http_status['msg'] + (' (%s)' % e.error_message if hasattr(e, 'error_message') else '')
                    raise HTTPError(
                        http_status['code'],
                        error_msg
                    )
                except M2Error as e:
                    # default for M2Error
                    logger.error("%s in %s: %s" % (func.__qualname__, handler.__module__, repr(e)))
                    if e.show_to_user:
                        raise HTTPError(
                            http_statuses['ANY_ERR']['code'],
                            http_statuses['ANY_ERR']['msg'] + ' ' + e.error_message
                        )
                    else:
                        raise HTTPError(
                            http_statuses['ANY_ERR']['code'],
                            http_statuses['ANY_ERR']['msg']
                        )
                except HTTPError as e:
                    # re-raise for any HTTPError exception
                    raise e
                # voluptuous (validation) exceptions
                except VoluptuousError as e:
                    logger.error("%s in %s: %s" % (func.__qualname__, handler.__module__, repr(e)))
                    raise HTTPError(
                        http_statuses['WRONG_REQUEST']['code'],
                        http_statuses['WRONG_REQUEST']['msg']
                    )
                except Exception as e:
                    # re-raise for any other exception
                    logger.error("%s in %s: %s" % (func.__qualname__, handler.__module__, repr(e)))
                    raise HTTPError(
                        http_statuses['SRV_INTERNAL_ERR']['code'],
                        http_statuses['SRV_INTERNAL_ERR']['msg']
                    )

            return new_func

        return decorator

    def __recreate_db(self):
        """
        Recreates all DB scheme via SQLAlchemy functionality
        """
        MetaBase.metadata.drop_all(self.__db_engine)
        MetaBase.metadata.create_all(self.__db_engine)

    def __init__(self):
        """
        Constructor
        """
        # search for config variables in environment
        options.parse_environment()
        logger.debug('path to config: %s' % options.config_name)
        options.parse_config_file(options.config_name)
        if options.parse_cli_options:
            # override options from config with command line options
            options.parse_command_line()

        self.__db_engine = None  # engine for db_session
        self.__db_session = None  # singleton of SQLAlchemy connections pool
        self.__redis_session = None  # singleton of Redis connections pool
        self.__redis_scheme = redis_scheme  # Redis key mapping
        self.__thread_pool = None  # thread pool for doing some jobs in background
        self.__custom_response_headers = dict()  # custom headers, which will be mixed in every response
        self.__endpoints = list()  # list of Tornado routes with handler classes, permissions
        self.__handler_docs = dict()  # all docstrings of all methods of all routes
        self.__handler_validators = dict()  # all validators (UrlParser instance) of all methods of all routes
        self.__started = False
        self.__app = None
        self.__test_users = dict()  # used for impersonation users during integration tests

        # make singleton of thread pool
        self.__make_thread_pool()

        # init singleton of DB connections pool
        self.__make_db_session()

        # init singleton of Redis connections pool
        self.__make_redis_session()

    def __make_app(self):
        """
        Init Tornado
        """
        return tornado.web.Application(
            [endpoint for endpoint in self.__endpoints],
            redis={
                'connector': self.__redis_session,
                'scheme': self.__redis_scheme
            },
            db=self.__db_session,
            endpoints=self.__endpoints,
            handler_docs=self.__handler_docs,
            handler_validators=self.__handler_validators,
            custom_response_headers=self.__custom_response_headers,
            permissions=M2Core.handler_permissions,
            thread_pool=self.__thread_pool,
            debug=options.debug,
            **options.tornado_application_kwargs
        )

    def route(self, human_route: str=None, handler_cls: Type[RequestHandler]=None, rule_group: str=None,
              extra: dict=None, **kwargs):
        if self.__started:
            raise RuntimeError('You can\'t add endpoints when app is already started')
        if human_route is None:
            raise M2Error('`human_route` parameter can\'t be an empty string')
        if handler_cls is None or not issubclass(handler_cls, RequestHandler):
            raise M2Error('`handler_cls` parameter must be inherited from `RequestHandler`')

        for k, v in kwargs.items():
            if k.lower() not in handler_cls.__dict__:
                raise AttributeError('Trying to add permissions on non-existent method `%s` or route `%s`' %
                                     (k.lower(), human_route))

            if k.upper() not in handler_cls.SUPPORTED_METHODS:
                raise M2Error('method name must be in `RequestHandler.SUPPORTED_METHODS`')

        url_parser = M2Core.rules.add_meta(human_route, handler_cls, rule_group, kwargs)
        tornado_route = url_parser.tornado_url()

        # hack for some Tornado builtin Handlers
        if issubclass(handler_cls, WebSocketHandler) and not M2Core.rules.docs(human_route, 'GET'):
            # specially for WebSocketHandler we have to add GET method, because it's required for WS protocol
            M2Core.rules[human_route]['GET'] = 'Builtin method for WebSocket proto'

        elif issubclass(handler_cls, StaticFileHandler) and not M2Core.rules.docs(human_route, 'GET'):
            # specially for StaticFileHandler we have to add GET method
            M2Core.rules[human_route]['GET'] = 'Builtin method for StaticFileHandler'

        tornado_handler_params = {
            'human_route': human_route,
            'url_parser': url_parser,
            'm2core': self
        }
        if extra:
            tornado_handler_params.update(extra)

        if issubclass(handler_cls, StaticFileHandler):
            # for StaticFileHandler we have to reduce kwargs because of its initialize method
            self.__endpoints.append(
                (
                    tornado_route,
                    handler_cls,
                    extra
                )
            )
        else:
            self.__endpoints.append(
                (
                    tornado_route,
                    handler_cls,
                    tornado_handler_params
                )
            )

    def add_endpoint(self, human_route: str, handler_class: Type[RequestHandler], extra_params: dict = dict()):
        """
        Adds to endpoint list() new endpoint. Also searches for docstrings and adds permissions per each method
        in SUPPORTED_METHODS
        :param human_route: url string, which passes to UrlParser, example: '/admin/roles/{id}'
        :param handler_class: reference to handler class, example: UsersHandler
        :param extra_params: pass here a dict of params you want to bypass to Tornado
        """
        if self.__started:
            raise RuntimeError('You can\'t add endpoints when app is already started')

        url_parser = UrlParser(human_route)
        tornado_route = url_parser.tornado_url()

        # add documentation per each method in SUPPORTED_METHODS
        for method in handler_class.__dict__:
            if method.upper() in handler_class.SUPPORTED_METHODS:
                if self.__handler_docs.get(human_route):
                    self.__handler_docs[human_route].update({
                        method: handler_class.__dict__[method].__doc__
                    })
                else:
                    self.__handler_docs[human_route] = {
                        method: handler_class.__dict__[method].__doc__
                    }
                # also add empty permissions per each method
                M2Core.handler_permissions.add_handler_method_rules(human_route, method, [])

        if WebSocketHandler in handler_class.__bases__ and \
                (not self.__handler_docs.get(human_route) or not self.__handler_docs[human_route].get('get')):
            # specially for WebSocketHandler we have to add GET method, because it's required for WS proto
            if not self.__handler_docs.get(human_route):
                self.__handler_docs[human_route] = {
                    'get': 'Builtin method for WebSocket proto'
                }
            else:
                self.__handler_docs[human_route].update({
                    'get': 'Builtin method for WebSocket proto'
                })

        if StaticFileHandler in handler_class.__bases__ and \
                (not self.__handler_docs.get(human_route) or not self.__handler_docs[human_route].get('get')):
            # specially for StaticFileHandler we have to add GET method
            if not self.__handler_docs.get(human_route):
                self.__handler_docs[human_route] = {
                    'get': 'Builtin method for StaticFileHandler'
                }
            else:
                self.__handler_docs[human_route].update({
                    'get': 'Builtin method for StaticFileHandler'
                })

        # mix `self` into static field of handler - sometimes this is useful when you need access to Redis
        # session in static method
        if not getattr(handler_class, 'm2core', None):
            handler_class.m2core = self

        tornado_handler_params = {
            'human_route': human_route,
            'url_parser': url_parser,
        }
        tornado_handler_params.update(extra_params)

        if StaticFileHandler in handler_class.__bases__ or StaticFileHandler == handler_class:
            # for StaticFileHandler we have to reduce kwargs because of its initialize method
            self.__endpoints.append(
                (
                    tornado_route,
                    handler_class,
                    extra_params
                )
            )
        else:
            self.__endpoints.append(
                (
                    tornado_route,
                    handler_class,
                    tornado_handler_params
                )
            )

        self.__handler_validators[human_route] = url_parser

    def add_endpoint_method_permissions(self, human_route: str, method: str, permissions: list or None):
        """
        Adds permissions for specified method of handler, accessed by `human_route`
        :param human_route: url string, which passes to UrlParser, example: '/admin/roles/{id}'
        :param method: method name in lower case, example: 'get'
        :param permissions: list of permissions, example: ['authorized', 'add_user'].
                            if you want to completely deny access to this method, simply pass `None` instead of list().
                            if you want to skip permissions check for this method for specified `human_route` - simply
                            pass empty list like [] or list()
        """
        if self.__started:
            raise RuntimeError('You can\'t add endpoint permissions when app is already started')

        # earlier in add_endpoint method we already added docs per each existing method in handler
        # so we can simply use __handler_docs dict to check method for existence and add special permissions
        if human_route not in self.__handler_docs.keys() or method not in self.__handler_docs[human_route].keys():
            raise AttributeError('Trying to add permissions on non-existent method [%s] or route [%s]' %
                                 (method, human_route))

        M2Core.handler_permissions.add_handler_method_rules(human_route, method, permissions)

    def add_endpoint_permissions(self, human_route: str, permissions: dict):
        """
        Adds permissions for list of methods of handler, accessed by `human_route`
        :param human_route: url string, which passes to UrlParser, example: '/admin/roles/{id}'
        :param permissions: dict() with pairs method -> permissions. example:
                            {
                                'get': ['authorized', 'admin', 'add_user'],
                                'post': None,
                                'put': ['authorized', 'admin', 'update_user'],
                                'delete': ['authorized', 'admin', 'remove_user'],
                            }
                            permission rules are the same as in `add_endpoint_method_permissions` method
        """
        if self.__started:
            raise RuntimeError('You can\'t add endpoint permissions when app is already started')

        # earlier in add_endpoint method we already added docs per each existing method in handler
        # so we can simply use __handler_docs dict to check method for existence and add special permissions
        for method in permissions.keys():
            if human_route not in self.__handler_docs.keys() or method not in self.__handler_docs[human_route].keys():
                raise AttributeError('Trying to add permissions on non-existent method [%s] or route [%s]' %
                                     (method, human_route))

        M2Core.handler_permissions.add_handler_rules(human_route, permissions)

    def add_redis_scheme(self, _redis_scheme: dict):
        """
        Adds to M2Core Redis keys mapping other keys. Use it if you want to add something special in that mapping
        :param _redis_scheme: example of dict:
            {
                'TABLE_KEY1': {'prefix': 'tk1:%s', 'ttl': 3600},
                'TABLE_KEY2': {'prefix': 'tk2:%s', 'ttl': 3600},
            }
        """
        self.__redis_scheme.update(_redis_scheme)

    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        """
        Getter of a thread pool
        """
        return self.__thread_pool

    @property
    def db_engine(self) -> Engine:
        """
        Getter of instance of SQLAlchemy engine
        """
        return self.__db_engine

    @property
    def db_session(self) -> scoped_session:
        """
        Getter of SQLAlchemy sessions pool
        """
        return self.__db_session

    @property
    def redis_session(self) -> redis.StrictRedis:
        """
        Getter of Redis sessions pool
        """
        return self.__redis_session

    @property
    def redis_tables(self) -> dict:
        """
        Getter of Redis tables
        """
        return self.__redis_scheme

    @property
    def app(self) -> tornado.web.Application:
        """
        Tornado app instance, it's `None` before initialized in `self.run` or `self.run_with_recreate` method
        """
        return self.__app

    def __make_db_session(self):
        """
        Creates SQLAlchemy connection pool
        """
        self.__db_engine = create_engine(
            'postgresql://%s:%s@%s:%s/%s' % (options.pg_user, options.pg_password, options.pg_host,
                                             options.pg_port, options.pg_db),
            poolclass=QueuePool,
            pool_size=options.pg_pool_size,
            pool_recycle=options.pg_pool_recycle,
            echo=options.debug_orm,
            **options.engine_kwargs
        )

        self.__db_session = scoped_session(
            sessionmaker(
                autoflush=False,
                autocommit=False,
                expire_on_commit=True,
                bind=self.__db_engine,
                **options.session_kwargs
            )
        )

        EnchantedMixin.set_db_session(self.__db_session)
        EnchantedMixin.set_sh(SessionHelper)

    def __make_thread_pool(self):
        """
        Creates thread pool for doing some background stuff via `yield thread_pool.submit()`
        """
        self.__thread_pool = ThreadPoolExecutor(options.thread_pool_size)

    def __make_redis_session(self):
        """
        Creates Redis connection pool
        """
        self.__redis_session = redis.StrictRedis(
            connection_pool=redis.ConnectionPool(
                host=options.redis_host,
                port=str(options.redis_port),
                db=options.redis_db,
                decode_responses=True,
                **options.redis_connection_pool_kwargs
            ),
        )
        EnchantedMixin.set_redis_session({
            'connector': self.__redis_session,
            'scheme': self.__redis_scheme
        })

    def add_callback(self, callback: callable, *args, **kwargs):
        """
        Adds callback to main event-loop, which would be called on M2COre start with passed params (args
        and kwargs). Additionally, an instance of inited M2Core will be passed as kwarg `m2core`.
        :param callback: reference to your callback
        """
        tornado.ioloop.IOLoop.current().add_callback(callback, m2core=self, *args, **kwargs)

    def extended(self, callback: callable):
        """
        Extends M2Core instance with a `callback`. When called - `self` would be mixed as first param and will contain
        inited instance of M2Core
        :param callback: reference to function
        :return: also returns mixed function you can use
        """

        def call_me_maybe(*args, **kwargs):
            return callback(self, *args, **kwargs)

        setattr(self, callback.__name__, call_me_maybe)
        return call_me_maybe

    def add_custom_response_headers(self, headers: dict()):
        """
        Adds custom HTTP response headers, which will be included in every response (it could be CORS-headers i.e.)
        :param headers: pair key => value, example: {'Access-Control-Allow-Origin': '*', }
        """
        self.__custom_response_headers = headers

    def run(self):
        """
        Launches Tornado web server
        """
        locale.setlocale(locale.LC_TIME, options.locale)
        self.__app = self.__make_app()
        self.__app.listen(
            options.server_port,
            address=options.server_listen_ip,
            **options.http_server_kwargs
        )
        # write all permissions and roles to DB
        tornado.ioloop.IOLoop.current().add_callback(sync_permissions)
        # dump all permissions and roles to Redis
        tornado.ioloop.IOLoop.current().add_callback(dump_roles)
        self.__started = True
        logger.info('Starting M2Core...')
        try:
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            pass

    def run_with_recreate(self):
        """
        Does exactly the same as `run` method, but firstly recreates DB structure
        """
        self.__recreate_db()
        self.run()

    def run_for_test(self) -> tornado.web.Application:
        """
        USE ONLY FOR TESTING
        This method creates Tornado app so you can grab it and use for creating instances
        of your own RequestHandlers!
        """
        locale.setlocale(locale.LC_TIME, options.locale)
        self.__app = self.__make_app()
        return self.__app

    def add_test_user(self, at: str, user_id: int=None, permissions: set=None):
        """
        USE ONLY FOR TESTING
        Adds user to global dict, where keys are access tokens, and values are user's info dict. Main
        purpose of it to allow users' impersonation during integration tests. For proper impersonation
        you also need to set `options.allow_test_users` to `True`

        :param at: access token, generate whatever value you want
        :param user_id: id of test user
        :param permissions: set of user permissions
        """
        self.__test_users[at] = {
            'id': user_id if user_id else randint(1, 10000),
            'access_token': at,
            'permissions': permissions
        }

    def get_test_user(self, at: str) -> dict:
        """
        Returns test user's data by access token

        :param at: access token
        :return: dict with user's info
        """
        return self.__test_users.get(at)


def sync_permissions():
    """
    Syncs permissions, received from all method of all handlers per each human route during initialization
    and stores them in DB, also with caching them in Redis
    """
    # load or create default admin role
    admin_role = M2Role.load_by_params(name=options.admin_role_name)
    # admin group, which holds all new added permissions
    if not admin_role:
        # if there is no such group (i.e. - first run) - create it
        admin_role = M2Role.load_or_create(
            name=options.admin_role_name,
            description='Superuser role with all existing permissions'
        )
    # default group for all authorized users
    default_role = M2Role.load_by_params(name=options.default_role_name)
    if not default_role:
        # if there is no such group (i.e. - first run) - create it
        default_role = M2Role.create(
            name=options.default_role_name,
            description='Default user role'
        )

    # now we add default permission, which will be added to all newly created users
    permission = M2Permission.load_by_params(name=options.default_permission)
    if not permission:
        permission = M2Permission.create(name=options.default_permission, system_name=options.default_permission)
    M2RolePermission.load_or_create(
        role_id=default_role.get('id'),
        permission_id=permission.get('id')
    )
    logger.debug(f'added {permission} for `default` role to DB')

    # for new permissions model
    all_perms = PermissionsEnum.all_platform_permissions
    for p in all_perms:
        permission = M2Permission.load_by_params(
            system_name=p.sys_name
        )
        logger.debug(f'checking {permission}')
        if not permission:
            permission = M2Permission.create(
                name=p.name,
                system_name=p.sys_name,
                description=p.description
            )
            M2RolePermission.create(
                role_id=admin_role.get('id'),
                permission_id=permission.get('id')
            )
            logger.debug(f'added {permission} for `admin` role to DB')
        else:
            M2RolePermission.load_or_create(
                role_id=admin_role.get('id'),
                permission_id=permission.get('id')
            )
            logger.debug(f'added {permission} for `admin` role to DB')
            pass


def dump_roles():
    """
    Caches all permissions of each role to Redis
    """
    # TODO: complete refactoring
    roles = M2Role.all()
    for role in roles:
        role.dump_role_permissions()
        logger.debug(f'dumped role {role} to Redis')
