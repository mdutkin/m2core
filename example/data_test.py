import pprint
from m2core import M2Core
from m2core.data_schemes.db_system_scheme import BaseModel
from m2core.bases.base_model import MetaBase
from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship, backref


# small test for BaseModel->data() method, just to remember what it can do )
# this ugly sqlalchemy declaration models are made specially for test


class Portal(BaseModel):
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))
    description = Column(String(255))

    users = relationship(
        'PortalUser',
        backref=backref('portal')
    )

    settings = relationship(
        'PortalSettingEntity',
        backref=backref('portal')
    )


class PortalUser(BaseModel):
    id = Column(BigInteger, primary_key=True)
    portal_id = Column(BigInteger, ForeignKey('portal.id'))
    name = Column(String(255))

    settings = relationship(
        'UserSetting',
    )


class PortalSettingEntity(BaseModel):
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    value = Column(String(255))
    portal_id = Column(BigInteger, ForeignKey('portal.id'))

    settings = relationship(
        'UserSetting',
    )


class UserSetting(BaseModel):
    id = Column(BigInteger, primary_key=True)
    setting_id = Column(BigInteger, ForeignKey('portal_setting_entity.id'))
    user_id = Column(BigInteger, ForeignKey('portal_user.id'))

    setting_entity = relationship(
        'PortalUser',
    )

    user = relationship(
        'PortalUser',
    )


m2core = M2Core()
MetaBase.metadata.drop_all(m2core.db_engine)
MetaBase.metadata.create_all(m2core.db_engine)

portal_data = {
    'title': 'My portal title',
    'description': 'Desperado portal'
}
portal = Portal.load_or_create(**portal_data)
for i in range(1, 10):
    user = PortalUser.load_or_create(
        portal_id=portal.get('id'),
        name='My Boy %s' % i
    )
    setting = PortalSettingEntity.load_or_create(
        name='Setting %s' % i,
        value='%s' % i,
        portal_id=portal.get('id')
    )
    user_setting = UserSetting.load_or_create(
        setting_id=setting.get('id'),
        user_id=user.get('id')
    )

pp = pprint.PrettyPrinter(indent=2)
stuff = portal.data(
    'id',
    'description',
    'users',
    'title',
    'settings>name',
    'settings>portal_id',
    'settings>value',
    'settings>settings>id',
    max_level=3
)
pp.pprint(stuff)
