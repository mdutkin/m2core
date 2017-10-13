from m2core.bases.base_handler import BaseHandler, http_statuses
from m2core.m2core import M2Core
from example.models import User
from tornado import gen
from json.decoder import JSONDecodeError
from sqlalchemy import exc


exceptions_list = [
    (JSONDecodeError, http_statuses['WRONG_REQUEST']),
    (exc.SQLAlchemyError, http_statuses['WRONG_PARAM']),
    (TypeError, {'code': 500, 'msg': 'Custom test error message'})
]


class SchemaHandler(BaseHandler):
    """Generates JSON-scheme which could be used by front, i.e. your FormGenerator in React SPA"""
    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    @M2Core.requires_permission
    def get(self, *args, **kwargs):
        """Generates JSON-scheme of DB models"""
        data = User.schema(True)
        self.write_json(data=data)
