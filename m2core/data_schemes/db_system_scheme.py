from sqlalchemy import Column, BigInteger, String, Boolean, Integer, ForeignKey, UniqueConstraint, DateTime, text
from sqlalchemy.exc import SQLAlchemyError
from m2core.bases.base_model import BaseModel
from m2core.utils.error import M2Error
from typing import List


class CreatedMixin(object):
    created = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    updated = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
CreatedMixin.created._creation_order = 9998
CreatedMixin.updated._creation_order = 9999


class SortMixin(object):
    sort_order = Column(BigInteger, default=0, server_default='0', nullable=False)
SortMixin.sort_order._creation_order = 9997


class M2Permissions(BaseModel):
    __repr_list__ = ['id', 'name']

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    system_name = Column(String(255), unique=True)
    description = Column(String(500))
    active = Column(Boolean, default=True, server_default='1')
    created = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)


class M2Roles(BaseModel):
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(500))
    active = Column(Boolean, default=True, server_default='1')

    def get_role_permissions(self) -> List[str]:
        """
        Returns permissions list for current role
        :return: permissions list
        """
        permissions = M2Permissions.q. \
            join(M2RolePermissions). \
            filter(M2RolePermissions.role_id == self.get('id'))
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
            self.s.query(M2RolePermissions).filter(M2RolePermissions.role_id==self.get('id')).delete()
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
        permission = M2Permissions.load_by_params(system_name=permission_system_name)
        if not permission:
            raise M2Error('Trying to add non-existent permission', True)

        M2RolePermissions.load_or_create(role_id=self.get('id'), permission_id=permission.get('id'))


class M2RolePermissions(BaseModel):
    id = Column(BigInteger, primary_key=True)
    role_id = Column(BigInteger, ForeignKey(M2Roles.__table__.c.id, ondelete="CASCADE"), nullable=False)
    permission_id = Column(BigInteger, ForeignKey(M2Permissions.__table__.c.id, ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint('role_id', 'permission_id', name='_m2core_permission_per_role_uq'), )


class M2UserRoles(BaseModel):
    id = Column(BigInteger, primary_key=True)
    # not possible to specify ForeignKey for user_id, because no one knows what table it would be linked
    user_id = Column(BigInteger, nullable=False)
    role_id = Column(BigInteger, ForeignKey(M2Roles.__table__.c.id), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'role_id', name='_m2core_role_per_user_uq'),)
