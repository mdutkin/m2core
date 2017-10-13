from tornado import httpclient
from tornado.httputil import HTTPHeaders
import os
import requests
import json
import logging


class RESTTest(object):
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
                    user_agent='DeliveryBoy Unittests',
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
            response = e.response
            response_code = e.response.code
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
