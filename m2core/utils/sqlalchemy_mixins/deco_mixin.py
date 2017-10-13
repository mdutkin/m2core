from sqlalchemy.ext.declarative import declared_attr
from m2core.utils.data_helper import DataHelper


class DecoMixin:
    __abstract__ = True

    __repr_list__ = set()

    @declared_attr
    def __tablename__(cls):
        return DataHelper.camel_to_underline(cls.__name__)

    def __repr__(self):
        columns = self.__table__.c
        repr_list = list()
        if self.__repr_list__:
            for key in self.__repr_list__:
                repr_list.append('%s: %s' % (key, getattr(self, key, None)))
        else:
            for key in columns.keys():
                repr_list.append('%s: %s' % (key, getattr(self, key, None)))
        return '<%s (%s)>' % (self.__class__.__name__, ', '.join(repr_list))
