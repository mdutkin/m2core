__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import unittest
import os
from unittest.mock import MagicMock
from example.handlers.my_handler import MyHandler
from m2core import M2Core
from m2core.bases import BaseHandler, http_statuses
from m2core.common import PermissionsEnum, Permission
from m2core.utils.tests import RESTTest, M2CoreAsyncHTTPTestCase
from tornado.options import options
from tornado.web import HTTPError
from tornado.testing import AsyncHTTPTestCase
from example.tests.helpers import OldUserRightsFactory, http_server_request_factory


options.config_name = os.getenv('TEST_CONFIG', 'config_local.py')


class UserCanTest(M2CoreAsyncHTTPTestCase):
    def init_m2core(self):
        m2core = M2Core()

        class SamplePermissionsHandler(BaseHandler):
            @M2Core.user_can
            def get(self, *args, **kwargs):
                self.write_json(data='ok')

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

        self.sph = SamplePermissionsHandler
        self.pp = PlatformPermissions

        human_route = r'/'
        m2core.route(human_route=human_route, handler_cls=MyHandler, get=PlatformPermissions.SKIP)

        human_route = r'/not-allowed'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=None)

        human_route = r'/guest'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=PlatformPermissions.SKIP)

        human_route = r'/authenticated'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=PlatformPermissions.AUTHORIZED)

        human_route = r'/authenticated-but-not-enough'
        m2core.route(
            human_route=human_route,
            handler_cls=SamplePermissionsHandler,
            get=PlatformPermissions.AUTHORIZED & PlatformPermissions.VIEW_SOME_INFO &
                PlatformPermissions.EDIT_SOME_INFO
        )

        human_route = r'/admin'
        m2core.route(human_route=human_route, handler_cls=SamplePermissionsHandler, get=PlatformPermissions.ALL)

        return m2core

    def test_root(self):
        response = self.fetch_json('/')
        self.assertEqual('Hello, world!', response['data'])

    def test_not_allowed(self):
        response = self.fetch_json('/not-allowed', expected_codes={405, })
        self.assertEqual(None, response['data'])

    def test_guest(self):
        response = self.fetch_json('/guest')
        self.assertEqual('Hello, world!', response['data'])

    # def test_requires_permission_not_allowed(self):
    #     sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
    #         'human_route': r'/not-allowed',
    #         'url_parser': MagicMock()
    #     })
    #     sph.write_json = MagicMock()
    #     sph.current_user = None
    #     try:
    #         sph.get()
    #     except HTTPError as e:
    #         self.assertEqual(e.log_message, http_statuses['METHOD_NOT_ALLOWED']['msg'])
    #         self.assertEqual(e.status_code, http_statuses['METHOD_NOT_ALLOWED']['code'])
    #     sph.write_json.assert_not_called()
    #
    # def test_requires_permission_guest(self):
    #     sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
    #         'human_route': r'/guest',
    #         'url_parser': MagicMock()
    #     })
    #     sph.write_json = MagicMock()
    #     sph.current_user = OldUserRightsFactory.guest()
    #     sph.get()
    #     sph.write_json.assert_called_once()
    #
    # def test_requires_permission_authenticated(self):
    #     sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
    #         'human_route': r'/authenticated',
    #         'url_parser': MagicMock()
    #     })
    #     sph.write_json = MagicMock()
    #     sph.current_user = OldUserRightsFactory.authenticated()
    #     sph.get()
    #     sph.write_json.assert_called_once()
    #
    # def test_requires_permission_authenticated_but_not_enough(self):
    #     sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
    #         'human_route': r'/authenticated-but-not-enough',
    #         'url_parser': MagicMock()
    #     })
    #     sph.write_json = MagicMock()
    #     sph.current_user = OldUserRightsFactory.authenticated()
    #     try:
    #         sph.get()
    #     except HTTPError as e:
    #         self.assertEqual(e.log_message, http_statuses['WRONG_CREDENTIALS']['msg'])
    #         self.assertEqual(e.status_code, http_statuses['WRONG_CREDENTIALS']['code'])
    #     sph.write_json.assert_not_called()
    #
    # def test_requires_permission_admin(self):
    #     sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
    #         'human_route': r'/admin',
    #         'url_parser': MagicMock()
    #     })
    #     sph.write_json = MagicMock()
    #     sph.current_user = OldUserRightsFactory.admin()
    #     sph.get()
    #     sph.write_json.assert_called_once()
