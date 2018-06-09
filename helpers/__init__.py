import mail

import flask
import menu
import os
import pygal_config as config
import time
import urllib
from pylibs import fstools

STR_ARG_CACHEDATA_INDEX = 'cache_data_index'
STR_ARG_TAG_INDEX = 'tag_index'
STR_ARG_THUMB_INDEX = 'thumb_index'
STR_ARG_WEB_INDEX = 'web_index'

STR_ARG_ACTION = 'action'
STR_ARG_ADMIN_ACTION_COMMIT = 'commit'
STR_ARG_ADMIN_ACTION_CREATE = 'create'
STR_ARG_ADMIN_ACTION_DELETE = 'delete'
STR_ARG_ADMIN_ACTION_THUMB = 'thumb'
STR_ARG_DOWNLOAD_ACTION_FLAT = 'flat'

STR_ARG_ADMIN_CONTAINER = 'container'
STR_ARG_ADMIN_ISSUE = 'admin_issue'
STR_ARG_ADMIN_ISSUE_PERMISSION = 'permission'
STR_ARG_ADMIN_ISSUE_STAGING = 'staging'
STR_ARG_ADMIN_ISSUE_FOLDERS = 'folders'
STR_ARG_ADMIN_NAME = 'name'
STR_ARG_ADMIN_USER = 'username'
STR_ARG_ADMIN_TARGET = 'target'
STR_ARG_FAVOURITE = 'action'
STR_ARG_FAVOURITE_ADD = 'add'
STR_ARG_FAVOURITE_REMOVE = 'remove'
STR_ARG_REDIRECT_PARENT = 'parent'

def full_url():
    return urllib.quote(encode(flask.request.url))

def db_filename_by_relpath(db_path, rel_path):
    return os.path.join(db_path, rel_path + '.json')

def info_filename_by_relpath(rel_path):
    uid = fstools.uid(os.path.join(config.item_path, rel_path))
    return os.path.join(config.cache_path, uid + '_info.json')

def decode(string):
    for i in ['utf-8', 'cp1252']:
        try:
            return string.decode(i)
        except UnicodeEncodeError:
            pass
        except UnicodeDecodeError:
            pass
    return string


def encode(string):
    for i in ['utf-8', 'cp1252']:
        try:
            return string.encode(i)
        except UnicodeEncodeError:
            pass
        except UnicodeDecodeError:
            pass
    return string


class simple_info(object):
    def __init__(self, description, info):
        self.description = description
        self.info = info


class link(object):
    def __init__(self, url, name):
        self.url = urllib.quote(encode(url)) if url is not None else None
        self.name = name


class piclink(link):
    def __init__(self, url, name, icon):
        link.__init__(self, url, name)
        self.icon = icon


def strargs(args):
    return '' if len(args) == 0 else '?' + '&'.join([('%s=%s' if args[key] != ''  else '%s%s') % (key, urllib.quote(str(args[key]))) for key in args.keys()])


class time_measurement(object):
    def __init__(self):
        self._start_time = time.time()

    def get_time_str(self):
        return 'Time consumption: %.2fs' % (time.time() - self._start_time)


def url_extention(item_name):
    if item_name:
        return '/' + urllib.quote(encode(item_name))
    else:
        return ''
