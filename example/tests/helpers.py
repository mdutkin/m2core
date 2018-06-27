__author__ = 'Maxim Dutkin (max@dutkin.ru)'


from unittest.mock import MagicMock
from tornado.httputil import HTTPServerRequest


class OldUserRightsFactory:
    admin_permissions = ['admin', 'authenticated', ]
    authenticated_permissions = ['authenticated', ]

    def __init__(self):
        self.default_obj = {
                'id': 1,
                'access_token': 'generated_access_token',
                'permissions': []
            }

    @classmethod
    def admin(cls):
        _ = cls()
        _.default_obj.update(permissions=cls.admin_permissions)
        return _.default_obj

    @classmethod
    def guest(cls):
        return None

    @classmethod
    def authenticated(cls):
        _ = cls()
        _.default_obj.update(permissions=cls.authenticated_permissions)
        return _.default_obj


def http_server_request_factory(
        method='GET',
        uri='/',
        version='HTTP/1.1',
        headers=None,
        body=None,
        host='m2core.loc:9999',
        files=None,
        connection=None,
        start_line=None,
        server_connection=None) -> HTTPServerRequest:
    _ = HTTPServerRequest(
        method=method,
        uri=uri,
        version=version,
        headers=headers,
        body=body,
        host=host,
        files=files,
        connection=connection or MagicMock(),
        start_line=start_line,
        server_connection=server_connection or MagicMock()
    )
    return _
