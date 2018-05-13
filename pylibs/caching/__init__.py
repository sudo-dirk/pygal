"""
Caching Module
==============

**Author:** Dirk Alders <d.alders@arcor.de>
"""


import hashlib
import hmac
import json
from pylibs import report
import os
import pickle

__VERSION__ = '1.1.0'

class property_cache_pickle(report.logit):
    """
    Class to cache properties, which take longer on initialising than reading a file in pickle format.

    :param source_instance: The source instance holding the data
    :type source_instance: instance
    :param cache_filename: File name, where the properties are stored as cache
    :type cache_filename: str
    :param load_all_on_init: Optionally init behaviour control parameter. True will load all available properties from source on init, False not.
    :raises: ?

    .. note:: This module uses logging. So logging should be initialised at least by executing logging.basicConfig(...)

    .. note:: source_instance needs to have at least the following methods: uid(), keys(), data_version(), get()

                * uid(): returns the unique id of the source.
                * keys(): returns a list of all available keys.
                * data_version(): returns a version number of the current data (it should be increased, if the get method of the source instance returns improved values or the data structure had been changed).
                * get(key, default): returns the property for a key. If key does not exists, default will be returned.

    Reasons for updating the complete data set:

    * UID of source_instance has changed (in comparison to the cached value).
    * data_version is increased

    **Example:**

    .. code-block:: python

        logging.basicConfig(format='%(asctime)s::%(levelname)s::%(pathname)s::%(lineno)s::%(message)s', level=logging.DEBUG)

        class test_slow_data(object):
            _ONE = '1'
            _TWO = '2'
            _THREE = '_property_cache_data_version_'
            _FOUR = '_property_cache_uid_'
            _FIVE = '__property_cache_uid_'
            KEYS = [_ONE, _TWO, _THREE, _FOUR, _FIVE]
            VERS = 0.1

            def data_version(self):
                return self.VERS

            def one(self):
                return self.get(self._ONE)

            def two(self):
                return self.get(self._TWO)

            def three(self):
                return self.get(self._THREE)

            def four(self):
                return self.get(self._FOUR)

            def five(self):
                return self.get(self._FIVE)

            def get(self, key, default=None):
                def print_n_sleep(k):
                    logging.info('slow get executed for %s', k)
                    time.sleep(3)
                if key == self._ONE:
                    print_n_sleep(key)
                    return 'one'
                if key == self._TWO:
                    print_n_sleep(key)
                    return 'two'
                if key == self._THREE:
                    print_n_sleep(key)
                    return 'three'
                if key == self._FOUR:
                    print_n_sleep(key)
                    return 'four'
                if key == self._FIVE:
                    print_n_sleep(key)
                    return 'five'
                return default

            def keys(self):
                return self.KEYS

            def uid(self):
                return None

        class tsd_cache_pickle(test_slow_data):
            def __init__(self, *args, **kwargs):
                test_slow_data.__init__(self, *args, **kwargs)
                self._cached_data = property_cache_pickle(test_slow_data(*args, **kwargs), 'cache.pickle', load_all_on_init=False)

            def two(self):
                return test_slow_data.get(self, self._TWO)

            def get(self, key, default=None):
                return self._cached_data.get(key, default)


        data = tsd_cache_pickle()
        print 'Testing property_cache (pickle):\\n--------------------------------'
        print data.one()
        print data.two()
        print data.three()
        print data.four()
        print data.five()

    Will result on the first execution to the following output (with a long execution time):

    .. code-block:: text

        Testing property_cache (pickle):
        --------------------------------
        2015-01-11 17:40:42,172::DEBUG::__init__.py::69::Loading property for "1" from source instance
        2015-01-11 17:40:42,173::INFO::__init__.py::343::slow get executed for 1
        2015-01-11 17:40:45,176::INFO::__init__.py::129::cache-file stored (cache.pickle)
        one
        2015-01-11 17:40:45,176::INFO::__init__.py::343::slow get executed for 2
        two
        2015-01-11 17:40:48,180::DEBUG::__init__.py::69::Loading property for "_property_cache_data_version_" from source instance
        2015-01-11 17:40:48,180::INFO::__init__.py::343::slow get executed for _property_cache_data_version_
        2015-01-11 17:40:51,183::INFO::__init__.py::129::cache-file stored (cache.pickle)
        three
        2015-01-11 17:40:51,184::DEBUG::__init__.py::69::Loading property for "_property_cache_uid_" from source instance
        2015-01-11 17:40:51,184::INFO::__init__.py::343::slow get executed for _property_cache_uid_
        2015-01-11 17:40:54,187::INFO::__init__.py::129::cache-file stored (cache.pickle)
        four
        2015-01-11 17:40:54,188::DEBUG::__init__.py::69::Loading property for "__property_cache_uid_" from source instance
        2015-01-11 17:40:54,188::INFO::__init__.py::343::slow get executed for __property_cache_uid_
        2015-01-11 17:40:57,192::INFO::__init__.py::129::cache-file stored (cache.pickle)
        five

    With every following execution (slow for getting "two" which is not cached - see implementation):

    .. code-block:: text

        Testing property_cache (pickle):
        --------------------------------
        2015-01-11 17:42:42,158::DEBUG::__init__.py::75::Providing property for "1" from cache
        one
        2015-01-11 17:42:42,158::INFO::__init__.py::343::slow get executed for 2
        two
        2015-01-11 17:42:45,161::DEBUG::__init__.py::75::Providing property for "_property_cache_data_version_" from cache
        three
        2015-01-11 17:42:45,162::DEBUG::__init__.py::75::Providing property for "_property_cache_uid_" from cache
        four
        2015-01-11 17:42:45,162::DEBUG::__init__.py::75::Providing property for "__property_cache_uid_" from cache
        five
    """
    LOG_PREFIX = 'PickCache:'
    DATA_VERSION_TAG = '_property_cache_data_version_'
    UID_TAG = '_property_cache_uid_'

    def __init__(self, source_instance, cache_filename, load_all_on_init=False, callback_on_data_storage=None):
        self._source_instance = source_instance
        self._cache_filename = cache_filename
        self._load_all_on_init = load_all_on_init
        self._callback_on_data_storage = callback_on_data_storage
        self._cached_props = None

    def get(self, key, default=None, logger=None):
        """
        Method to get the cached property. If key does not exists in cache, the property will be loaded from source_instance and stored in cache (file).

        :param key: key for value to get.
        :param default: value to be returned, if key does not exists.
        :returns: value for a given key or default value.
        """
        if key in self.keys():
            if self._cached_props is None:
                self._init_cache(logger=logger)
            if self._key_filter(key) not in self._cached_props:
                val = self._source_instance.get(key, None)
                self.logit_debug(logger, "Loading property for '%s' from source instance (%s)", key, repr(val))
                self._cached_props[self._key_filter(key)] = val
                self._save_cache(logger)
            else:
                self.logit_debug(logger, "Providing property for '%s' from cache (%s)", key, repr(self._cached_props.get(self._key_filter(key), default)))
            return self._cached_props.get(self._key_filter(key), default)
        else:
            self.logit_warning(logger, "Key '%s' is not in cached_keys. Uncached data will be returned.", key)
            return self._source_instance.get(key, default)

    def keys(self):
        return self._source_instance.keys()

    def _data_version(self):
        if self._cached_props is None:
            return None
        else:
            return self._cached_props.get(self.DATA_VERSION_TAG, None)

    def _init_cache(self, logger):
        if not self._load_cache(logger=logger) or self._source_instance.uid() != self._uid() or self._source_instance.data_version() > self._data_version():
            if self._uid() is not None and self._source_instance.uid() != self._uid():
                self.logit_debug(logger, "Source uid changed, ignoring previous cache data")
            if self._data_version() is not None and self._source_instance.data_version() > self._data_version():
                self.logit_debug(logger, "Data version increased, ignoring previous cache data")
            self._cached_props = dict()
            if self._load_all_on_init:
                self._load_source(logger)
            self._cached_props[self.UID_TAG] = self._source_instance.uid()
            self._cached_props[self.DATA_VERSION_TAG] = self._source_instance.data_version()
            self._save_cache(logger)

    def _load_cache(self, logger):
        if os.path.exists(self._cache_filename):
            with open(self._cache_filename, 'r') as fh:
                self._cached_props = pickle.loads(fh.read())
            self.logit_info(logger, 'Loading properties from cache (%s)', self._cache_filename)
            return True
        else:
            self.logit_debug(logger, 'Cache file does not exists (yet).')
        return False

    def _key_filter(self, key):
        if type(key) is str or type(key) is unicode:
            if key.endswith(self.DATA_VERSION_TAG) or key.endswith(self.UID_TAG):
                return '_' + key
        return key

    def _load_source(self, logger):
        self.logit_debug(logger, 'Loading all data from source - %s', repr(self._source_instance.keys()))
        for key in self._source_instance.keys():
            val = self._source_instance.get(key, logger=logger)
            self._cached_props[self._key_filter(key)] = val

    def _save_cache(self, logger):
        with open(self._cache_filename, 'w') as fh:
            fh.write(pickle.dumps(self._cached_props))
            self.logit_info(logger, 'cache-file stored (%s)', self._cache_filename)
        if self._callback_on_data_storage is not None:
            self._callback_on_data_storage()

    def _uid(self):
        if self._cached_props is None:
            return None
        else:
            return self._cached_props.get(self.UID_TAG, None)


