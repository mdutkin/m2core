from m2core.db.sqlalchemy_mixins import DecoMixin
from m2core.db.sqlalchemy_mixins import DataMixin
from sqlalchemy.ext.declarative import declarative_base

MetaBase = declarative_base()


class EnchantedMixin(DataMixin, DecoMixin):
    """
    Mixin together
    """
    __abstract__ = True

    __repr__ = DecoMixin.__repr__


class BaseModel(MetaBase, EnchantedMixin):
    """
    Use this BaseModel class 
    """
    pass
