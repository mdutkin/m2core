import random
import string
import re


class DataHelper:
    @staticmethod
    def random_char(length: int) -> str:
        """
        Generates random char sequence with the given length
        """
        return ''.join(random.choice(string.ascii_letters) for x in range(length))

    @staticmethod
    def random_hex_str(length: int) -> str:
        """
        Generates random alpha-numeric sequence, where all chars are from hex set (a-f)
        :param length:
        :return:
        """
        return '%x' % random.randrange(16 ** length)

    @staticmethod
    def camel_to_underline(camel) -> str:
        """
        Converts camelcased-string to underlined string, example:
                ConvertMeToUnderline -> convert_me_to_underline
        :param camel: string to convert
        :return: converted string
        """
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