class property_cache_json(property_cache_pickle):
    """
    Class to cache properties, which take longer on initialising than reading a file in json format. See also parent :py:class:`property_cache_pickle`

    :param source_instance: The source instance holding the data
    :type source_instance: instance
    :param cache_filename: File name, where the properties are stored as cache
    :type cache_filename: str
    :param load_all_on_init: Optionally init behaviour control parameter. True will load all available properties from source on init, False not.
    :raises: ?

    .. warning:: This class uses json. You should **only** use keys of type string!

    .. note:: This module uses logging. So logging should be initialised at least by executing logging.basicConfig(...)

    .. note:: source_instance needs to have at least the following methods: uid(), keys(), data_version(), get()

                * uid(): returns the unique id of the source.
                * keys(): returns a list of all available keys.
                * data_version(): returns a version number of the current data (it should be increased, if the get method of the source instance returns improved values or the data structure had been changed).
                * get(key, default): returns the property for a key. If key does not exists, default will be returned.

    Reasons for updating the complete data set:

    * UID of source_instance has changed (in comparison to the cached value).
    * data_version is increased

    **Example:**

    .. code-block:: python

        logging.basicConfig(format='%(asctime)s::%(levelname)s::%(pathname)s::%(lineno)s::%(message)s', level=logging.DEBUG)

        class test_slow_data(object):
            _ONE = '1'
            _TWO = '2'
            _THREE = '_property_cache_data_version_'
            _FOUR = '_property_cache_uid_'
            _FIVE = '__property_cache_uid_'
            KEYS = [_ONE, _TWO, _THREE, _FOUR, _FIVE]
            VERS = 0.1

            def data_version(self):
                return self.VERS

            def one(self):
                return self.get(self._ONE)

            def two(self):
                return self.get(self._TWO)

            def three(self):
                return self.get(self._THREE)

            def four(self):
                return self.get(self._FOUR)

            def five(self):
                return self.get(self._FIVE)

            def get(self, key, default=None):
                def print_n_sleep(k):
                    logging.info('slow get executed for %s', k)
                    time.sleep(3)
                if key == self._ONE:
                    print_n_sleep(key)
                    return 'one'
                if key == self._TWO:
                    print_n_sleep(key)
                    return 'two'
                if key == self._THREE:
                    print_n_sleep(key)
                    return 'three'
                if key == self._FOUR:
                    print_n_sleep(key)
                    return 'four'
                if key == self._FIVE:
                    print_n_sleep(key)
                    return 'five'
                return default

            def keys(self):
                return self.KEYS

            def uid(self):
                return None

        class tsd_cache_json(test_slow_data):
            def __init__(self, *args, **kwargs):
                test_slow_data.__init__(self, *args, **kwargs)
                self._cached_data = property_cache_json(test_slow_data(*args, **kwargs), 'cache.json', load_all_on_init=False)

            def one(self):
                return test_slow_data.get(self, self._ONE)

            def get(self, key, default=None):
                return self._cached_data.get(key, default)
        

        data = tsd_cache_json()
        print 'Testing property_cache (json):\\n------------------------------'
        print data.one()
        print data.two()
        print data.three()
        print data.four()
        print data.five()

    Will result on the first execution to the following output (with a long execution time):

    .. code-block:: text

        Testing property_cache (json):
        ------------------------------
        2015-01-11 17:34:53,522::INFO::__init__.py::342::slow get executed for 1
        one
        2015-01-11 17:34:56,526::DEBUG::__init__.py::69::Loading property for "2" from source instance
        2015-01-11 17:34:56,526::INFO::__init__.py::342::slow get executed for 2
        2015-01-11 17:34:59,529::INFO::__init__.py::305::cache-file stored (cache.json)
        two
        2015-01-11 17:34:59,530::DEBUG::__init__.py::69::Loading property for "_property_cache_data_version_" from source instance
        2015-01-11 17:34:59,530::INFO::__init__.py::342::slow get executed for _property_cache_data_version_
        2015-01-11 17:35:02,533::INFO::__init__.py::305::cache-file stored (cache.json)
        three
        2015-01-11 17:35:02,533::DEBUG::__init__.py::69::Loading property for "_property_cache_uid_" from source instance
        2015-01-11 17:35:02,533::INFO::__init__.py::342::slow get executed for _property_cache_uid_
        2015-01-11 17:35:05,537::INFO::__init__.py::305::cache-file stored (cache.json)
        four
        2015-01-11 17:35:05,537::DEBUG::__init__.py::69::Loading property for "__property_cache_uid_" from source instance
        2015-01-11 17:35:05,538::INFO::__init__.py::342::slow get executed for __property_cache_uid_
        2015-01-11 17:35:08,541::INFO::__init__.py::305::cache-file stored (cache.json)
        five

    With every following execution (slow for getting "one" which is not cached - see implementation):

    .. code-block:: text

        Testing property_cache (json):
        ------------------------------
        2015-01-11 17:35:53,709::INFO::__init__.py::342::slow get executed for 1
        one
        2015-01-11 17:35:56,713::DEBUG::__init__.py::75::Providing property for "2" from cache
        two
        2015-01-11 17:35:56,713::DEBUG::__init__.py::75::Providing property for "_property_cache_data_version_" from cache
        three
        2015-01-11 17:35:56,713::DEBUG::__init__.py::75::Providing property for "_property_cache_uid_" from cache
        four
        2015-01-11 17:35:56,713::DEBUG::__init__.py::75::Providing property for "__property_cache_uid_" from cache
        five
    """
    LOG_PREFIX = 'JsonCache:'

    def _load_cache(self, logger):
        if os.path.exists(self._cache_filename):
            with open(self._cache_filename, 'r') as fh:
                self._cached_props = json.loads(fh.read())
            self.logit_info(logger, 'Loading properties from cache (%s)', self._cache_filename)
            return True
        else:
            self.logit_debug(logger, 'Cache file does not exists (yet).')
        return False

    def _save_cache(self, logger):
        with open(self._cache_filename, 'w') as fh:
            fh.write(json.dumps(self._cached_props, sort_keys=True, indent=4))
            self.logit_info(logger, 'cache-file stored (%s)', self._cache_filename)
        if self._callback_on_data_storage is not None:
            self._callback_on_data_storage()
