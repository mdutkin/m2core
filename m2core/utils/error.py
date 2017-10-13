import logging


logger = logging.getLogger(__name__)


class M2Error(Exception):
    """
    Raise this error wherever you want you exception to be raised, logged and showed up to user with custom message
    """
    def __init__(self, msg: str='', show_to_user: bool=False):
        self.error_message = msg
        self.show_to_user = show_to_user
        self._log()

    def _log(self):
        logger.error(self.error_message)

    def __repr__(self):
        return self.error_message
