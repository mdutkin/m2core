__author__ = 'Maxim Dutkin (max@dutkin.ru)'


from enum import IntEnum


class M2CoreIntEnum(IntEnum):
    @classmethod
    def get(cls, member_value: int or str):
        """
        Returns enum member from `int` ID. If no member found - returns `None`

        :param member_value:

        :return: enum member or `None`
        """
        if type(member_value) is int:
            try:
                return cls(member_value)
            except ValueError:
                return None
        elif type(member_value) is str:
            for m in cls.all():
                if m.name == member_value:
                    return m
            return None
        else:
            raise AttributeError('You can load enum members only by `str` name or `int` value')

    @classmethod
    def all(cls):
        return [_ for _ in cls]
