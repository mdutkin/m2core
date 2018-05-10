__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import unittest
import logging
import os
from unittest.mock import MagicMock
from m2core import M2Core
from m2core.bases import BaseHandler
from m2core.bases import http_statuses
from m2core.utils.tests import RESTTest
from tornado.options import options
from tornado.web import HTTPError
from example.tests.helpers import UserRightsFactory, http_server_request_factory


options.config_name = os.getenv('TEST_CONFIG', 'config_local.py')

m2core = M2Core()


class Exception1(Exception):
    pass


class Exception2(Exception):
    pass


class Exception3(Exception):
    pass


exceptions_list = [
    (Exception1, {'code': 400, 'msg': 'Exception1'}),
    (Exception2, {'code': 403, 'msg': 'Exception2'}),
    (Exception3, {'code': 500, 'msg': 'Exception3'})
]


class SampleTryexHandler(BaseHandler):
    def do_something_with_exception(self):
        pass

    @M2Core.tryex(*exceptions_list)
    def get(self, *args, **kwargs):
        self.do_something_with_exception()
        self.write_json(data='ok')


class SamplePermissionsHandler(BaseHandler):
    @M2Core.requires_permission
    def get(self, *args, **kwargs):
        self.write_json(data='ok')


human_route = r'/not-allowed'
m2core.add_endpoint(human_route, SamplePermissionsHandler)
m2core.add_endpoint_method_permissions(human_route, 'get', None)

human_route = r'/guest'
m2core.add_endpoint(human_route, SamplePermissionsHandler)
m2core.add_endpoint_method_permissions(human_route, 'get', [])

human_route = r'/authenticated'
m2core.add_endpoint(human_route, SamplePermissionsHandler)
m2core.add_endpoint_method_permissions(human_route, 'get', UserRightsFactory.authenticated_permissions)

human_route = r'/authenticated-but-not-enough'
m2core.add_endpoint(human_route, SamplePermissionsHandler)
m2core.add_endpoint_method_permissions(human_route, 'get', [*UserRightsFactory.authenticated_permissions, 'one more'])

human_route = r'/admin'
m2core.add_endpoint(human_route, SamplePermissionsHandler)
m2core.add_endpoint_method_permissions(human_route, 'get', UserRightsFactory.admin_permissions)

app = m2core.run_for_test()


class DecoratorsTest(unittest.TestCase, RESTTest):

    def setUp(self):
        pass

    def test_tryex(self):
        sth = SampleTryexHandler(app, http_server_request_factory(), human_route='/test', urlparser=MagicMock())
        sth.write_json = MagicMock()

        sth.do_something_with_exception = MagicMock(side_effect=Exception1)
        try:
            sth.get()
        except HTTPError as e:
            self.assertEqual(e.log_message, 'Exception1')
            self.assertEqual(e.status_code, 400)
        sth.write_json.assert_not_called()

        sth.do_something_with_exception = MagicMock(side_effect=Exception2)
        try:
            sth.get()
        except HTTPError as e:
            self.assertEqual(e.log_message, 'Exception2')
            self.assertEqual(e.status_code, 403)
        sth.write_json.assert_not_called()

        sth.do_something_with_exception = MagicMock(side_effect=Exception3)
        try:
            sth.get()
        except HTTPError as e:
            self.assertEqual(e.log_message, 'Exception3')
            self.assertEqual(e.status_code, 500)
        sth.write_json.assert_not_called()

    def test_requires_permission_not_allowed(self):
        sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
            'human_route': r'/not-allowed',
            'urlparser': MagicMock()
        })
        sph.write_json = MagicMock()
        sph.current_user = None
        try:
            sph.get()
        except HTTPError as e:
            self.assertEqual(e.log_message, http_statuses['METHOD_NOT_ALLOWED']['msg'])
            self.assertEqual(e.status_code, http_statuses['METHOD_NOT_ALLOWED']['code'])
        sph.write_json.assert_not_called()

    def test_requires_permission_guest(self):
        sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
            'human_route': r'/guest',
            'urlparser': MagicMock()
        })
        sph.write_json = MagicMock()
        sph.current_user = UserRightsFactory.guest()
        sph.get()
        sph.write_json.assert_called_once()

    def test_requires_permission_authenticated(self):
        sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
            'human_route': r'/authenticated',
            'urlparser': MagicMock()
        })
        sph.write_json = MagicMock()
        sph.current_user = UserRightsFactory.authenticated()
        sph.get()
        sph.write_json.assert_called_once()

    def test_requires_permission_authenticated_but_not_enough(self):
        sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
            'human_route': r'/authenticated-but-not-enough',
            'urlparser': MagicMock()
        })
        sph.write_json = MagicMock()
        sph.current_user = UserRightsFactory.authenticated()
        try:
            sph.get()
        except HTTPError as e:
            self.assertEqual(e.log_message, http_statuses['WRONG_CREDENTIALS']['msg'])
            self.assertEqual(e.status_code, http_statuses['WRONG_CREDENTIALS']['code'])
        sph.write_json.assert_not_called()

    def test_requires_permission_admin(self):
        sph = SamplePermissionsHandler(MagicMock(), MagicMock(), **{
            'human_route': r'/admin',
            'urlparser': MagicMock()
        })
        sph.write_json = MagicMock()
        sph.current_user = UserRightsFactory.admin()
        sph.get()
        sph.write_json.assert_called_once()
