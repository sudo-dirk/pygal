#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Multimedia Module
=================

**Author:** Dirk Alders <d.alders@arcor.de>
"""

import os
from pylibs import report

__all__ = ['multimedia.video', 'multimedia.picture']


class base_info(report.logit):
    """Base class to hold and handle information of a file

    :param str filename: Name of the source file

    .. note:: This is is not designed to be used directly.
    """
    TAG_TYPES = {}
    LOG_PREFIX = 'MULTIMEDIA:'

    def __init__(self, filename):
        self.filename = filename
        self._info = None

    def get(self, key, default=None, logger=None):
        """
        This gets an information of the sourcefile by a key.

        :param key: The key (name) of the information to get
        :param default: The default value to be returned, if no information with that key exists
        :returns: The information for the given key
        """
        self.logit_debug(logger, "Property request (%s) for %s", key, os.path.basename(self.filename))
        if self._info is None:
            self._get_info(logger=logger)
        return self._info.get(key, default)

    def keys(self):
        """
        This returns a list of all available keys.

        :returns: The keylist
        :rtype: list
        """
        return self.TAG_TYPES.keys()

    def _get_info(self, logger=None):
        (logger)
        self._info = dict()
