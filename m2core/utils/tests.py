from unittest.mock import patch
from m2core.utils.session_helper import SessionHelper
from m2core.utils.data_helper import DataHelper
from m2core import M2Core
from contextlib import ContextDecorator
from tornado import httpclient
from tornado.escape import json_decode
from tornado.httputil import HTTPHeaders
from tornado.testing import AsyncHTTPTestCase
from m2core.common.options import options
import json
import logging


class RESTTest:
    """
    Helper class for unittests
    """
    def setUp(self):
        """
        All initial settings can be made here
        """
        pass

    @staticmethod
    def report_completed(test_name):
        """
        Reports of successfully passed test
        :param test_name: 
        :return: 
        """
        logging.info('== ' + test_name + ' passed!')

    def fetch_data(self, endpoint: dict()) -> bytes:
        """
        Получаем/отправляем данные на сервер
        Fetches/sends data on server (depends on method)
        :param endpoint: dict with special structure (example):
            {
                'method': 'POST',
                'url': 'http://example.com',
                'codes': [201, 304],
                'data': {
                    'some': 'variables',
                    'to': 'send'
                }
            }
        
        Example for registering user:
        
        self.fetch_data({
            'method': 'POST',
            'url': '%s/authorization/register' % domain_name,
            'codes': [
                http_statuses['CREATED']['code'],
            ],
            'data': {
                'email': tornado_settings['test_email'],
                'password': tornado_settings['test_password'],
                'name': tornado_settings['test_username'],
                'surname': tornado_settings['test_surname'],
                'phone': tornado_settings['test_phone']
            }
        })
        
        :return: bytes
        """
        http_client = httpclient.HTTPClient()
        try:
            # if method is PUT or POST - it means we will send data to server. since M2Core is JSON-based
            # REST-api core, we'll form a JSON, place it in body and add special headers
            if endpoint['method'] not in ['POST', 'PUT']:
                request = httpclient.HTTPRequest(
                    endpoint['url'],
                    method=endpoint['method'],
                    follow_redirects=False,
                    user_agent='M2Core Unittests',
                    use_gzip=False,
                    allow_nonstandard_methods=True,
                    connect_timeout=5
                )
            else:
                # prepare headers
                h = HTTPHeaders({'Content-Type': 'application/json; charset=utf-8'})
                # and body. make it JSON if it has dict() type
                b = json.dumps(endpoint['data']) if isinstance(endpoint['data'], dict) else endpoint['data']
                request = httpclient.HTTPRequest(
                    endpoint['url'],
                    method=endpoint['method'],
                    follow_redirects=False,
                    user_agent='M2Core Unittests',
                    use_gzip=False,
                    allow_nonstandard_methods=True,
                    connect_timeout=5,
                    headers=h,
                    body=b
                )

            response = http_client.fetch(request)
            response_code = response.code
        except httpclient.HTTPError as e:
            # HTTPError is raised for non-200 responses; the response
            # can be found in e.response.
            # 599 - Timeout
            response = e.response if e.code != 599 else None
            response_code = e.code
        self.assertIn(response_code, endpoint['codes'], 'Received unexpected HTTP-code [%s][%s] from %s' % (
            response_code, endpoint['method'], endpoint['url']))
        http_client.close()
        return response.body

    def upload_file(self, filename: str) -> bytes:
        """
        Uploads data to server.
        """
        # TODO: refactor and test it!
        # cur_dir = os.path.dirname(os.path.realpath(__file__))
        # data = requests.post('%s/upload?access_token=%s' % (domain_name, test_customer.test_access_token),
        #                      files={'file': open(cur_dir + '/test.jpg', 'rb')},
        #                      headers={'user-agent': 'DeliveryBoy Unittests'})
        #
        # id = json_decode(data.content)['data']['id']


