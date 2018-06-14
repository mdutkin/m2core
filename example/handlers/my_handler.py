from m2core.bases.base_handler import BaseHandler, http_statuses
from m2core import M2Core
from example.run_me import m2core
from tornado import gen
from json.decoder import JSONDecodeError
from sqlalchemy import exc

exceptions_list = [
    (JSONDecodeError, http_statuses['WRONG_REQUEST']),
    (exc.SQLAlchemyError, http_statuses['WRONG_PARAM']),
    (TypeError, {'code': 500, 'msg': 'Custom test error message'})
]


class MyHandler(BaseHandler):
    """
    New permissions testing
    """
    @gen.coroutine
    # @M2Core.tryex(*exceptions_list)
    @M2Core.user_can
    def get(self, *args, **kwargs):
        """Returns a list of all endpoints with its method where user is allowed to pass"""
        me = self.current_user
        permitted_handlers = self.application.settings['permissions'].get_all_permitted_handlers(me['permissions'])
        data = dict()
        for human_route in permitted_handlers.keys():
            data[human_route] = dict()
            data[human_route]['url_params'] = self.application.settings['handler_validators'][human_route].params()
            data[human_route]['methods'] = dict()
            for method in permitted_handlers[human_route]:
                data[human_route]['methods'][method] = self.application.settings['handler_docs'][human_route][method]
        print(m2core)
        self.write_json(data=data)
