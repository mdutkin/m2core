from tornado.options import options
# import all handlers
from example.handlers import *
# import core
import logging
from m2core import M2Core, logger as core_logger
from tornado.gen import coroutine, sleep

if __name__ == '__main__':
    # INIT M2CORE
    options.config_name = 'config.py'
    m2core = M2Core()

    # setup core logger level
    core_logger.setLevel(logging.DEBUG)
    # setup project logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # add some headers per every response - CORS
    m2core.add_custom_response_headers({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,OPTIONS',
        'Access-Control-Expose-Headers': '',
        'Access-Control-Max-Age': '1728000',
        'Access-Control-Allow-Headers': 'Content-Type, X-Access-Token'
    })

    # ENDPOINTS
    human_route = r'/docs.js'
    m2core.add_endpoint(human_route, RestApiDocsHandler)
    m2core.add_endpoint_method_permissions(human_route, 'get', [])

    human_route = r'/admin/users/:{id:int}'
    m2core.add_endpoint(human_route, AdminUsersHandler)
    # you can add permissions like that
    m2core.add_endpoint_method_permissions(human_route, 'get', [options.default_permission, 'user_info', 'get'])
    m2core.add_endpoint_method_permissions(human_route, 'post', None)
    m2core.add_endpoint_method_permissions(human_route, 'put', [options.default_permission, 'user_info', 'put'])
    m2core.add_endpoint_method_permissions(human_route, 'delete', [options.default_permission, 'user_info', 'delete'])

    human_route = r'/users'
    m2core.add_endpoint(human_route, AdminUsersHandler)
    # or like that
    m2core.add_endpoint_permissions(human_route, {
        'get': None,
        'post': [],
        'put': None,
        'delete': None,
    })

    human_route = r'/users/self'
    m2core.add_endpoint(human_route, AdminUsersHandler)
    # and that
    m2core.add_endpoint_permissions(human_route, {
        'get': [options.default_permission, ],
        'post': None,
        'put': [options.default_permission, ],
        'delete': [options.default_permission, ],
    })

    human_route = r'/users/login'
    m2core.add_endpoint(human_route, UsersLoginHandler)

    human_route = r'/evil_routes.js'
    m2core.add_endpoint(human_route, EvilRoutesHandler)
    m2core.add_endpoint_method_permissions(human_route, 'get', [options.default_permission, ])

    human_route = r'/schema.js'
    m2core.add_endpoint(human_route, SchemaHandler)
    m2core.add_endpoint_method_permissions(human_route, 'get', [])

    # that's the way you can do something non-blocking in background
    @coroutine
    def my_cool_callback(*args, **kwargs):
        logger.debug('callback was called with:\nargs: %s\nkwargs: %s\nkwargs[\'m2core\']=%s' %
              (args, kwargs, kwargs['m2core']))
        while True:
            # logger.debug('look at me, I\'m infinity!')
            yield sleep(3)
    m2core.add_callback(my_cool_callback, 'arg1', 'arg2', arg3='arg3', arg4='arg4')

    # you can even extend core functionality with your custom functions
    @m2core.extended
    def say_something(self, what_to_say):
        # you'll have M2Core instance in self variable. feel free to do something with it
        # example:
        # m2core_thread_pool = self.thread_pool
        logger.debug("inited m2core: [%s], arg: [%s]" % (type(self), what_to_say))

    # and then call it:
    m2core.say_something('M2Core is great!')

    # also you can do some blocking stuff in background thread like that
    # @coroutine
    # def generate_stream_preview(*args, **kwargs):
    #     def generate_pvw(src):
    #         # this normally blocks main event loop. but we run it in background, so everything is ok
    #         try:
    #             full_path_to_img = 'some_path'
    #             os.system('%s -i %s -vframes 1 %s -y > /dev/null 2>&1' % (
    #                 ffmpeg_path,
    #                 src,
    #                 full_path_to_img
    #             ))
    #             return full_path_to_img
    #         except:
    #             return None
    #
    #     logger.debug('GENERATE STREAM PREVIEW loop started!')
    #     while True:
    #         entities = Source.all()
    #         for entity in entities:
    #             result = yield m2core.thread_pool.submit(generate_pvw, entity.get('source'))
    #             entity.set(
    #                 preview=result
    #             )
    #             entity.save()
    #         yield sleep(30)

    # RUN CORE
    # this will run an application and create all tables if they're not presented in DB
    m2core.run()
    # this will recreate all tables mentioned in your sqlalchemy scheme. be careful while running this on production!!
    # m2core.run_with_recreate()
