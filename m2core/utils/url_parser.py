import re
from voluptuous import Schema, Required, Coerce, Boolean, Length, All, Range, In
from voluptuous.error import Error
from m2core.utils.voluptuous_checkers import NotNone


class UrlParserAttr:
    ATTR_TYPES = {
        'int': int,
        'float': float,
        'string': str,
        'bool': bool
    }

    def __init__(self, attr_name: str, attr_type: str, type_params: str):
        """
        Constructor
        :param attr_name: 
        :param attr_type: 
        :param type_params: 
        """
        self._attr_name = attr_name
        self._attr_type = attr_type
        self._type_params = type_params
        # (_len_limit, _second_param)
        # _len_limit is always int
        # _second_param may be int, dict(min=, max=), list(val1, val2, val3)
        self._len_limit = None
        self._second_param = None

        # specify only attribute name
        if attr_name and not attr_type and not type_params:
            self._parse_name()
        # specify attribute name with it's type
        elif attr_name and attr_type and attr_type in UrlParserAttr.ATTR_TYPES.keys() and not type_params:
            self._parse_name_type()
        # specify attribute name, it's type and params
        elif attr_name and attr_type and attr_type in UrlParserAttr.ATTR_TYPES.keys() and type_params:
            self._parse_name_type_params()
        else:
            raise AttributeError('Wrong-formed url attribute rules with %s:%s[%s]' %
                                 (self._attr_name, self._attr_type, self._type_params))

    def _parse_name(self):
        self._attr_type = 'string'

    def _parse_name_type(self):
        pass

    def _parse_name_type_params(self):
        # if bool - raise exception, there is no params for bool
        if self._type_params and self._attr_type == 'bool':
            raise AttributeError('You can\'t use any params with [bool] type')

        # if 1 numeric param has been passed
        m = re.match(r'^(\d+)$', self._type_params)
        if m:
            self._len_limit = int(m.group(1))
            return

        # if 2 numeric params have been passed
        m = re.match(r'^(\d+),(\d+)$', self._type_params)
        if m:
            # if int - raise exception, int doesn't have second param
            if self._type_params and self._attr_type == 'int':
                raise AttributeError('You can\'t use second param with [int] type')
            self._len_limit = int(m.group(1))
            self._second_param = m.group(2)
            return

        # if 1 numeric and interval params have been passed
        m = re.match(r'^(\d+),\[(\d+)-(\d+)\]$', self._type_params)
        if m:
            # if str - raise exception, str doesn't have interval param
            if self._type_params and self._attr_type == 'str':
                raise AttributeError('You can\'t use interval with [str] type')
            self._len_limit = int(m.group(1))
            self._second_param = dict(min=int(m.group(2)), max=int(m.group(3)))
            return

        # if list of permitted values has been passed
        m = re.match(r'^(\d+),\[([^\]]+)\]$', self._type_params)
        if m:
            self._len_limit = int(m.group(1))
            # split interval value by `;` symbol
            splitted = m.group(2).split(';')
            if self._attr_type == 'int':
                self._second_param = [int(x) for x in splitted]
            elif self._attr_type == 'float':
                self._second_param = [float(x) for x in splitted]
            else:
                self._second_param = splitted
            return

    def validator(self):
        """
        Generates validator for `voluptuous` module for current attribute
        """
        # {Optional('id'): All(Coerce(int)),}
        if self._attr_type == 'bool':
            return self._bool_validator()

        if self._attr_type == 'int':
            return self._int_validator()

        if self._attr_type == 'float':
            return self._float_validator()

        if self._attr_type == 'string':
            return self._string_validator()

    def replacement(self):
        """
        Generates replacement to make final url path for Tornado
        """
        if self._attr_type == 'bool':
            return r'(?P<%s>[01])' % self._attr_name

        if self._attr_type == 'int':
            return r'(?P<%s>[0-9]+)' % self._attr_name

        if self._attr_type == 'float':
            return r'(?P<%s>[0-9,.]+)' % self._attr_name

        if self._attr_type == 'string':
            # take my excuses for concatenation - it's because of the `%` symbol
            return r'(?P<' + self._attr_name + '>[^/_+?#$%]+)'

    def params(self):
        """
        dict() with parsed attribute params
        """
        return {
            # 'attribute_name': self._attr_name,
            'attribute_type': self._attr_type,
            'length_limit': self._len_limit,
            'second_params': self._second_param,
        }

    def name(self):
        """
        Attribute name
        """
        return self._attr_name

    def _bool_validator(self):
        return {Required(self._attr_name): All(NotNone(msg='<%s> should be not None' % self._attr_name), Boolean())}

    def _int_validator(self):
        # /users/:{id:int}
        if not self._len_limit and not self._second_param:
            return {Required(self._attr_name): All(NotNone(msg='<%s> should be not None' % self._attr_name),
                                                   Coerce(int, msg='<%s> should be of [int] type' % self._attr_name))}

        # /users/:{id:int(2)}
        if self._len_limit and not self._second_param:
            return {Required(self._attr_name): All(Coerce(int, msg='<%s> should be of [int] type' % self._attr_name),
                                                   NotNone(msg='<%s> should be not None' % self._attr_name),
                                                   Range(
                                                       min=0,
                                                       max=pow(10, self._len_limit) - 1,
                                                       msg='<%s> length should be in [0-%s] range' %
                                                           (self._attr_name, self._len_limit))
                                                   )}

        # /users/:{id:int(2,5)}
        if self._len_limit and self._second_param and type(self._second_param) == int:
            return {Required(self._attr_name): All(Coerce(int, msg='<%s> should be of [int] type' % self._attr_name),
                                                   NotNone(msg='<%s> should be not None' % self._attr_name),
                                                   Range(
                                                       min=pow(10, self._len_limit - 1) if self._len_limit else 0,
                                                       max=pow(10, self._len_limit) - 1,
                                                       msg='<%s> length should be in [%s-%s] range' %
                                                           (self._attr_name, self._len_limit, self._second_param))
                                                   )}

        # /users/:{id:int(4,[5-150])}
        if self._second_param and type(self._second_param) == dict:
            return {Required(self._attr_name): All(Coerce(int, msg='<%s> should be of [int] type' % self._attr_name),
                                                   NotNone(msg='<%s> should be not None' % self._attr_name),
                                                   Range(
                                                       min=pow(10, self._len_limit - 1) if self._len_limit else 0,
                                                       max=pow(10, self._len_limit) - 1 if self._len_limit else None,
                                                       msg='<%s> length should be %s length' %
                                                           (self._attr_name, self._len_limit)),
                                                   Range(
                                                       min=self._second_param['min'],
                                                       max=self._second_param['max'],
                                                       msg='<%s> values should be in [%s-%s] range' %
                                                           (self._attr_name, self._second_param['min'],
                                                            self._second_param['max'])
                                                   )
                                                   )}

        # /users/:{id:int(0,[5;15;150;500])}
        if self._second_param and type(self._second_param) == list:
            return {Required(self._attr_name): All(Coerce(int, msg='<%s> should be of [int] type' % self._attr_name),
                                                   NotNone(msg='<%s> should be not None' % self._attr_name),
                                                   Range(
                                                       min=pow(10, self._len_limit - 1) if self._len_limit else 0,
                                                       max=self._len_limit if self._len_limit > 0 else None,
                                                       msg='<%s> length should be %s length' %
                                                           (self._attr_name, self._len_limit)),
                                                   In(
                                                       self._second_param,
                                                       msg='<%s> value should be in %s' %
                                                           (self._attr_name, self._second_param))
                                                   )}

    def _float_validator(self):
        # /users/:{id:float}
        if not self._len_limit and not self._second_param:
            return {Required(self._attr_name): All(NotNone(msg='<%s> should be not None' % self._attr_name),
                                                   Coerce(float,
                                                          msg='<%s> should be of [float] type' % self._attr_name))}

        # /users/:{id:float(2)}
        if self._len_limit and not self._second_param:
            return {
                Required(self._attr_name): All(Coerce(float, msg='<%s> should be of [float] type' % self._attr_name),
                                               NotNone(msg='<%s> should be not None' % self._attr_name),
                                               Range(
                                                   min=0,
                                                   max=pow(10, self._len_limit) - 1,
                                                   msg='<%s> length of integer part should be in [0-%s] range' %
                                                       (self._attr_name, self._len_limit))
                                               )}

        # /users/:{id:float(2,5)}
        if self._len_limit and self._second_param and type(self._second_param) == float:
            return {
                Required(self._attr_name): All(Coerce(float, msg='<%s> should be of [float] type' % self._attr_name),
                                               NotNone(msg='<%s> should be not None' % self._attr_name),
                                               Range(
                                                   min=pow(10, self._len_limit - 1) if self._len_limit else 0,
                                                   max=pow(10, self._len_limit) - 1,
                                                   msg='<%s> length of integer part should be in [%s-%s] range' %
                                                       (self._attr_name, self._len_limit, self._second_param))
                                               )}

        # /users/:{id:float(4,[5-150])}
        if self._second_param and type(self._second_param) == dict:
            return {
                Required(self._attr_name): All(Coerce(float, msg='<%s> should be of [float] type' % self._attr_name),
                                               NotNone(msg='<%s> should be not None' % self._attr_name),
                                               Range(
                                                   min=pow(10, self._len_limit - 1) if self._len_limit else 0,
                                                   max=pow(10, self._len_limit) - 1 if self._len_limit else None,
                                                   msg='<%s> length of integer part should be %s length' %
                                                       (self._attr_name, self._len_limit)),
                                               Range(
                                                   min=self._second_param['min'],
                                                   max=self._second_param['max'],
                                                   msg='<%s> values should be in [%s-%s] range' %
                                                       (self._attr_name, self._second_param['min'],
                                                        self._second_param['max'])
                                               )
                                               )}

        # /users/:{id:float(0,[5;15;150;500])}
        if self._second_param and type(self._second_param) == list:
            return {
                Required(self._attr_name): All(Coerce(float, msg='<%s> should be of [float] type' % self._attr_name),
                                               NotNone(msg='<%s> should be not None' % self._attr_name),
                                               Range(
                                                   min=pow(10, self._len_limit - 1) if self._len_limit else 0,
                                                   max=self._len_limit if self._len_limit > 0 else None,
                                                   msg='<%s> length of integer part should be %s length' %
                                                       (self._attr_name, self._len_limit)),
                                               In(
                                                   self._second_param,
                                                   msg='<%s> value should be in %s' %
                                                       (self._attr_name, self._second_param))
                                               )}

    def _string_validator(self):
        # '/users/:{id:string}'
        if not self._len_limit and not self._second_param:
            return {Required(self._attr_name): All(
                NotNone(msg='<%s> should be not None' % self._attr_name),
                Coerce(str, msg='<%s> should be of [str] type' % self._attr_name))}

        # '/users/:{id:string(3)}',
        if self._len_limit and not self._second_param:
            return {Required(self._attr_name): All(
                NotNone(msg='<%s> should be not None' % self._attr_name),
                Coerce(str, msg='<%s> should be of [str] type' % self._attr_name),
                Length(
                    min=0,
                    max=self._len_limit if self._len_limit > 0 else None,
                    msg='<%s> length should be %s length' % (self._attr_name, self._len_limit)))}

        # '/users/:{id:string(0,[string1;string2;string3])}',
        if self._second_param:
            return {Required(self._attr_name): All(
                NotNone(msg='<%s> should be not None' % self._attr_name),
                Coerce(str, msg='<%s> should be of [str] type' % self._attr_name),
                Length(
                    min=0,
                    max=self._len_limit if self._len_limit > 0 else None,
                    msg='<%s> length should be %s length' % (self._attr_name, self._len_limit)
                ),
                In(
                    self._second_param,
                    msg='<%s> value should be in %s' % (self._attr_name, self._second_param)))}

    def __repr__(self):
        return 'attr_name: %s[%s], length_limit: %s, type_attr: %s' % \
               (self._attr_name, self._attr_type, self._len_limit, self._second_param)


