import flask
import time
import urllib

STR_ARG_CACHEDATA_INDEX = 'cache_data_index'
STR_ARG_TAG_INDEX = 'tag_index'
STR_ARG_THUMB_INDEX = 'thumb_index'
STR_ARG_WEB_INDEX = 'web_index'
STR_ARG_ADMIN_ACTION = 'action'
STR_ARG_ADMIN_ACTION_COMMIT = 'commit'
STR_ARG_ADMIN_ACTION_CREATE = 'create'
STR_ARG_ADMIN_ACTION_DELETE = 'delete'
STR_ARG_ADMIN_ACTION_THUMB = 'thumb'
STR_ARG_ADMIN_CONTAINER = 'container'
STR_ARG_ADMIN_ISSUE = 'admin_issue'
STR_ARG_ADMIN_ISSUE_PERMISSION = 'permission'
STR_ARG_ADMIN_ISSUE_STAGING = 'staging'
STR_ARG_ADMIN_ISSUE_FOLDERS = 'folders'
STR_ARG_ADMIN_NAME = 'name'
STR_ARG_ADMIN_USER = 'username'
STR_ARG_ADMIN_TARGET = 'target'

def decode(string):
    for i in ['utf-8', 'cp1252']:
        try:
            return string.decode(i)
        except UnicodeEncodeError:
            pass
    return string


def encode(string):
    for i in ['utf-8', 'cp1252']:
        try:
            return string.encode(i)
        except UnicodeEncodeError:
            pass
    return string


class simple_info(object):
    def __init__(self, description, info):
        self.description = description
        self.info = info


class link(object):
    def __init__(self, url, name):
        self.url = url
        self.name = name


class piclink(link):
    def __init__(self, url, name, pic):
        link.__init__(self, url, name)
        self.pic = pic


def strargs(args):
    return '' if len(args) == 0 else '?' + '&'.join(['%s=%s' % (key, args[key]) for key in args.keys()])


class time_measurement(object):
    def __init__(self):
        self._start_time = time.time()

    def get_time_str(self):
        return 'Time consumption: %.2fs' % (time.time() - self._start_time)


def url_extention(item_name):
    if item_name:
        return '/' + urllib.quote(item_name)
    else:
        return ''
