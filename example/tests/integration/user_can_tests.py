__author__ = 'Maxim Dutkin (max@dutkin.ru)'


from m2core import M2Core
from m2core.bases import BaseHandler, http_statuses
from m2core.common import PermissionsEnum, Permission
from m2core.utils.tests import M2CoreAsyncHTTPTestCase


class SamplePermissionsHandler(BaseHandler):
    @M2Core.user_can
    def get(self, *args, **kwargs):
        self.write_json(data='ok')


class UserCanTest(M2CoreAsyncHTTPTestCase):
    def init_m2core(self):
        class PlatformPermissions(PermissionsEnum):
            AUTHORIZED = Permission(
                name='Authorized users',
                sys_name='authorized',
                description='All authorized users will have this permission by default (overwrites default '
                            '`AUTHORIZED` permission)'
            )
            VIEW_SOME_INFO = Permission(
                name='View some info',
                sys_name='view_some_info',
                description='Example of some view permissions'
            )
            EDIT_SOME_INFO = Permission(
                name='Edit some info',
                sys_name='edit_some_info',
                description='Example of some edit permissions'
            )
            DELETE_SOME_INFO = Permission(
                name='Delete some info',
                sys_name='delete_some_info',
                description='Example of some delete permissions'
            )
            ADMIN = Permission(
                name='Admin privilege',
                sys_name='admin',
                description='Example of admin (super user) permissions'
            )
            
        self.pp = PlatformPermissions
        m2core = M2Core()

        human_route = r'/'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=self.pp.SKIP)

        human_route = r'/not-allowed'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=None)

        human_route = r'/guest'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=self.pp.SKIP)

        human_route = r'/authenticated'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=self.pp.AUTHORIZED)

        human_route = r'/authenticated-but-not-enough'
        m2core.route(
            human_route=human_route,
            handler_cls=SamplePermissionsHandler,
            get=self.pp.AUTHORIZED & self.pp.VIEW_SOME_INFO &
                self.pp.EDIT_SOME_INFO
        )

        human_route = r'/admin'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=self.pp.ALL)

        return m2core

    def test_root(self):
        response = self.fetch_json('/')
        self.assertEqual('ok', response['data'])

    def test_not_allowed(self):
        response = self.fetch_json('/not-allowed', expected_codes={http_statuses['METHOD_NOT_ALLOWED']['code'], })
        self.assertEqual(None, response['data'])

    def test_guest(self):
        response = self.fetch_json('/guest')
        self.assertEqual('ok', response['data'])

    def test_authenticated(self):
        response = self.fetch_json('/authenticated', user_permissions={self.pp.AUTHORIZED, })
        self.assertEqual('ok', response['data'])

        response = self.fetch_json(
            '/authenticated-but-not-enough',
            user_permissions={self.pp.AUTHORIZED, },
            expected_codes={http_statuses['WRONG_CREDENTIALS']['code'], }
        )
        self.assertEqual(None, response['data'])

    def test_authenticated_but_not_enough(self):
        response = self.fetch_json(
            '/authenticated-but-not-enough',
            user_permissions={self.pp.AUTHORIZED, self.pp.VIEW_SOME_INFO, },
            expected_codes={http_statuses['WRONG_CREDENTIALS']['code'], }
        )
        self.assertEqual(None, response['data'])

        response = self.fetch_json(
            '/authenticated-but-not-enough',
            user_permissions={self.pp.AUTHORIZED, self.pp.VIEW_SOME_INFO,
                              self.pp.EDIT_SOME_INFO}
        )
        self.assertEqual('ok', response['data'])