class UrlParser:
    """
    Great class for making url masks, generating validators for url parameters, url attribute descriptions.
    Here are examples of different url masks which you can comfortably use:

    /users/:{id} -> :id - attribute, any type
    /users/:{id:int} -> :id - int attribute, any length
    /users/:{id:int(2)} -> :id - int attribute, length is 2 numbers
    /users/:{id:float} -> :id - float attribute
    /users/:{id:float(3)} -> :id - float attribute, length is 3 numbers including `,`
    /users/:{id:float(2,5)} -> :id - float attribute, length is between 2 and 5 numbers including `,`
    /users/:{id:string} -> :id - string, any length, without `/` symbol
    /users/:{id:string(2)} -> :id - string,  length is 2 symbols, without `/` symbol
    /users/:{id:bool} -> :id - bool flag, accepts only `0` or `1`
    /users/:{id:int(0,[0-100])} -> :id - int, any length (0), but value must be between `0` and `100`
    /users/:{id:float(0,[0-100])} -> :id - float, any length (0), but value must be between `0` and `100`
    /users/:{id:string(0,[string1;string2;string3])} -> :id - string, any length (0), but value must be in list
                                        of values: ('string1', 'string2', 'string3')
    """

    def __init__(self, url: str):
        self.original_url = url
        self.url_attributes = []
        self._full_match = ''
        self.__parse()

    def __parse(self):
        # check for `:{}`
        m = re.finditer(r':{(?P<attr_name>\w+)(?:(?::(?P<attr_type>|int|float|string|bool))'
                        r'(?:\((?P<type_params>[^)]+)\))?)?}', self.original_url)
        for match in m:
            attr = UrlParserAttr(match.group('attr_name'), match.group('attr_type'), match.group('type_params'))
            self.url_attributes.append({'instance': attr, 'full_match': match.group(0)})

    def tornado_url(self):
        result = self.original_url
        for attr in self.url_attributes:
            result = result.replace(attr['full_match'], attr['instance'].replacement(), 1)
        return result

    def params(self):
        result = dict()
        for param in self.url_attributes:
            result[param['instance'].name()] = param['instance'].params()
        return result

    def validator_schema(self):
        result = dict()
        for attr in self.url_attributes:
            result.update(attr['instance'].validator())
        return Schema(result)

    def __repr__(self):
        return self.original_url


# This is kind of unittest. Just run this script and you'll see validator in action
if __name__ == "__main__":
    def try_parser():
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
        print('\n\ntest for valid and invalid params validators')
        for url_rule in valid_urls.keys():
            parser = UrlParser(url_rule)
            print('url rule: %s' % url_rule)
            print('tornado url: %s' % parser.tornado_url())
            for attr in parser.url_attributes:
                validator = attr['instance'].validator()
                if validator:
                    s = Schema(validator)
                    for valid_key in valid_urls[url_rule]['valid']:
                        print('valid: %s' % valid_key)
                        s({'id': valid_key})
                    for invalid_key in valid_urls[url_rule]['invalid']:
                        try:
                            print('invalid: %s' % invalid_key)
                            s({'id': invalid_key})
                            raise Exception('normally you can\'t get there')
                        except Error:
                            continue

        print('\n\ntest for invalid url rules')
        for url in invalid_urls:
            try:
                parser = UrlParser(url)
                if len(parser.url_attributes) > 0:
                    raise Exception('normally you can\'t get there')
            except AttributeError:
                continue

    try_parser()
