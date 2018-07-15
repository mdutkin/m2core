__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import re
from m2core.utils.decorators import classproperty


class BasePermissionRule(list):
    operator_char = ''

    def __new__(cls, *args, **kwargs):
        return super(BasePermissionRule, cls).__new__(cls, args)

    def __init__(self, *args):
        super(BasePermissionRule, self).__init__(args)

    def __call__(self, user_permissions):
        raise NotImplemented('You have to implement `__call__` method for your rule class')

    def __repr__(self):
        return f' {self.operator_char} '.join([repr(_) for _ in self])


class Or(BasePermissionRule):
    operator_char = '|'

    def __call__(self, user_permissions):
        for rule in self:
            if isinstance(rule, BasePermissionRule):
                result = rule(user_permissions)
            elif isinstance(rule, Permission):
                result = rule in user_permissions
            else:
                raise TypeError('For checking permissions you should use instances of `BasePermissionRule` or '
                                '`Permissions`')
            if result:
                return True

        return False


class And(BasePermissionRule):
    """
    All results inside it's members should be True, otherwise this rule returns False when called
    """
    operator_char = '&'

    def __call__(self, user_permissions):
        for rule in self:
            if isinstance(rule, BasePermissionRule):
                result = rule(user_permissions)
            elif isinstance(rule, Permission):
                result = rule in user_permissions
            else:
                raise TypeError('For checking permissions you should use instances of `BasePermissionRule` or '
                                '`Permissions`')
            if not result:
                return False

        return True


class Not(BasePermissionRule):
    """
    This rule means that we must not meet this permission in `user_permissions`, always consists of only one element
    """
    operator_char = '!'

    def __call__(self, user_permissions):
        if isinstance(self[0], BasePermissionRule):
            return not self[0](user_permissions)
        elif isinstance(self[0], Permission):
            return self[0] not in user_permissions
        else:
            raise TypeError('For checking permissions you should use instances of `BasePermissionRule` or '
                            '`Permissions`')


class Permission:
    def __init__(self, name: str=None, sys_name: str=None, description: str=None):
        if name is None or not len(name):
            raise AttributeError('`name` param should not be `None` or it\'s length should be > 0')
        self._name = name
        self._sys_name = sys_name
        self._description = description
        self.rule_chain = None

    @property
    def sys_name(self):
        return self._sys_name or re.sub(r'\W', '_', self._name).upper()

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    def copy(self):
        return Permission(name=self._name, sys_name=self._sys_name)

    def __check_type(self, _type):
        return self.rule_chain is not None and type(self.rule_chain) is _type

    def __do_magic(self, other: 'Permission', _m_class: type(BasePermissionRule)):
        l_side = self.rule_chain
        r_side = other.rule_chain
        result_perm = other.copy()
        if l_side and r_side:
            # we get there only after both sides have been evaluated and compiler met distinct operator
            if type(l_side) is _m_class:
                l_side.append(r_side)
                result_perm.rule_chain = l_side
            else:
                result_perm.rule_chain = _m_class(l_side, r_side)
        elif l_side:
            if type(l_side) is _m_class:
                l_side.append(other)
                result_perm.rule_chain = l_side
            else:
                result_perm.rule_chain = _m_class(l_side, other)
        elif r_side:
            result_perm.rule_chain = _m_class(self, r_side)
        else:
            result_perm.rule_chain = _m_class(self, other)

        return result_perm

    def __and__(self, other):
        _m_class = And
        return self.__do_magic(other, _m_class)

    def __or__(self, other):
        _m_class = Or
        return self.__do_magic(other, _m_class)

    def __invert__(self):
        result_perm = self.copy()
        result_perm.rule_chain = Not(self.rule_chain or self)
        return result_perm

    def __call__(self, user_permissions):
        if self.rule_chain is None:
            return self in user_permissions
        else:
            return self.rule_chain(user_permissions)

    def __repr__(self):
        if self.rule_chain:
            return self.rule_chain.__repr__()
        else:
            return f'<{self.__class__.__name__}.{self.sys_name}>'


class PermissionsEnumMeta(type):
    """Metaclass for PermissionsEnum"""

    def __init__(cls, name, bases, nmspc):
        super(PermissionsEnumMeta, cls).__init__(name, bases, nmspc)
        if not hasattr(cls, 'registry'):
            cls.registry = set()
        cls.registry.add(cls)
        cls.registry -= set(bases)  # Remove base classes

    def __str__(cls):
        if cls in cls.registry:
            return cls.__name__
        return cls.__name__ + ": " + ", ".join([sc.__name__ for sc in cls])


class PermissionsEnum(metaclass=PermissionsEnumMeta):
    AUTHORIZED = Permission('authorized')

    @classproperty
    def ALL(cls):
        cache_var_name = '__all_cache'
        cached_perms = getattr(cls, cache_var_name, None)
        if cached_perms is None:
            setattr(cls, cache_var_name, set())
            cached_perms = getattr(cls, cache_var_name)
            for attr_name in dir(cls):
                if not attr_name.startswith('_') and attr_name != 'ALL':
                    attr = getattr(cls, attr_name)
                    if type(attr) is Permission:
                        cached_perms.add(attr)
        return cached_perms

    @classproperty
    def SKIP(cls):
        return lambda p: True

    @classproperty
    def all_platform_permissions(cls):
        sub_classes = PermissionsEnum.registry
        all_perms = set()
        for c in sub_classes:
            all_perms |= c.ALL

        return all_perms

