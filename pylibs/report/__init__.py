"""
Report Module(report)
=====================

**Author:**

* Dirk Alders <d.alders@arcor.de>

"""
try:
    import jinja2
except:
    jinja2 = None
import logging
import os
import sys

SHORT_FMT = "%(asctime)s: %(levelname)-7s - %(message)s"
""" A short formatter including the most important information"""
LONG_FMT = """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
File "%(pathname)s", line %(lineno)d, in %(funcName)s
%(asctime)s: %(levelname)-7s - %(message)s"""
""" A long formatter which results in links to the source code inside Eclipse"""
DEFAULT_FMT = LONG_FMT
"""The default formatstring"""
TCEL_SMOKE = 10
"""Testcase level (smoke), this is just a rough test for the main functionality"""
TCEL_SHORT = 50
"""Testcase level (short), this is a short test for an extended functionality"""
TCEL_FULL = 90
"""Testcase level (full), this is a complete test for the full functionality"""
TCEL_NAMES = {TCEL_SMOKE: 'Smoke',
              TCEL_SHORT: 'Short',
              TCEL_FULL: 'Full'}
"""Dictionary for resolving the test case levels (TCL) to a (human readable) name"""


class __recordCollection__(list):
    def get(self, level):
        l = __recordCollection__()
        for entry in self:
            if entry.levelno >= level:
                l.append(entry.__dict__)
        return l


