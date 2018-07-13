from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from m2core.bases.base_model import BaseModel
from m2core.common.permissions import Permission, PermissionsEnum
from m2core.utils.error import M2Error
from typing import List


class CreatedMixin:
    """
    Stored in UTC without any offset and timezone
    """
    created = Column(DateTime(timezone=False), default=func.now(), server_default=text('now()'), nullable=False)
    updated = Column(DateTime(timezone=False), default=func.now(), server_default=text('now()'),
                     onupdate=datetime.utcnow, nullable=False)


CreatedMixin.created._creation_order = 9998
CreatedMixin.updated._creation_order = 9999


class SortMixin:
    sort_order = Column(BigInteger, default=0, server_default='0', nullable=False)


SortMixin.sort_order._creation_order = 9997


class M2PermissionCheckMixin:
    def can(self, permission_rule: Permission) -> bool:
        return permission_rule(self.permissions)


class M2Permission(BaseModel):
    __repr_list__ = ['id', 'system_name']

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    system_name = Column(String(255), unique=True)
    description = Column(String(500))
    active = Column(Boolean, default=True, server_default='1')
    created = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    @property
    def enum_member(self):
        if not hasattr(self, '__enum_member'):
            all_perms = PermissionsEnum.all_platform_instances
            sys_name = self.system_name
            for p in all_perms:
                if p.sys_name == sys_name:
                    setattr(self, '__enum_member', p)
                    return p
            raise M2Error(f'No corresponding enum member found for Permission with sys_name=`{sys_name}`')
        else:
            return getattr(self, '__enum_member')

    @classmethod
    def from_enum_member(cls, member: Permission):
        entity = cls.s.query(M2RolePermission).filter(M2Permission.system_name == member.sys_name).first()
        if not entity:
            raise M2Error(f'No corresponding permission found for Permission with sys_name=`{member.sys_name}`')

        return entity


class M2Role(BaseModel):
    __repr_list__ = ['id', 'name']

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(500))
    active = Column(Boolean, default=True, server_default='1')

    def get_role_permissions(self) -> List[str]:
        """
        Returns permissions list for current role
        :return: permissions list
        """
        permissions = M2Permission.q. \
            join(M2RolePermission). \
            filter(M2RolePermission.role_id == self.get('id'))
        permissions = permissions.all()
        return [x.get('system_name') for x in permissions]

    def dump_role_permissions(self):
        """
        Dumps all role permissions to Redis
        """
        permissions_list = self.get_role_permissions()
        self.sh.dump_role_permissions(self.get('id'), permissions_list)

    def set_permissions(self, permissions: list):
        """
        Replaces all existing permissions with new list and dumps it to Redis
        :param permissions: list of system_name's
        """
        try:
            # get all existing and delete them
            self.s.query(M2RolePermission).filter(M2RolePermission.role_id == self.get('id')).delete()
            self.s.commit()
            # add new
            for p in permissions:
                self.add_permission(p)
            # dump to db
            self.dump_role_permissions()
        except SQLAlchemyError:
            self.s.rollback()
            raise

    def add_permission(self, permission_system_name: str):
        """
        Adds existing permission to current role. You can not create new permission, because they are added
        during M2Core initialization. Do not forget to dump it in Redis!
        """
        permission = M2Permission.load_by_params(system_name=permission_system_name)
        if not permission:
            raise M2Error('Trying to add non-existent permission', True)

        M2RolePermission.load_or_create(role_id=self.get('id'), permission_id=permission.get('id'))


class M2RolePermission(BaseModel):
    id = Column(BigInteger, primary_key=True)
    role_id = Column(BigInteger, ForeignKey(M2Role.__table__.c.id, ondelete="CASCADE"), nullable=False)
    permission_id = Column(BigInteger, ForeignKey(M2Permission.__table__.c.id, ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint('role_id', 'permission_id', name='_m2core_permission_per_role_uq'),)


class M2UserMixin:
    """
    Use this mixin in your User's class:

        class User(M2UserMixin, CreatedMixin, BaseModel):
            email = Column(String(255), nullable=False, unique=False)

    your class must be named `User` or it's `__tablename__` attribute must be equals to `User`
    """
    id = Column(BigInteger, primary_key=True)


class M2UserRole(BaseModel):
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('User.id'), nullable=False)
    role_id = Column(BigInteger, ForeignKey(M2Role.__table__.c.id), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'role_id', name='_m2core_role_per_user_uq'),)
