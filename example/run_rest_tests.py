import unittest
from tornado.options import define, options
from m2core.utils.tests import RESTTest
from m2core.utils.data_helper import DataHelper
from m2core import M2Core
from m2core.bases import http_statuses
from tornado.escape import json_decode
from example.models import User


# init empty object to pass it through all of your tests
class SomeData:
    pass


test_data = SomeData()
test_data.test_access_token = None  # access token for REST requests
test_data.users_count = 3  # amount of test users to create
test_data.test_users = list()  # test users list


# unit testing config
define('test_server', 'm2core.loc')
define('test_protocol', 'http')
define('test_port', 8888)
define('test_login', 'unittest')
define('test_password', 'unittest')
define('test_username', 'name')
define('test_surname', 'surname')
define('test_email', 'unitest@mail.ru')
define('test_phone', '+7(111)111-11-11')

options.config_name = 'config_local.py'
m2core = M2Core()
domain_name = '%s://%s:%s' % (
    options.test_protocol,
    options.test_server,
    options.test_port,
)


class TestMyREST(unittest.TestCase, RESTTest):
    def test_00_base_model(self):
        # test auto modification of updated field from CreatedMixin
        modified_user = User.load_or_create(email='some@email.com', gender=0)
        updated_date = modified_user.get('updated')
        modified_user.save()
        self.assertNotEqual(updated_date, modified_user.get('updated'), msg='`updated` filed didn\'t update on save()')
        modified_user.delete()
        self.report_completed('test_00_base_model')

    def test_01_user_create(self):
        user = User.load_by_params(email=options.test_email)
        # drop test user from DB if it exists
        if user:
            user.delete()

        for i in range(1, test_data.users_count + 1):
            # create users, first one will be admin
            email = '%s@m2.group' % DataHelper.random_char(6)
            result = self.fetch_data({
                'method': 'POST',
                'url': '%s/users' % domain_name,
                'codes': [
                    http_statuses['CREATED']['code'],
                ],
                'data': {
                    'name': options.test_username if i == 1 else options.test_username + ' %s' % i,
                    'password': options.test_password,
                    'email': options.test_email if i == 1 else email,
                    'gender': 0
                }
            })
            if i != 1:
                result1 = self.fetch_data({
                    'method': 'POST',
                    'url': '%s/users/login' % domain_name,
                    'codes': [
                        http_statuses['OK']['code'],
                    ],
                    'data': {
                        'email': email,
                        'password': options.test_password,
                    }
                })
                data = json_decode(result1)['data']
                test_data.test_users.append(data)
                at = data['access_token']
                print('at: %s %s' % (data['user_info']['id'], at))

        user = User.load_by_params(email=options.test_email)
        user.add_role(options.admin_role_name)

        self.report_completed('test_01_user_create')

    def test_02_user_login(self):
        # login user. after login he gets access token, which gives him some permissions
        result = self.fetch_data({
            'method': 'POST',
            'url': '%s/users/login' % domain_name,
            'codes': [
                http_statuses['OK']['code'],
            ],
            'data': {
                'email': options.test_email,
                'password': options.test_password,
            }
        })
        test_data.test_access_token = json_decode(result)['data']['access_token']
        self.assertGreater(len(test_data.test_access_token), 0, msg='Received empty access token')

        print('access token is: %s' % test_data.test_access_token)
        self.report_completed('test_02_user_login')

    def test_03_evil_routes(self):
        # test our special handler
        result = self.fetch_data({
            'method': 'GET',
            'url': '%s/evil_routes.js?access_token=%s' % (domain_name, test_data.test_access_token),
            'codes': [
                http_statuses['OK']['code'],
            ],
            'data': None
        })
        routes = json_decode(result)['data']
        self.assertGreater(len(routes.keys()), 0, msg='Received empty access token')

        self.report_completed('test_03_evil_routes')

    def test_04_admin_get_and_modify_user(self):
        for user in test_data.test_users:
            # get user's info by id (for admins only)
            self.fetch_data({
                'method': 'GET',
                'url': '%s/admin/users/%s?access_token=%s' % (domain_name, user['user_info']['id'], test_data.test_access_token),
                'codes': [
                    http_statuses['OK']['code'],
                ],
                'data': None
            })
            self.fetch_data({
                'method': 'PUT',
                'url': '%s/admin/users/%s?access_token=%s' % (domain_name, user['user_info']['id'], test_data.test_access_token),
                'codes': [
                    http_statuses['CREATED']['code'],
                ],
                'data': {
                    'name': 'Modified %s' % user['user_info']['id'],
                    'password': 'new_cool_pass',
                    'gender': 1
                }
            })

        self.report_completed('test_04_admin_get_and_modify_user')

    def test_05_admin_delete_user(self):
        # delete user by id (for admin only)
        user = test_data.test_users.pop()
        self.fetch_data({
            'method': 'DELETE',
            'url': '%s/admin/users/%s?access_token=%s' % (domain_name, user['user_info']['id'], test_data.test_access_token),
            'codes': [
                http_statuses['OK']['code'],
            ],
            'data': None
        })

        self.report_completed('test_05_admin_delete_user')

    def test_06_schema(self):
        # test our special handler
        result = self.fetch_data({
            'method': 'GET',
            'url': '%s/schema.js?access_token=%s' % (domain_name, test_data.test_access_token),
            'codes': [
                http_statuses['OK']['code'],
            ],
            'data': None
        })
        schema = json_decode(result)['data']
        self.assertEqual(list(schema.keys()), ['user'], msg='Received wrong json')
        self.assertEqual(list(schema['user'].keys()),
                         ['id', 'email', 'password', 'name', 'gender', 'created', 'updated'],
                         msg='Received wrong json')

        self.report_completed('test_06_schema')

    def test_06_restrict_access(self):
        # get first random user with default roles
        user = test_data.test_users[0]
        # on this endpoint you can only get with admin's rights
        result = self.fetch_data({
            'method': 'GET',
            'url': '%s/admin/schema.js?access_token=%s' % (domain_name, user['access_token']),
            'codes': [
                http_statuses['WRONG_CREDENTIALS']['code'],
            ],
            'data': None
        })
        # now with admin token
        result = self.fetch_data({
            'method': 'GET',
            'url': '%s/admin/schema.js?access_token=%s' % (domain_name, test_data.test_access_token),
            'codes': [
                http_statuses['OK']['code'],
            ],
            'data': None
        })
        schema = json_decode(result)['data']
        self.assertEqual(list(schema.keys()), ['user'], msg='Received wrong json')
        self.assertEqual(list(schema['user'].keys()),
                         ['id', 'email', 'password', 'name', 'gender', 'created', 'updated'],
                         msg='Received wrong json')

        self.report_completed('test_06_schema')
