from m2core.bases.base_handler import BaseHandler, http_statuses
from m2core.m2core import M2Core
from tornado import gen
from json.decoder import JSONDecodeError
from sqlalchemy import exc

exceptions_list = [
    (JSONDecodeError, http_statuses['WRONG_REQUEST']),
    (exc.SQLAlchemyError, http_statuses['WRONG_PARAM']),
    (TypeError, {'code': 500, 'msg': 'Custom test error message'})
]


class RestApiDocsHandler(BaseHandler):
    """Returns docstrings per each method of each `human route`"""
    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    @M2Core.requires_permission
    def get(self, *args, **kwargs):
        """Description of `GET` method"""
        self.validate_url_params(kwargs)

        validators = dict()
        for key in self.application.settings['handler_validators'].keys():
            validators[key] = self.application.settings['handler_validators'][key].params()
        handler_permissions = self.application.settings['permissions'].get_all_handler_settings()
        handler_docs = dict()
        for route in self.application.settings['handler_docs']:
            for method in self.application.settings['handler_docs'][route]:
                method_perms = handler_permissions[route][method]
                if method_perms is not None:
                    if not handler_docs.get(route, False):
                        handler_docs[route] = dict()
                    handler_docs[route][method] = self.application.settings['handler_docs'][route][method]
        data = {
            'handler_docs': handler_docs,
            'handler_permissions': handler_permissions,
            'handler_validators': validators,
            'all_system_permissions': self.permissions.get_all_permissions(),
        }
        self.write_json(data=data)
