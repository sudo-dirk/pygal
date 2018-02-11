"""
Report Module(report)
=====================

**Author:**

* Dirk Alders <d.alders@arcor.de>

"""
import logging
import os
import sys


class logit(object):
    """
    Class to be used as parent to log records.
    """
    LOG_STR = '%-10s %s'
    LOG_PREFIX = 'None:'

    def logit(self, logger, level, msg, *args, **kwargs):
        """This logs a message for a given logger and level.

        :param logger: The logger to be used or None, if no logging is needed
        :param int level: The level for the log record (e.g. logging.INFO)
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if logger is not None and logger.isEnabledFor(level):
            logger._log(level, self.LOG_STR % (self.LOG_PREFIX, msg), args, kwargs)

    def logit_debug(self, logger, msg, *args, **kwargs):
        """This logs a message for a given logger at level debug.

        :param logger: The logger to be used or None, if no logging is needed
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if logger is not None and logger.isEnabledFor(logging.DEBUG):
            logger._log(logging.DEBUG, self.LOG_STR % (self.LOG_PREFIX, msg), args, kwargs)

    def logit_info(self, logger, msg, *args, **kwargs):
        """This logs a message for a give logger at level INFO.

        :param logger: The logger to be used or None, if no logging is needed
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if logger is not None and logger.isEnabledFor(logging.INFO):
            logger._log(logging.INFO, self.LOG_STR % (self.LOG_PREFIX, msg), args, kwargs)

    def logit_warning(self, logger, msg, *args, **kwargs):
        """This logs a message for a give logger at level WARNING.

        :param logger: The logger to be used or None, if no logging is needed
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if logger is not None and logger.isEnabledFor(logging.WARNING):
            logger._log(logging.WARNING, self.LOG_STR % (self.LOG_PREFIX, msg), args, kwargs)

    def logit_error(self, logger, msg, *args, **kwargs):
        """This logs a message for a give logger at level ERROR.

        :param logger: The logger to be used or None, if no logging is needed
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if logger is not None and logger.isEnabledFor(logging.ERROR):
            logger._log(logging.ERROR, self.LOG_STR % (self.LOG_PREFIX, msg), args, kwargs)

    def logit_critical(self, logger, msg, *args, **kwargs):
        """This logs a message for a give logger at level CRITICAL.

        :param logger: The logger to be used or None, if no logging is needed
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if logger is not None and logger.isEnabledFor(logging.CRITICAL):
            logger._log(logging.CRITICAL, self.LOG_STR % (self.LOG_PREFIX, msg), args, kwargs)
