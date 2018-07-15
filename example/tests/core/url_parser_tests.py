__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import unittest
from m2core import M2Core
from m2core.utils.url_parser import UrlParser
from m2core.utils.tests import RESTTest
from voluptuous import Schema, Error


class UrlParserTest(unittest.TestCase, RESTTest):

    def setUp(self):
        m2core = M2Core()
        m2core.run_for_test()

    def test_parser(self):
        valid_urls = {
            # for bool
            '/users/:{id:bool}': {
                'valid': ['0', '1', 'False', 'yes', 'on', 'ON'],
                'invalid': ['suka', 'pido3r']
            },

            # for int
            '/users/:{id}': {
                'valid': ['1', '2', '10000', '-1', 'asdasaaad'],
                'invalid': [],
            },
            '/users/:{id:int}': {
                'valid': [' 000', '-1'],
                'invalid': ['hello', 'hello2']
            },
            '/users/:{id:int(3)}': {
                'valid': ['1', '2', '3', '4', '5', '100'],
                'invalid': ['hel', '3342', '-999']
            },
            '/users/:{id:int(0,[0-100])}': {
                'valid': ['0', '1', '3', '99', '100'],
                'invalid': ['1000', '-1000', '-1', '101']
            },

            # for float
            '/users/:{id:float}': {
                'valid': ['1', '2', '3', '1000', '-1', '2.', '3.', '2.0', '3.52'],
                'invalid': ['hello', 'hello2']
            },
            '/users/:{id:float(3)}': {
                'valid': ['1', '2', '3', '4', '5', '100', '2.', '3.', '2.0', '3.53333'],
                'invalid': ['hel', '3342', '-999', '3333.3']
            },
            '/users/:{id:float(0,[0-100])}': {
                'valid': ['0', '1', '3', '99', '100', '2.', '3.', '2.0', '3.5'],
                'invalid': ['1000', '-1000', '-1', '101', '3333.3']
            },

            # for string
            '/users/:{id:string}': {
                'valid': ['hello', 'hello1'],
                'invalid': ['', None],
            },
            '/users/:{id:string(3)}': {
                'valid': ['he', 'hee', 'h'],
                'invalid': ['hhhh', 'h1h2'],
            },
            '/users/:{id:string(0,[tet;te1;te2])}': {
                'valid': ['tet', 'te1', 'te2'],
                'invalid': [None, '', 'test1', 'tests13', 'te3']
            },
        }
        invalid_urls = [
            '/users/:{id{}}',
            '/users/:{{id}}}',
            '/users/:{id:int{}',
            '/users/:{id:int()}',
            '/users/:{id:float)}',
            '/users/:{id:float(}',
            '/users/:{id:string_}',
        ]
        # test for valid and invalid params validators
        for url_rule in valid_urls.keys():
            parser = UrlParser(url_rule)
            for attr in parser.url_attributes:
                validator = attr['instance'].validator()
                if validator:
                    s = Schema(validator)
                    for valid_key in valid_urls[url_rule]['valid']:
                        # valid
                        s({'id': valid_key})
                    for invalid_key in valid_urls[url_rule]['invalid']:
                        try:
                            # invalid
                            s({'id': invalid_key})
                            raise Exception('normally you can\'t get there')
                        except Error:
                            continue

        # test for invalid url rules
        for url in invalid_urls:
            try:
                parser = UrlParser(url)
                if len(parser.url_attributes) > 0:
                    raise Exception('normally you can\'t get there')
            except AttributeError:
                continue
