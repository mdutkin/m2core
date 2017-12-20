import traceback
import logging
from tornado import escape
from tornado.escape import *
from tornado.web import HTTPError
from tornado.web import RequestHandler
from tornado.options import options
from m2core.utils.session_helper import SessionHelper
from m2core.db.sqlalchemy_json import AlchemyJSONEncoder

# 200 – OK – All is working, normal answer for any ordinary request
# 201 – OK – Returned if resource was created successfully (POST or PUT)
# 204 – OK – Returned if resource was deleted successfully (DELETE)
# 304 – Not Modified – Resource was not modified
# 400 – Bad Request – Wrong request or request couldn't be served.
# 401 – Unauthorized – Authorization required for this resource
# 403 – Forbidden – Not enough permissions for this resource
# 404 – Not found
# 422 – Unprocessable Entity – Server couldn't serve this request because there is not enough data
# 500 – Internal Server Error – Internal server error. Normally doesn't show up )

http_statuses = {
    'OK': {'code': 200, 'msg': 'OK'},
    'CREATED': {'code': 201, 'msg': 'Successfully created/updated content'},
    'NO_CONTENT': {'code': 204, 'msg': 'Request is ok, but response body is empty'},
    'NOT_MODIFIED': {'code': 304, 'msg': 'Resource not modified'},
    'HIDDEN_ERR': {'code': 400, 'msg': 'You\'re not allowed to do this kind of things. %s'},
    'ANY_ERR': {'code': 400, 'msg': 'An error occurred because you\'ve passed incorrect data.'},
    'WRONG_FILENAME': {'code': 400, 'msg': 'Wrong filename was given'},
    'WRONG_CREDENTIALS': {'code': 403, 'msg': 'Your access token is not valid to access content'},
    'NO_OBJ_FOUND': {'code': 404, 'msg': 'There is no requested <object> in a system'},
    'NO_MEDIA_FOUND': {'code': 404, 'msg': 'There is no requested <media> in a system'},
    'NO_CUR_BIKE': {'code': 404, 'msg': 'You can only operate with currently selected bike, nothing is selected now'},
    'METHOD_NOT_ALLOWED': {'code': 405, 'msg': 'A request method is not supported for the requested resource.'},
    'WRONG_PARAM': {'code': 409, 'msg': 'Wrong parameter(s) was(were) passed in request'},
    'WRONG_REQUEST': {'code': 409, 'msg': 'Wrong formed request, no conditions available to complete it'},
    'NOT_ENOUGH_PARAM': {'code': 409, 'msg': 'Not enough params were given to complete the request'},
    'WRONG_PARAM_WITH_EXC': {'code': 422, 'msg': 'Wrong parameter(s) was(were) passed in request. %s'},
    'DUPLICATE_IN_DB': {'code': 422, 'msg': 'There is already an entry in DB with equal value(s), must be unique. %s'},
    'SRV_INTERNAL_ERR': {'code': 500, 'msg': 'Core server error has occurred. We are soooo sorry :('},
    'NOT_IMPLEMENTED': {'code': 500, 'msg': 'Request is ok, but server has no implementation for this method'},
}


logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        """
        Constructor
        :param application: 
        :param request: 
        :param kwargs: 
        """
        self._redis = application.settings['redis']
        self._session = application.settings['db']
        self._endpoints = application.settings['endpoints']
        self._handler_docs = application.settings['handler_docs']
        self._handler_validators = application.settings['handler_validators']
        self._custom_response_headers = application.settings['custom_response_headers']
        self._permissions = application.settings['permissions']
        self._thread_pool = application.settings['thread_pool']
        self._url_parser = lambda x: True
        self._human_route = ''
        """Expire sql alchemy inner cache when initializing BaseHandler for incoming client"""
        if options.expire_on_connect:
            self._session.expire_all()
        super(BaseHandler, self).__init__(application, request, **kwargs)

    def set_default_headers(self):
        """
        Mixin some additional headers (CORS i.e.) if there are any
        :return: 
        """
        for header in self._custom_response_headers.keys():
            self.set_header(header, self._custom_response_headers[header])

    def initialize(self, **kwargs):
        """
        Called during initialization (from RequestHandler)
        :param kwargs: 
        :return: 
        """
        self._human_route = kwargs['human_route']
        self._url_parser = kwargs['urlparser']

    def validate_url_params(self, params: dict):
        """
        Additional url validation
        :param params: 
        :return: 
        """
        self._url_parser.validator_schema()(params)

    def get(self, *args, **kwargs):
        """
        Default 404 code for not implemented GET-method
        :param args: 
        :param kwargs: 
        :return: 
        """
        logger.warning('Access to not implemented GET-method')
        raise HTTPError(http_statuses['NO_OBJ_FOUND']['code'],
                        http_statuses['NO_OBJ_FOUND']['msg'])

    def write_error(self, status_code: int, **kwargs):
        """Override to implement custom error pages.

        ``write_error`` may call `write`, `render`, `set_header`, etc
        to produce output as usual.

        If this error was caused by an uncaught exception (including
        HTTPError), an ``exc_info`` triple will be available as
        ``kwargs["exc_info"]``.  Note that this exception may not be
        the "current" exception for purposes of methods like
        ``sys.exc_info()`` or ``traceback.format_exc``.
        """
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            self.set_header('Content-Type', 'text/plain; charset=utf-8')
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish()
        else:
            http_error = None
            for line in kwargs["exc_info"]:
                if isinstance(line, HTTPError):
                    http_error = line
                    break
            self.set_header('Content-Type', 'application/json; charset=utf-8')
            err_msg = ''
            if http_error:
                err_msg = http_error.log_message
            self.write_json(
                code=status_code if status_code else http_statuses['SRV_INTERNAL_ERR']['code'],
                msg=err_msg
            )

    def write_json(self, code: int=200, msg: str=None, data: any=None):
        """
        Writes json response to client, decoding `data` to json with HTTP-header
        :param code: HTTP response code
        :param msg: status code message
        :param data: data to pass to client
        :return:
        """
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.set_status(code, msg)
        if code == 204:
            # status code expects no body
            self.finish()
        else:
            result = {
                'meta':
                    {
                        'code': self._status_code,
                        'msg': self._reason,
                    },
                'data': data,
            } if code != 204 else None
            self.finish(json.dumps(result,
                                   indent=options.json_indent,
                                   cls=AlchemyJSONEncoder).
                        replace("</", "<\\/"))

    def get_current_user(self):
        """
        Called only once when `self.current_user` is used at first time. If `None` is returned, then
        decorator `@authenticated` (and also `@authenticated_json` in our M2-case) will raise 403 HTTPError,
        otherwise it has to return some data, i.e. `integer` user ID
        """
        # looking for access_token in GET params, then in X-Access-Token header
        # TODO: add Cookie support
        token = (self.get_argument("access_token", None) or
                 self.request.headers.get("X-Access-Token"))
        try:
            if not token and self.request.headers.get('Content-Type') and 'application/json;' \
                    in self.request.headers.get('Content-Type').lower():
                body = escape.json_decode(self.request.body)
                token = body['access_token']
        except json.decoder.JSONDecodeError as err:
            # not a json :(
            logger.warning('Access token in request body is not a JSON')
        except KeyError as err:
            # no `access_token` field in json
            logger.warning('no `access_token` field in request body JSON')

        if not token:
            return None

        session = SessionHelper(self._redis['connector'], self._redis['scheme'])
        session.init_user(token)
        return {
            'id': session.get_user_id(),
            'access_token': session.get_token(),
            'permissions': session.get_user_permissions()
        }

    def session_helper_factory(self) -> SessionHelper:
        """
        This helper needed to interact with redis to store and get permissions data
        :return: 
        """
        session_helper = SessionHelper(self._redis['connector'], self._redis['scheme'])
        if self.current_user:
            session_helper.init_user(self.current_user['access_token'])
        return session_helper

    def options(self, *args, **kwargs):
        pass
