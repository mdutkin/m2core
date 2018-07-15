__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import unittest
import os
from unittest.mock import MagicMock, patch
from m2core import M2Core
from m2core.bases import BaseHandler
from m2core.utils.tests import RESTTest
from m2core.common.options import options
from example.tests.helpers import http_server_request_factory


options.config_name = os.getenv('TEST_CONFIG', 'config_local.py')

m2core = M2Core()
app = m2core.run_for_test()


class BaseHandlerTest(unittest.TestCase, RESTTest):

    def setUp(self):
        pass

    @patch('m2core.bases.BaseHandler.finish')
    def test_write_json(self, m_finish):
        bh = BaseHandler(app, http_server_request_factory(), human_route='/test', url_parser=MagicMock())
        payload = [{
                'field1': {
                    'list': [1, 2, '33', None],
                    'dict': {
                        '1': 1,
                        '2': 3
                    },
                }
            },
            'string',
            [10, 22, 33, 44, ]
        ]
        bh.write_json(code=201, msg='Custom message 1', data=payload)
        output_json = """{
  "meta": {
    "code": 201,
    "msg": "Custom message 1"
  },
  "data": [
    {
      "field1": {
        "list": [
          1,
          2,
          "33",
          null
        ],
        "dict": {
          "1": 1,
          "2": 3
        }
      }
    },
    "string",
    [
      10,
      22,
      33,
      44
    ]
  ]
}"""
        self.assertEqual(m_finish.call_args[0][0], output_json)
        bh.write_json(code=400, msg='Custom message 2', data=payload)
        output_json = """{
  "meta": {
    "code": 400,
    "msg": "Custom message 2"
  },
  "data": [
    {
      "field1": {
        "list": [
          1,
          2,
          "33",
          null
        ],
        "dict": {
          "1": 1,
          "2": 3
        }
      }
    },
    "string",
    [
      10,
      22,
      33,
      44
    ]
  ]
}"""
        self.assertEqual(m_finish.call_args[0][0], output_json)