class M2CoreAsyncHTTPTestCase(AsyncHTTPTestCase):
    """
    Possible options for self.fetch():

        method="GET", headers=None, body=None,
        auth_username=None, auth_password=None, auth_mode=None,
        connect_timeout=None, request_timeout=None,
        if_modified_since=None, follow_redirects=None,
        max_redirects=None, user_agent=None, use_gzip=None,
        network_interface=None, streaming_callback=None,
        header_callback=None, prepare_curl_callback=None,
        proxy_host=None, proxy_port=None, proxy_username=None,
        proxy_password=None, proxy_auth_mode=None,
        allow_nonstandard_methods=None, validate_cert=None,
        ca_certs=None, allow_ipv6=None, client_key=None,
        client_cert=None, body_producer=None,
        expect_100_continue=False, decompress_response=None,
        ssl_options=None

    """
    def init_m2core(self):
        raise NotImplemented('You must implement method which returns M2Core instance')

    def get_app(self):
        self.m2core = self.init_m2core()
        options.debug = False
        return self.m2core.run_for_test()

    def fetch_bytes(self, url: str, method: str= 'GET', expected_codes=None, data=None, user_permissions=None,
                    **kwargs) -> bytes:
        """
        Получаем/отправляем данные на сервер
        Fetches/sends data on server (depends on method)
        :param url: dict with special structure (example):
            {
                'method': 'POST',
                'url': 'http://example.com',
                'codes': [201, 304],
                'data': {
                    'some': 'variables',
                    'to': 'send'
                }
            }
        :param method:
        :param expected_codes:
        :param data:

        Example for registering user:

        self.fetch_data({
            'method': 'POST',
            'url': '%s/authorization/register' % domain_name,
            'codes': [
                http_statuses['CREATED']['code'],
            ],
            'data': {
                'email': tornado_settings['test_email'],
                'password': tornado_settings['test_password'],
                'name': tornado_settings['test_username'],
                'surname': tornado_settings['test_surname'],
                'phone': tornado_settings['test_phone']
            }
        })

        :return: bytes
        """
        if expected_codes is None:
            expected_codes = {200, }
        options = kwargs
        # if method is PUT or POST - it means we will send data to server. since M2Core is JSON-based
        # REST-api core, we'll form a JSON, place it in body and add special headers
        h = HTTPHeaders()
        if user_permissions:
            # hack for test user
            rnd_at = DataHelper.random_hex_str(16)
            self.m2core.add_test_user(rnd_at, permissions=user_permissions)
            h.add('X-Access-Token', rnd_at)

        if method not in ['POST', 'PUT']:
            options.update(dict(
                method=method,
                follow_redirects=False,
                user_agent='M2Core Unittests',
                use_gzip=False,
                allow_nonstandard_methods=True,
                connect_timeout=5,
                headers=h
            ))
        else:
            # prepare headers
            h.add('Content-Type', 'application/json; charset=utf-8')
            # and body. make it JSON if it has dict() type
            b = json.dumps(data) if isinstance(data, dict) else data
            options.update(dict(
                method=method,
                follow_redirects=False,
                user_agent='M2Core Unittests',
                use_gzip=False,
                allow_nonstandard_methods=True,
                connect_timeout=5,
                headers=h,
                body=b
            ))

        response = self.fetch(url, **options)
        response_code = response.code
        self.assertIn(response_code, expected_codes, 'Received unexpected HTTP-code [%s][%s] from %s' % (
            response_code, method, url))
        return response.body

    def fetch_json(self, url: str, method: str = 'GET', expected_codes=None, data=None,
                   user_permissions=None, **kwargs) -> dict:
        return json_decode(self.fetch_bytes(url, method, expected_codes, data, user_permissions, **kwargs))

    def upload_file(self, filename: str) -> bytes:
        """
        Uploads data to server.
        """
        # TODO: refactor and test it!
        # cur_dir = os.path.dirname(os.path.realpath(__file__))
        # data = requests.post('%s/upload?access_token=%s' % (domain_name, test_customer.test_access_token),
        #                      files={'file': open(cur_dir + '/test.jpg', 'rb')},
        #                      headers={'user-agent': 'DeliveryBoy Unittests'})
        #
        # id = json_decode(data.content)['data']['id']
