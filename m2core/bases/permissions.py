__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import re


class BasePermissionRule(list):
    def __new__(cls, *args, **kwargs):
        return super(BasePermissionRule, cls).__new__(cls, args)

    def __init__(self, *args):
        super(BasePermissionRule, self).__init__(args)

    def __call__(self, user_permissions):
        raise NotImplemented('You have to implement `__call__` method for your rule class')

    def __repr__(self):
        return self.__class__.__name__ + '(' + ', '.join([repr(_) for _ in self]) + ')'


class Or(BasePermissionRule):
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
    def __call__(self, user_permissions):
        if isinstance(self[0], BasePermissionRule):
            return not self[0](user_permissions)
        elif isinstance(self[0], Permission):
            return self[0] not in user_permissions
        else:
            raise TypeError('For checking permissions you should use instances of `BasePermissionRule` or '
                            '`Permissions`')


class Permission:
    def __init__(self, name: str=None, sys_name: str=None):
        if name is None or not len(name):
            raise AttributeError('`name` param should not be `None` or it\'s length should be > 0')
        self._name = name
        self._sys_name = sys_name
        self.rule_chain = None

    @property
    def sys_name(self):
        return self._sys_name or re.sub(r'\W', '_', self._name).upper()

    @property
    def name(self):
        return self._name

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
        return self.rule_chain(user_permissions)

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.sys_name}>'
