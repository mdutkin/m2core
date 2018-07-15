__author__ = 'Maxim Dutkin (max@dutkin.ru)'


from enum import IntEnum
from sqlalchemy.types import TypeDecorator, Integer


class IntEnumType(TypeDecorator):
    """
    SQLAlchemy enum column type. Makes simple mapping between `IntEnum` structures and SQLAlchemy columns.
    When enum member is specified - saves it to DB as `int`, when loads from DB - finds corresponding enum
    member.

    Here's usage example:

        class UserStatusEnum(M2CoreIntEnum):
            ONLINE = 1
            OFFLINE = 2


        class User(BaseModel):
            id = Column(BigInteger, primary_key=True)
            status = Column(IntEnumType(UserStatusEnum))


        user = User.load_by_pk(1)
        print(user.status)  # outputs <UserStatusEnum.ONLINE: 1>
        user.status = UserStatusEnum.OFFLINE
        # or like that:
        # user.status = 2
        user.save()

    """
    impl = Integer

    def __init__(self, enum_struct):
        self.__enum_struct = enum_struct
        super().__init__()

    def process_bind_param(self, value, dialect):
        if isinstance(value, IntEnum):
            return int(value)

        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        return self.__enum_struct.get_by_int(value)
