from m2core.bases.base_handler import BaseHandler, http_statuses
from m2core.m2core import M2Core
from collections import defaultdict
from tornado import gen
from json.decoder import JSONDecodeError
from sqlalchemy import exc

exceptions_list = [
    (JSONDecodeError, http_statuses['WRONG_REQUEST']),
    (exc.SQLAlchemyError, http_statuses['WRONG_PARAM']),
    (TypeError, {'code': 500, 'msg': 'Custom test error message'})
]


class EvilRoutesHandler(BaseHandler):
    """Accessible by /evil_routes.js. Returns a list of all endpoints with its method where user is allowed to pass"""
    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    @M2Core.user_can
    def get(self, *args, **kwargs):
        """Returns a list of all endpoints with its method where user is allowed to pass"""
        me = self.current_user

        allowed_routes = defaultdict(list)
        for human_route, route in M2Core.rules.items():
            for method, p in route['permissions'].items():
                if p is not None and p(me['permissions']):
                    allowed_routes[human_route].append(method)
        self.write_json(data=allowed_routes)
