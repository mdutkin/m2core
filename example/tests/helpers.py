__author__ = 'Maxim Dutkin (max@dutkin.ru)'


class UserRightsFactory:
    admin_permissions = ['admin', 'authenticated', ]
    authenticated_permissions = ['authenticated', ]

    def __init__(self):
        self.default_obj = {
                'id': 1,
                'access_token': 'generated_access_token',
                'permissions': []
            }

    @classmethod
    def admin(cls):
        _ = cls()
        _.default_obj.update(permissions=cls.admin_permissions)
        return _.default_obj

    @classmethod
    def guest(cls):
        return None

    @classmethod
    def authenticated(cls):
        _ = cls()
        _.default_obj.update(permissions=cls.authenticated_permissions)
        return _.default_obj
