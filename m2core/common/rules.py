__author__ = 'Maxim Dutkin (max@dutkin.ru)'


from collections import defaultdict
from tornado.web import RequestHandler
from typing import Type
from m2core.common.permissions import PermissionsEnum
from m2core.utils.url_parser import UrlParser


class Rules(defaultdict):
    def validator(self, human_route: str=None):
        return self[human_route]['validator']

    def docs(self, human_route: str=None, method: str=None):
        return self[human_route]['docs'].get(method.upper())

    def permissions(self, human_route: str=None, method: str=None):
        return self[human_route]['permissions'].get(method.upper())

    def group(self, human_route: str=None):
        return self[human_route]['group']

    def add_meta(self, human_route, handler_cls: Type[RequestHandler], rule_group: str, method_permissions: dict) \
            -> UrlParser:
        # add documentation per each method in SUPPORTED_METHODS
        for method in handler_cls.__dict__:
            method_upper = method.upper()
            if method_upper in handler_cls.SUPPORTED_METHODS:
                self[human_route]['docs'][method_upper] = handler_cls.__dict__[method].__doc__
                # also add permissions per each method. default - skip check
                permissions = PermissionsEnum.skip
                for m, p in method_permissions.items():
                    if m.upper() == method_upper:
                        permissions = p
                        break
                self[human_route]['permissions'][method_upper] = permissions
        self[human_route]['group'] = rule_group
        url_parser = UrlParser(human_route)
        self[human_route]['validator'] = url_parser

        return url_parser
