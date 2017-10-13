from redis import StrictRedis
from sqlalchemy.orm import Session, scoped_session, Query
from m2core.utils.sqlalchemy_mixins.decorators import classproperty
from m2core.utils.error import M2Error
from m2core.utils.session_helper import SessionHelper


class SessionMixin:
    __abstract__ = True

    @classmethod
    def set_db_session(cls, session) -> scoped_session or Session:
        """
        Sets DB Session during M2Core initialization with this method
        """
        cls._db_session = session

    @classproperty
    def s(cls) -> scoped_session or Session:
        """
        Returns DB Session
        """
        if cls._db_session:
            return cls._db_session
        else:
            raise M2Error('No DB session defined')

    @classmethod
    def set_redis_session(cls, session) -> scoped_session or Session:
        """
        Sets Redis Session during M2Core initialization with this method
        """
        cls._redis_session = session

    @classproperty
    def r(cls) -> StrictRedis:
        """
        Returns Redis Session
        """
        if cls._redis_session:
            return cls._redis_session
        else:
            raise M2Error('No Redis session defined')

    @classproperty
    def sh(cls):
        """
        Returns instance of Session Helper
        :return: 
        """
        if not cls.r:
            raise M2Error('No Redis session defined')
        return SessionHelper(cls.r['connector'], cls.r['scheme'])

    @classproperty
    def q(cls) -> Query:
        """
        Returns prepared Query taken from DB Session
        """
        if not cls.s:
            raise M2Error('No DB session defined')
        return cls.s.query(cls)