class __collectingFormatter__(logging.Formatter):
    def __init__(self, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self.collection = __recordCollection__()
        self._max_level = 0

    def format(self, *args, **kwargs):
        record = args[0]
        if record.levelno > self._max_level:
            self._max_level = record.levelno
        self.collection.append(record)
        return logging.Formatter.format(self, *args, **kwargs)

    def max_level(self):
        return self._max_level


class __collectingFormatterTestcase__(__collectingFormatter__):
    def __init__(self, *args, **kwargs):
        self.fmt = args[0]
        self.level_stream_list = kwargs.pop('level_stream_list')
        __collectingFormatter__.__init__(self, *args, **kwargs)
        self._module_logger = None

    def get_module_logger(self):
        if self._module_logger is None:
            self._module_logger = collectingLogger('Details', self.level_stream_list, fmt=self.fmt)
            self._module_logger.debug("REPORT: Starting...")
        return self._module_logger

    def format(self, *args, **kwargs):
        args[0].__dict__['moduleLogger'] = self._module_logger
        self._module_logger = None
        __collectingFormatter__.format(self, *args, **kwargs)


class __destroying_stream__(object):
    def write(self, *args, **kwargs):
        pass


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


class logit_to_central_logger(object):
    """
    Class to be used for logging to a logger given on initialisation.
    """
    LOG_STR = '%-10s %s'

    def __init__(self, logger, prefix='None:'):
        self._logger = logger
        self._prefix = prefix

    def logit(self, level, msg, *args, **kwargs):
        """This logs a message for a given level.

        :param int level: The level for the log record (e.g. logging.INFO)
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """

        if self._logger is not None and self._logger.isEnabledFor(level):
            self._logger._log(level, self.LOG_STR % (self._prefix, msg), args, kwargs)

    def logit_debug(self, msg, *args, **kwargs):
        """This logs a message at level debug.

        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if self._logger is not None and self._logger.isEnabledFor(logging.DEBUG):
            self._logger._log(logging.DEBUG, self.LOG_STR % (self._prefix, msg), args, kwargs)

    def logit_info(self, msg, *args, **kwargs):
        """This logs a message at level INFO.

        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if self._logger is not None and self._logger.isEnabledFor(logging.INFO):
            self._logger._log(logging.INFO, self.LOG_STR % (self._prefix, msg), args, kwargs)

    def logit_warning(self, msg, *args, **kwargs):
        """This logs a message at level WARNING.

        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if self._logger is not None and self._logger.isEnabledFor(logging.WARNING):
            self._logger._log(logging.WARNING, self.LOG_STR % (self._prefix, msg), args, kwargs)

    def logit_error(self, msg, *args, **kwargs):
        """This logs a message at level ERROR.

        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if self._logger is not None and self._logger.isEnabledFor(logging.ERROR):
            self._logger._log(logging.ERROR, self.LOG_STR % (self._prefix, msg), args, kwargs)

    def logit_critical(self, logger, msg, *args, **kwargs):
        """This logs a message for a give logger at level CRITICAL.

        :param logger: The logger to be used or None, if no logging is needed
        :param str msg: The message to be logged
        :param args: Arguments for messsage
        :param kwargs: Keyword arguments for message
        """
        if logger is not None and logger.isEnabledFor(logging.CRITICAL):
            logger._log(logging.CRITICAL, self.LOG_STR % (self._prefix, msg), args, kwargs)

def getLogger(name, level_stream_list=[], fmt=None):
    """
    Class to stream log records.

    :param str name: The Name of the Logger
    :param list level_stream_list: A list of tuples including level and stream (e.g.: `[(logging.DEBUG, sys.stdout), (logging.WARNING, sys.stderr)]`).
    :param str fmt: A format string for the log output (see :py:class:`logging` for more details). :py:const:`DEFAULT_FMT` is used if `fmt` is `None`.
    """
    fmt = fmt or DEFAULT_FMT
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    #
    for level, stream in level_stream_list:
        lh = logging.StreamHandler(stream)
        lh.setFormatter(logging.Formatter(fmt))
        lh.setLevel(level)
        logger.addHandler(lh)
    return logger


class collectingLogger(logging.Logger):
    """
    Class to collect (all) and stream log records.

    :param str name: The Name of the Logger
    :param list level_stream_list: A list of tuples including level and stream (e.g.: `[(logging.DEBUG, sys.stdout), (logging.WARNING, sys.stderr)]`).
    :param str fmt: A format string for the log output (see :py:class:`logging` for more details). :py:const:`DEFAULT_FMT` is used if `fmt` is `None`.
    """
    def __init__(self, name, level_stream_list=[], fmt=None):
        fmt = fmt or DEFAULT_FMT
        logging.Logger.__init__(self, name, logging.DEBUG)
        self.name = name
        self.formatter = __collectingFormatter__(fmt)
        lh = logging.StreamHandler(__destroying_stream__())
        lh.setFormatter(self.formatter)
        lh.setLevel(logging.DEBUG)
        self.addHandler(lh)
        #
        for level, stream in level_stream_list:
            lh = logging.StreamHandler(stream)
            lh.setFormatter(logging.Formatter(fmt))
            lh.setLevel(level)
            self.addHandler(lh)

    def get_module_logger(self):
        """This returns this collecting logger, cause it already is the module logger.
        """
        return self

    def max_level(self):
        return self.formatter.max_level()

    def max_level_name(self):
        return logging.getLevelName(self.max_level())

    def getLogs(self, level=0):
        """This returns a list of logged data (dict) higher than a given level. The return object is json processable.

        :param int level: The level to be streamed (e.g. logging.INFO)
        :returns: A list of logged data (dictionaries)
        """
        return self.formatter.collection.get(level)

    def get_json_processable_object(self, level=0):
        logs = list()
        json_obj = self.getLogs(level)
        for index in range(0, len(json_obj)):
            d = dict()
            for key in json_obj[index]:
                if type(json_obj[index][key]) in [collectingLogger, collectingTestcaseLogger]:
                    d[key] = json_obj[index][key].get_json_processable_object()
                else:
                    d[key] = json_obj[index][key]
            logs.append(d)
        return logs


class collectingTestcaseLogger(collectingLogger):
    """
    Class to collect (all) testcases and stream log records.

    :param str name: The Name of the Logger
    :param list level_stream_list: A list of tuples including level and stream (e.g.: `[(logging.DEBUG, sys.stdout), (logging.WARNING, sys.stderr)]`).
    :param str fmt: A format string for the log output (see :py:class:`logging` for more details). :py:const:`DEFAULT_FMT` is used if `fmt` is `None`.

    .. note:: A :py:class:`collectingLogger` can be created by :py:func:`get_module_logger`. It will be stored with the next log record.
    """
    def __init__(self, name, level_stream_list=[], fmt=None):
        fmt = fmt or DEFAULT_FMT
        logging.Logger.__init__(self, name, logging.DEBUG)
        self.name = name
        self.formatter = __collectingFormatterTestcase__(fmt, level_stream_list=level_stream_list)
        lh = logging.StreamHandler(__destroying_stream__())
        lh.setFormatter(self.formatter)
        lh.setLevel(logging.DEBUG)
        self.addHandler(lh)
        #
        for level, stream in level_stream_list:
            lh = logging.StreamHandler(stream)
            lh.setFormatter(logging.Formatter(fmt))
            lh.setLevel(level)
            self.addHandler(lh)

    def get_module_logger(self):
        """Method to get a module logger which will be stored with the next log record.

        :rtype: collectingLogger
        """
        return self.formatter.get_module_logger()


class testCaseLogger(collectingLogger):
    """
    Class to collect logs of a test cases. See also parent class :py:class:`collectingLogger`

    :param str name: Name of the test case group
    :param str version: Version of the test case group
    :param int testcase_execution_level: Level of test case execution (all levels below and equal will be executed - see also :py:class:`testCase`)
    :param list level_stream_list: A list of tuples including level and stream (e.g.: `[(logging.DEBUG, sys.stdout), (logging.WARNING, sys.stderr)]`).
    :param str fmt: A format string for the log output (see :py:class:`logging` for more details). :py:const:`DEFAULT_FMT` is used if `fmt` is `None`.

    .. note:: A :py:class:`collectingTestcaseLogger` is stored for every test case log record. See :py:class:`testCase()` for more information how to execute a testcase.

        * The testcaseLogger can be used to log more general information what the test is doing
        * The moduleLogger can be used to log the details (e.g. communication details, ...)

    **Example:**

    .. code-block:: python

        def test(tLogger, num):
            rv = logging.DEBUG
            tLogger.get_module_logger().info('got parameter type = %s', repr(type(num)))
            if type(num) is int:
                tLogger.info('Type of Parameter is integer.')
                if rv < logging.INFO:
                    rv = logging.INFO
            else:
                tLogger.error('Type of Parameter is not integer.')
                if rv < logging.ERROR:
                    rv = logging.ERROR

            tLogger.get_module_logger().info('got parameter num = %d', num)
            if num == 3:
                tLogger.info('Parameter is 3.')
                if rv < logging.INFO:
                    rv = logging.INFO
            else:
                tLogger.error('Parameter is not 3 (%d).', num)
                if rv < logging.ERROR:
                    rv = logging.ERROR
            return rv

        tcl = report.testCaseLogger(testcase_execution_level=report.TCEL_FULL, level_stream_list=[(logging.ERROR, sys.stderr), (logging.DEBUG, sys.stdout)], name='Test Group', version='0.1', tests=[5, 3])
        tcl.testCase('Parameter is 3?', report.TCEL_FULL, test, 5)
        tcl.testCase('Parameter is 3?', report.TCEL_SMOKE, test, 3)
        print tcl

    Will result to the following output:

    * **stderr**

    .. code-block:: text

        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 24, in test
        2015-09-24 15:01:22,424: ERROR   - Parameter is not 3 (5).
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 30, in <module>
        2015-09-24 15:01:22,426: ERROR   - Parameter is 3?

    * **stdout**

    .. code-block:: text

        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/report\__init__.py", line 72, in get_module_logger
        2015-09-24 15:01:22,424: DEBUG   - REPORT: Starting...
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 8, in test
        2015-09-24 15:01:22,424: INFO    - got parameter type = <type 'int'>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 10, in test
        2015-09-24 15:01:22,424: INFO    - Type of Parameter is integer.
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/report\__init__.py", line 72, in get_module_logger
        2015-09-24 15:01:22,424: DEBUG   - REPORT: Starting...
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 18, in test
        2015-09-24 15:01:22,424: INFO    - got parameter num = 5
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 24, in test
        2015-09-24 15:01:22,424: ERROR   - Parameter is not 3 (5).
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 30, in <module>
        2015-09-24 15:01:22,426: ERROR   - Parameter is 3?
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/report\__init__.py", line 72, in get_module_logger
        2015-09-24 15:01:22,426: DEBUG   - REPORT: Starting...
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 8, in test
        2015-09-24 15:01:22,426: INFO    - got parameter type = <type 'int'>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 10, in test
        2015-09-24 15:01:22,426: INFO    - Type of Parameter is integer.
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/report\__init__.py", line 72, in get_module_logger
        2015-09-24 15:01:22,427: DEBUG   - REPORT: Starting...
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 18, in test
        2015-09-24 15:01:22,427: INFO    - got parameter num = 3
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 20, in test
        2015-09-24 15:01:22,427: INFO    - Parameter is 3.
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        File "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py", line 31, in <module>
        2015-09-24 15:01:22,427: INFO    - Parameter is 3?
        tests: [5, 3]
        version: 0.1
        testcase_execution_level: 90
        name: Test Group
        testcase_names: {10: 'Smoke', 90: 'Full', 50: 'Short'}
                 ERROR    Parameter is 3?
                          INFO     Type of Parameter is integer.
                                   DEBUG    2015-09-24 15:08:12,875  REPORT: Starting...
                                   INFO     2015-09-24 15:08:12,875  got parameter type = <type 'int'>
                          ERROR    Parameter is not 3 (5).
                                   DEBUG    2015-09-24 15:08:12,877  REPORT: Starting...
                                   INFO     2015-09-24 15:08:12,877  got parameter num = 5
                 INFO     Parameter is 3?
                          INFO     Type of Parameter is integer.
                                   DEBUG    2015-09-24 15:08:12,878  REPORT: Starting...
                                   INFO     2015-09-24 15:08:12,878  got parameter type = <type 'int'>
                          INFO     Parameter is 3.
                                   DEBUG    2015-09-24 15:08:12,878  REPORT: Starting...
                                   INFO     2015-09-24 15:08:12,878  got parameter num = 3

        {
            "info": {
                "name": "Test Group",
                "testcase_execution_level": 90,
                "testcase_names": {
                    "10": "Smoke",
                    "50": "Short",
                    "90": "Full"
                },
                "tests": [
                    5,
                    3
                ],
                "version": "0.1"
            },
            "logs": [
                {
                    "args": "Parameter is 3?",
                    "asctime": "2015-09-24 15:08:12,877",
                    "created": 1443100092.877,
                    "exc_info": null,
                    "exc_text": null,
                    "filename": "unittest.py",
                    "funcName": "<module>",
                    "levelname": "ERROR",
                    "levelno": 40,
                    "lineno": 31,
                    "message": "Parameter is 3?",
                    "module": "unittest",
                    "msecs": 877.000093460083,
                    "msg": "%s",
                    "name": "Test Group",
                    "pathname": "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py",
                    "process": 1628,
                    "processName": "MainProcess",
                    "relativeCreated": 4.000186920166016,
                    "testcaseLogger": [
                        {
                            "asctime": "2015-09-24 15:08:12,877",
                            "created": 1443100092.877,
                            "exc_info": null,
                            "exc_text": null,
                            "filename": "unittest.py",
                            "funcName": "test",
                            "levelname": "INFO",
                            "levelno": 20,
                            "lineno": 11,
                            "message": "Type of Parameter is integer.",
                            "module": "unittest",
                            "moduleLogger": [
                                {
                                    "args": [],
                                    "asctime": "2015-09-24 15:08:12,875",
                                    "created": 1443100092.876,
                                    "exc_info": null,
                                    "exc_text": null,
                                    "filename": "__init__.py",
                                    "funcName": "get_module_logger",
                                    "levelname": "DEBUG",
                                    "levelno": 10,
                                    "lineno": 72,
                                    "message": "REPORT: Starting...",
                                    "module": "__init__",
                                    "msecs": 875.999927520752,
                                    "msg": "REPORT: Starting...",
                                    "name": "Details",
                                    "pathname": "/home/dirk/projekte/python/pylibs/_unittest/report/src/report\\__init__.py",
                                    "process": 1628,
                                    "processName": "MainProcess",
                                    "relativeCreated": 3.000020980834961,
                                    "thread": 8660,
                                    "threadName": "MainThread"
                                },
                                {
                                    "args": [
                                        "<type 'int'>"
                                    ],
                                    "asctime": "2015-09-24 15:08:12,875",
                                    "created": 1443100092.876,
                                    "exc_info": null,
                                    "exc_text": null,
                                    "filename": "unittest.py",
                                    "funcName": "test",
                                    "levelname": "INFO",
                                    "levelno": 20,
                                    "lineno": 9,
                                    "message": "got parameter type = <type 'int'>",
                                    "module": "unittest",
                                    "msecs": 875.999927520752,
                                    "msg": "got parameter type = %s",
                                    "name": "Details",
                                    "pathname": "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py",
                                    "process": 1628,
                                    "processName": "MainProcess",
                                    "relativeCreated": 3.000020980834961,
                                    "thread": 8660,
                                    "threadName": "MainThread"
                                }
                            ],
                            "msecs": 877.000093460083,
                            "msg": "Type of Parameter is integer.",
                            "name": "Testcase",
                            "pathname": "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py",
                            "process": 1628,
                            "processName": "MainProcess",
                            "relativeCreated": 4.000186920166016,
                            "thread": 8660,
                            "threadName": "MainThread"
                        },
                        {
                            "args": [
                                5
                            ],
                            "asctime": "2015-09-24 15:08:12,877",
                            "created": 1443100092.877,
                            "exc_info": null,
                            "exc_text": null,
                            "filename": "unittest.py",
                            "funcName": "test",
                            "levelname": "ERROR",
                            "levelno": 40,
                            "lineno": 25,
                            "message": "Parameter is not 3 (5).",
                            "module": "unittest",
                            "moduleLogger": [
                                {
                                    "args": [],
                                    "asctime": "2015-09-24 15:08:12,877",
                                    "created": 1443100092.877,
                                    "exc_info": null,
                                    "exc_text": null,
                                    "filename": "__init__.py",
                                    "funcName": "get_module_logger",
                                    "levelname": "DEBUG",
                                    "levelno": 10,
                                    "lineno": 72,
                                    "message": "REPORT: Starting...",
                                    "module": "__init__",
                                    "msecs": 877.000093460083,
                                    "msg": "REPORT: Starting...",
                                    "name": "Details",
                                    "pathname": "/home/dirk/projekte/python/pylibs/_unittest/report/src/report\\__init__.py",
                                    "process": 1628,
                                    "processName": "MainProcess",
                                    "relativeCreated": 4.000186920166016,
                                    "thread": 8660,
                                    "threadName": "MainThread"
                                },
                                {
                                    "args": [
                                        5
                                    ],
                                    "asctime": "2015-09-24 15:08:12,877",
                                    "created": 1443100092.877,
                                    "exc_info": null,
                                    "exc_text": null,
                                    "filename": "unittest.py",
                                    "funcName": "test",
                                    "levelname": "INFO",
                                    "levelno": 20,
                                    "lineno": 19,
                                    "message": "got parameter num = 5",
                                    "module": "unittest",
                                    "msecs": 877.000093460083,
                                    "msg": "got parameter num = %d",
                                    "name": "Details",
                                    "pathname": "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py",
                                    "process": 1628,
                                    "processName": "MainProcess",
                                    "relativeCreated": 4.000186920166016,
                                    "thread": 8660,
                                    "threadName": "MainThread"
                                }
                            ],
                            "msecs": 877.000093460083,
                            "msg": "Parameter is not 3 (%d).",
                            "name": "Testcase",
                            "pathname": "/home/dirk/projekte/python/pylibs/_unittest/report/src/unittest.py",
                            "process": 1628,
                            "processName": "MainProcess",
                            "relativeCreated": 4.000186920166016,
                            "thread": 8660,
                            "threadName": "MainThread"
                        }
                    ],
                    "thread": 8660,
                    "threadName": "MainThread"
                }
            ]
        }
    """
    T_LOGGER = 'testcaseLogger'
    """Definition for getting the testcase Logger"""
    M_LOGGER = 'moduleLogger'
    """Definition for getting the module Logger"""

    def __init__(self, level_stream_list=[], fmt=None, **kwargs):
        self._testcase_execution_level = kwargs.get('testcase_execution_level', None)
        if self._testcase_execution_level is None:
            tcel_default = TCEL_FULL
            kwargs['testcase_execution_level'] = tcel_default
            self._testcase_execution_level = tcel_default
        kwargs['testcase_names'] = TCEL_NAMES
        fmt = fmt or DEFAULT_FMT
        collectingLogger.__init__(self, kwargs['name'], level_stream_list, fmt)
        self._json_log = kwargs
        self._json_log['number_of_tests'] = 0
        self._json_log['number_of_failed_tests'] = 0
        self._json_log['number_of_successfull_tests'] = 0
        self.level_stream_list = level_stream_list
        self.fmt = fmt

    def testcase_execution_level(self):
        """This returns the testcase_execution_level of this testcase.

        :returns: The testcase execution level
        :rtype: int
        """
        return self._testcase_execution_level

    def testcase_execution_name(self):
        """This returns the name of the testcase_execution_level of this testcase.

        :returns: The name of the testcase execution level or None, if the level is not defined
        :rtype: str or None
        """
        return TCEL_NAMES.get(self._testcase_execution_level, None)

    def testCase(self, msg, testcase_level, testcase_func, *args, **kwargs):
        """This executes the testcase and stores the logging events.

        :param str msg: Description of the testcase
        :param str testcase_level: Testcase level for execution, depending on initialisation the testcase_function will be executed or not
        :param testcase_func: The test function to be executed
        :param args: Arguments for testcase_func
        :param kwargs: Keywordarguments for testcase_func
        :param list pre_exec: A list of methods to be executed before performing `testcase_func`
        :param list post_exec: A list of methods to be executed after `testcase_func` has been performed

        .. note:: A testcaseLogger is passed to :py:func:`testcase_func`, `pre_exec`- and `post_exec`-functions as the first argument followed by args and kwargs.
        """
        if testcase_level <= self._testcase_execution_level:
            pre_exec = kwargs.pop('pre_exec', None)
            post_exec = kwargs.pop('post_exec', None)
            testcaseLogger = collectingTestcaseLogger('Testcase', self.level_stream_list, fmt=self.fmt)
            if pre_exec is not None:
                for func in pre_exec:
                    func(testcaseLogger)
            testcase_func(testcaseLogger, *args, **kwargs)
            if post_exec is not None:
                for func in post_exec:
                    func(testcaseLogger)
            self._json_log['number_of_tests'] += 1
            if testcaseLogger.max_level() >= logging.WARNING:
                level_to_log = logging.ERROR    # Overall level to report
                self._json_log['number_of_failed_tests'] += 1
            else:
                level_to_log = logging.INFO		# Overall level to report
                self._json_log['number_of_successfull_tests'] += 1
            time_start = testcaseLogger.getLogs()[0].get(self.M_LOGGER).getLogs()[0].get('asctime')
            time_finished = testcaseLogger.getLogs()[-1].get('asctime')
            time_consumption = testcaseLogger.getLogs()[-1].get('created') - testcaseLogger.getLogs()[0].get(self.M_LOGGER).getLogs()[0].get('created')
            self._log(level_to_log, '%s', msg, extra={self.T_LOGGER: testcaseLogger,
                                                      'time_start': time_start,
                                                      'time_finished': time_finished,
                                                      'time_consumption': time_consumption})

    def get_json_processable_object(self, level=0, create_dict=False):
        """This returns a json processable object of the instance.

        :param int level: The level to be streamed (e.g. logging.INFO)
        :returns: A dictionary including with key 'logs' a list as generated by `getLogs()` and with key 'info' a dictionary with all additional keyword arguments given on initialisation.
        """
        rv = dict()
        for key in self._json_log:
            rv[key] = self._json_log[key]
        time_consumption = 0.
        if create_dict:
            rv['testcases'] = dict()
        else:
            rv['testcases'] = list()
        for log in collectingLogger.get_json_processable_object(self, level):
            time_consumption += log['time_consumption']
            if create_dict:
                rv['testcases'][log['args']] = log
            else:
                rv['testcases'].append(log)
        rv['time_consumption'] = time_consumption
        return rv

    def get_templated_report(self, template_file_path, level=logging.DEBUG, color_by_level={'DEBUG': 'green', 'INFO': 'green', 'WARNING': 'orange', 'ERROR': 'red', 'CRITICAL': 'red'}):
        if jinja2 is not None:
            template_path = os.path.dirname(template_file_path)
            template_filename = os.path.basename(template_file_path)
            jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
            template = jenv.get_template(template_filename)
            return template.render(json_obj=self.get_json_processable_object(level), color_by_level=color_by_level)
        else:
            return "You need to install jinja2 to create a templated report"

    def __str__(self, level=0):
        rv = ''
        for key in self._json_log:
            rv += u'%s: %s\n' % (key, self._json_log[key])
        for test in self.getLogs(level):
            rv += '         %(levelname)-9s%(message)s\n' % test
            for tLogger in test.get(self.T_LOGGER).getLogs(logging.DEBUG):
                rv += '                  %(levelname)-9s%(message)s\n' % tLogger
                for mLogger in tLogger.get('moduleLogger').getLogs(logging.DEBUG):
                    rv += '                           %(levelname)-9s%(asctime)-25s%(message)s\n' % mLogger
        return rv
