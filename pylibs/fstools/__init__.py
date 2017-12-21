#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Filesystem Tools
================

**Author:** Dirk Alders <d.alders@arcor.de>
"""

import glob
import hashlib
import hmac
import os
import sys
import time
from pylibs import report


class fstools_logit(report.logit):
    LOG_PREFIX = 'fstools:'

def uid(pathname, max_staleness=3600):
    """
    Function returning a unique id for a given file or path.

    :param str pathname: File or Path name for generation of the uid.
    :param int max_staleness: If a file or path is older than that, we may consider
                              it stale and return a different uid - this is a
                              dirty trick to work around changes never being
                              detected. Default is 3600 seconds, use None to
                              disable this trickery. See below for more details.
    :returns:  An object that changes value if the file changed,
               None is returned if there were problems accessing the file
    :rtype: str

    .. note:: Depending on the operating system capabilities and the way the
              file update is done, this function might return the same value
              even if the file has changed. It should be better than just
              using file's mtime though.
              max_staleness tries to avoid the worst for these cases.

    .. note:: If this function is used for a path, it will stat all pathes and files rekursively.

    Using just the file's mtime to determine if the file has changed is
    not reliable - if file updates happen faster than the file system's
    mtime granularity, then the modification is not detectable because
    the mtime is still the same.

    This function tries to improve by using not only the mtime, but also
    other metadata values like file size and inode to improve reliability.

    For the calculation of this value, we of course only want to use data
    that we can get rather fast, thus we use file metadata, not file data
    (file content).

    >>> print 'UID:', uid(__file__)
    UID: 16a65cc78e1344e596ef1c9536dab2193a402934
    """
    if os.path.isdir(pathname):
        pathlist =  dirlist(pathname) + filelist(pathname)
        pathlist.sort()
    else:
        pathlist = [pathname]
    uid = []
    for element in pathlist:
        try:
            st = os.stat(element)
        except (IOError, OSError):
            uid.append(None)    # for permanent errors on stat() this does not change, but
            #                     having a changing value would be pointless because if we
            #                     can't even stat the file, it is unlikely we can read it.
        else:
            fake_mtime = int(st.st_mtime)
            if not st.st_ino and max_staleness:
                # st_ino being 0 likely means that we run on a platform not
                # supporting it (e.g. win32) - thus we likely need this dirty
                # trick
                now = int(time.time())
                if now >= st.st_mtime + max_staleness:
                    # keep same fake_mtime for each max_staleness interval
                    fake_mtime = int(now / max_staleness) * max_staleness
            uid.append((st.st_mtime,    # might have a rather rough granularity, e.g. 2s
                                        # on FAT, 1s on ext3 and might not change on fast
                                        # updates
                   st.st_ino,           # inode number (will change if the update is done
                                        # by e.g. renaming a temp file to the real file).
                                        # not supported on win32 (0 ever)
                   st.st_size,          # likely to change on many updates, but not
                                        # sufficient alone
                   fake_mtime)          # trick to workaround file system / platform
                                        # limitations causing permanent trouble
                   )
    secret = ''
    return hmac.new(secret, repr(uid), hashlib.sha1).hexdigest()

def filelist(path='.', expression='*', rekursive=True, logger=None):
    """
    Function returning a list of files below a given path.

    :param str path: folder which is the basepath for searching files.
    :param str expression: expression to fit including shell-style wildcards.
    :param bool rekursive: search all subfolders if True.
    :param logger: Optionally logger instance to use instead of creating one.
    :returns: list of filenames including the pathe
    :rtype: list

    .. note:: The returned filenames could be relative pathes depending on argument path.

    >>> for filename in filelist(path='.', expression='*.py*', rekursive=True):
    ...     print filename
    ./__init__.py
    ./__init__.pyc
    """
    logit = fstools_logit()
    l = list()
    if os.path.exists(path):
        logit.logit_debug(logger, 'path (%s) exists - looking for files to append', path)
        for filename in glob.glob(os.path.join(path, expression)):
            if os.path.isfile(filename):
                l.append(filename)
        for directory in os.listdir(path):
            directory = os.path.join(path, directory)
            if os.path.isdir(directory) and rekursive:
                l.extend(filelist(directory, expression))
    else:
        logit.logit_info(logger, 'path (%s) does not exist - empty filelist will be returned', path)
    return l

def dirlist(path='.', rekursive=True, logger=None):
    """
    Function returning a list of directories below a given path.

    :param str path: folder which is the basepath for searching files.
    :param bool rekursive: search all subfolders if True.
    :param logger: Optionally logger instance to use instead of creating one.
    :returns: list of filenames including the pathe
    :rtype: list

    .. note:: The returned filenames could be relative pathes depending on argument path.

    >>> for dirname in dirlist(path='..', rekursive=True):
    ...     print dirname
    ../caching
    ../fstools
    """
    logit = fstools_logit()
    l = list()
    if os.path.exists(path):
        logit.logit_debug(logger, 'path (%s) exists - looking for directories to append', path)
        for dirname in os.listdir(path):
            fulldir = os.path.join(path, dirname)
            if os.path.isdir(fulldir):
                l.append(fulldir)
                if rekursive:
                    l.extend(dirlist(fulldir))
    else:
        logit.logit_info(logger, 'path (%s) does not exist - empty filelist will be returned', path)
    return l

def is_writeable(path):
    """.. warning:: Needs to be documented
    """
    if os.access(path, os.W_OK):
        # path is writeable whatever it is, file or directory
        return True
    else:
        # path is not writeable whatever it is, file or directory
        return False

def mkdir(path):
    """.. warning:: Needs to be documented
    """
    path=os.path.abspath(path)
    if not os.path.exists(os.path.dirname(path)):
        mkdir(os.path.dirname(path))
    if not os.path.exists(path):
        os.mkdir(path)
    return os.path.isdir(path)
