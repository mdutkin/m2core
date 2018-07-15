__author__ = 'Maxim Dutkin (max@dutkin.ru)'


from os import environ
from tornado.options import OptionParser


class M2OptionParser(OptionParser):
    def parse_environment(self, final=True):
        """
        Searches for option names in environment variables list. Assuming that all environment variable names
        are always in upper case, iterates through already defined options and searches their names in upper
        case in environment

        If ``final`` is ``False``, parse callbacks will not be run.
        This is useful for applications that wish to combine configurations
        from multiple sources.
        """
        for o, v in self.items():
            try:
                env_value = environ[o.upper()]
                normalized = self._normalize_name(o)
                if normalized in self._options:
                    self._options[normalized].parse(env_value)
            except KeyError:
                continue

        if final:
            self.run_parse_callbacks()


options = M2OptionParser()
