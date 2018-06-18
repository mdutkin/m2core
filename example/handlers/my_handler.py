from m2core.bases.base_handler import BaseHandler, http_statuses
from m2core import M2Core
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
    @M2Core.tryex(*exceptions_list)
    @M2Core.user_can
    def get(self, *args, **kwargs):
        """Returns a list of all endpoints with its method where user is allowed to pass"""
        self.write_json(data='Hello, world!')
