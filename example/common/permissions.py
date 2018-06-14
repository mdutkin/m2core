__author__ = 'Maxim Dutkin (max@dutkin.ru)'


from m2core.common import Permission, BasePermissionRule, And, Or, Not, PermissionsEnum


class PlatformPermissions(PermissionsEnum):
    AUTHORIZED = Permission(
        name='AUTHORIZED',
        sys_name='authorized',
        description='All authorized users will have this permission by default (overwrites default `AUTHORIZED` '
                    'permission)'
    )
    VIEW_SOME_INFO = Permission(
        name='VIEW_SOME_INFO',
        sys_name='view_some_info',
        description='Example of some view permissions'
    )
    EDIT_SOME_INFO = Permission(
        name='EDIT_SOME_INFO',
        sys_name='edit_some_info',
        description='Example of some edit permissions'
    )
    DELETE_SOME_INFO = Permission(
        name='DELETE_SOME_INFO',
        sys_name='delete_some_info',
        description='Example of some delete permissions'
    )