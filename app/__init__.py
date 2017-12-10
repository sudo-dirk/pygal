from auth import pygal_user
import flask
from pylibs import fstools
import os
import shutil
import pygal_config as config

prefix_add_tag = '/_add_tag_'                       # items
prefix_delete = '/_delete_'                         # items
prefix_download = '/_download_'                     # items
prefix_info = '/_info_'                             # items
prefix_login = '/_login_'                           # base_func
prefix_logout = '/_logout_'                         # base_func
prefix_lostpass = '/_lostpass_'                     # base_func
prefix_raw = '/_raw_'                               # items
prefix_register = '/_register_'                     # base_func
prefix_slideshow = '/_slideshow_'                   # items
prefix_thumbnail = '/_thumbnail_'                   # items
prefix_userprofile = '/_userprofile_'               # base_func
prefix_webnail = '/_webnail_'                       # items


def strargs(args):
    if len(args) == 0:
        return ''
    else:
        rv = '?'
        for key in args:
            rv += key
            if args.get(key):
                rv += '=' + args[key]
            rv += '&'
        return decode(rv[:-1])


def url_extention(item_name):
    if item_name:
        return '/' + decode(item_name)
    else:
        return ''


class base_item(object):
    mime_types = {}
    default_mime_type = 'text/plain'

    def __init__(self, rel_path, request_args={}, slideshow=False, parent=None):
        self._rel_path = rel_path
        self._request_args = request_args
        self._slideshow = slideshow

    def str_request_args(self):
        strargs(self._request_args)

    def rel_path(self):
        return self._rel_path

    def base_url(self, flask_prefix = ''):
        return config.url_prefix + flask_prefix + '/' + decode(self._rel_path)

    def delete(self):
        shutil.move(self.raw_path(), self.delete_path())

    def delete_path(self):
        return os.path.join(config.trash_path, self._rel_path.replace(os.path.sep, '_'))

    def download_url(self):
        du = config.url_prefix + prefix_download
        if self._rel_path:
            du += '/' + decode(self._rel_path)
        return du

    def exists(self):
        return os.path.isfile(self.raw_path())

    def index_by_rel_path(self, rel_path):
        for index in range(0, len(self)):
            if rel_path == self[index]._rel_path:
                return index
        return -1

    def mime_type(self):
        try:
            return self.mime_types[self.raw_ext()]
        except:
            return self.default_mime_type

    def name(self, full_name=False):
        name = decode(os.path.basename(self._rel_path))
        if full_name:
            return name
        else:
            return os.path.splitext(name)[0]

    def navigation_list(self):
        rv = list()
        rel_url = self.url(True)
        while os.path.basename(rel_url):
            rv.insert(0, link(os.path.join(config.url_prefix or '/', rel_url), os.path.basename(rel_url)))
            rel_url = os.path.dirname(rel_url)
        return rv

    def raw_ext(self):
        return os.path.splitext(self.raw_path())[1][1:].lower()

    def raw_path(self):
        return os.path.join(config.basepath, config.item_folder, self._rel_path)

    def raw_url(self):
        return config.url_prefix + prefix_raw + '/' + decode(self._rel_path) or ''

    def filesize(self):
        return os.path.getsize(self.raw_path())

    def parent_url(self):
        return config.url_prefix + '/' + decode(os.path.dirname(self._rel_path)) + strargs(self._request_args)

    def strfilesize(self):
        unit = {0: 'Byte', 1: 'kB', 2: 'MB', 3: 'GB', 4: 'TB'}
        size = self.filesize()
        u = 0
        while size > 1000.:
            size /= 1024.
            u += 1
        return '%.1f %s' % (size, unit[u])

    def slideshow(self):
        return self._slideshow

    def uid(self):
        return fstools.uid(self.raw_path())

    def url(self, relative=False):
        if relative:
            return decode(self._rel_path)
        else:
            return self.base_url() + strargs(self._request_args)

    def user_may_view(self):
        return pygal_user.may_view(self)

    def user_may_delete(self):
        return pygal_user.may_delete(self)

    def user_may_download(self):
        return pygal_user.may_download(self)


class base_list(object):
    mime_types = {'': 'folder'}

    def __init__(self, rel_path, request_args={}, parent=None):
        self._rel_path = rel_path
        self._parent = parent
        self._itemlist = None
        self._len = None
        self._request_args = request_args

    def __init_itemlist__(self):
        self._itemlist = list()
        self._len = 0

    def str_request_args(self):
        return strargs(self._request_args)

    def download_url(self):
        du = config.url_prefix + prefix_download
        if self._rel_path:
            du += '/' + decode(self._rel_path)
        du += self.str_request_args()
        return du

    def base_url(self, flask_prefix = ''):
        return config.url_prefix + flask_prefix + '/' + decode(self._rel_path)

    def exists(self):
        return os.path.isdir(self.raw_path())

    def list_holding_rel_path(self, rel_path):
        for item in self._itemlist:
            if rel_path == item._rel_path:
                return self
            try:
                return item.item_by_rel_path(rel_path)
            except AttributeError:
                pass  # seems to be not an base_list_object

    def index_by_rel_path(self, rel_path):
        for ind in range(0, len(self.itemlist())):
            if rel_path == self._itemlist[ind]._rel_path:
                return ind
        return -1

    def name(self, full_name=False):
        name = decode(os.path.basename(self._rel_path))
        if full_name:
            return name
        else:
            return os.path.splitext(name)[0]

    def navigation_list(self):
        rv = list()
        rel_url = self.url(True)
        while os.path.basename(rel_url):
            rv.insert(0, link(os.path.join(config.url_prefix or '/', rel_url), os.path.basename(rel_url)))
            rel_url = os.path.dirname(rel_url)
        return rv

    def raw_path(self):
        return os.path.join(config.basepath, config.item_folder, self._rel_path)

    def slideshow(self):
        return False

    def url(self, relative=False):
        if relative:
            return decode(self._rel_path)
        else:
            return config.url_prefix + '/' + decode(self._rel_path) + strargs(self._request_args)


class collector(object):
    def __init__(self, **kwds):
        for key in kwds:
            setattr(self, key, kwds[key])

    def has_attr(self, name):
        return hasattr(self, name)

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


class link(object):
    def __init__(self, url, name):
        self.url = url
        self.name = name


class piclink(link):
    def __init__(self, url, name, pic):
        link.__init__(self, url, name)
        self.pic = pic
