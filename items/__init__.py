from pylibs import caching
import os
from app import base_item, prefix_slideshow
from app import base_list
from app import prefix_add_tag
from app import prefix_admin
from app import prefix_cachedataview
from app import prefix_delete
from app import prefix_info
import auth
from auth import pygal_user
from auth import rights_uid
from helpers import database_handler
from helpers import decode
from helpers import link
from helpers import piclink
from helpers import strargs
import lang
from pylibs import fstools
import urllib
import json
import pygal_config as config
import time
from pygal import logger
from pylibs import report


class base_item_props(base_item, database_handler):
    required_prop_keys = []
    prop_vers = 0.0

    def __init__(self, rel_path, request_args={}, slideshow=False, parent=None):
        base_item.__init__(self, rel_path, request_args=request_args, slideshow=slideshow, parent=parent)
        database_handler.__init__(self, self.tag_path())
        self._parent = parent
        self._prv = None
        self._nxt = None

    def is_itemlist(self):
        return False

    def add_tag_url(self, ident=None):
        add_tag_url = config.url_prefix + prefix_add_tag
        if self.url(True):
            add_tag_url += '/' + self.url(True) or ''
        if ident is not None:
            add_tag_url += '?tag_id=%s' % str(ident)
        return add_tag_url

    def tag_path(self):
        tagfile = self._rel_path.replace(os.path.sep, '_').replace(os.path.extsep, '_') + '.json'
        return os.path.join(config.database_folder, tagfile)

    def delete_url(self):
        return config.url_prefix + prefix_delete + '/' + (self.url(True) or '') + strargs(self._request_args)

    def parent(self):
        if self._parent is None:
            c = get_class_for_item(os.path.dirname(self._rel_path))
            if c is not None:
                self._parent = c(os.path.dirname(self._rel_path), request_args=self._request_args)
        return self._parent

    def nxt(self, excluded_types=[]):
        if self._nxt is None:
            parent = self.parent()
            index = parent.index_by_rel_path(self._rel_path)
            if index >= 0:
                while True:
                    index += 1
                    if index >= len(parent._itemlist):
                        index = 0
                    if type(parent._itemlist[index]) not in excluded_types:
                        self._nxt = parent._itemlist[index]
                        break
        return self._nxt

    def prv(self, excluded_types=[]):
        if self._prv is None:
            parent = self.parent()
            index = parent.index_by_rel_path(self._rel_path)
            if index >= 0:
                while True:
                    index -= 1
                    if index < 0:
                        index = len(parent._itemlist) - 1
                    if type(parent._itemlist[index]) not in excluded_types:
                        self._prv = parent._itemlist[index]
                        break
        return self._prv

    def admin_url(self):
        admin_url = config.url_prefix + prefix_admin
        if self.url(True):
            admin_url += '/' + self.url(True)
        return admin_url + self.str_request_args()

    def info_url(self):
        info_url = config.url_prefix + prefix_info
        if self.url(True):
            info_url += '/' + self.url(True)
        return info_url + self.str_request_args()

    def prop_item_path(self):
        propfile = self._rel_path.replace(os.path.sep, '_').replace(os.path.extsep, '_') + '.json'
        return os.path.join(config.iprop_folder, propfile)

    def slideshow_url(self):
        return self.base_url(prefix_slideshow) + strargs(self._request_args) + '#main'

    def is_a_searchitem(self):
        return 'q' in self._request_args


def supported_extentions():
    # TODO: reduce late imports
    from picture import picture
    from video import video
    return picture.mime_types.keys() + video.mime_types.keys()


def get_class_for_item(rel_path, force_uncached=False, force_list=False):
    bl = base_list(rel_path)
    if bl.exists() or force_list:
        if force_uncached:
            return itemlist
        else:
            return cached_itemlist
    # TODO: reduce late imports
    from picture import picture
    from video import video
    possible_item_classes = [picture, video]
    extension = os.path.splitext(rel_path)[1][1:].lower()
    for class_for_file in possible_item_classes:
        if extension in class_for_file.mime_types.keys():
            return class_for_file
    return None


class itemlist(base_list):
    exclude_keys_request_args = ['search_request']
    DATA_VERSION = 1
    PROP_LEN = 'len'
    PROP_TIME = 'time'
    PROP_RATIO_X = 'ratio_x'
    PROP_RATIO_Y = 'ratio_y'
    PROP_THUMB_URL = 'thumb_url'
    PROP_WEB_URL = 'web_url'
    PROP_WEB_Y = 'web_y'
    PROP_NUM_PICS = 'num_pics'
    PROP_NUM_VIDS = 'num_vids'
    PROP_NUM_GALS = 'num_gals'
    PROP_FILESIZE = 'filesize'
    PROPERTIES = [PROP_LEN, PROP_TIME, PROP_RATIO_X, PROP_RATIO_Y, PROP_THUMB_URL, PROP_WEB_URL, PROP_WEB_Y, PROP_NUM_PICS, PROP_NUM_VIDS, PROP_NUM_GALS, PROP_FILESIZE]

    def __init__(self, rel_path, request_args={}, parent=None, slideshow=False, create_cache=False):
        base_list.__init__(self, rel_path, request_args=request_args, parent=parent)
        self._create_cache = create_cache

    def cache_data_url(self, i):
        cu = config.url_prefix + prefix_cachedataview
        if self._rel_path:
            cu += '/' + urllib.quote(self._rel_path)
        return cu + strargs({'index': str(i)})

    def cache_data(self):
        return list()

    def tag_id_exists(self, tag_id):    # for compatibility with picture object
        return False

    def is_a_searchresult(self):
        return 'q' in self._request_args

    def exists(self):
        return base_list.exists(self) or self.is_a_searchresult()

    def name(self, *args, **kwargs):
        if self.is_a_searchresult():
            return lang.search_results % self._request_args.get('q', '')
        else:
            return base_list.name(self, *args, **kwargs)

    def __init_itemlist__(self):
        base_list.__init_itemlist__(self)
        if self.is_a_searchresult():
            search_query = self._request_args.get('q', '')
            for f in fstools.filelist(config.database_folder, '*.json'):
                t = database_handler(f)
                if t.matches(search_query):
                    c = get_class_for_item(t.get_rel_path())
                    if c:
                        item = c(t.get_rel_path(), self._request_args)
                        if item.exists():
                            if type(item) not in [itemlist, cached_itemlist]:
                                if self._create_cache or item.user_may_view():
                                    self._len += 1
                                    self._itemlist.append(item)
                            else:
                                if item.len() > 0:
                                    self._len += 1
                                    self._itemlist.append(item)
        else:
            if self.exists():
                for entry in os.listdir(self.raw_path()):
                    c = get_class_for_item(os.path.join(self._rel_path, entry))
                    if c:
                        item = c(os.path.join(self._rel_path, entry), request_args=self._request_args, parent=self, create_cache=self._create_cache)
                        if item.exists():
                            if type(item) not in [itemlist, cached_itemlist]:
                                if self._create_cache or item.user_may_view():
                                    self._len += 1
                                    self._itemlist.append(item)
                            else:
                                if item.len() > 0:
                                    self._len += 1
                                    self._itemlist.append(item)
        #
        self.sort()
        #

    def user_may_view(self):
        return self.len() > 0

    def user_may_download(self):
        return pygal_user.may_download(self)

    def user_may_delete(self):
        return pygal_user.may_delete(self)

    #
    # Methods for caching
    #
    def data_version(self):
        return self.DATA_VERSION

    def get(self, key, default=None):
        if self._itemlist is None:
            self.__init_itemlist__()
        if key == self.PROP_LEN:
            return self._len
        elif key == self.PROP_TIME:
            if len(self._itemlist) > 0:
                return self._itemlist[0].time()
        elif key == self.PROP_RATIO_X:
            if len(self._itemlist) > 0:
                return self._itemlist[0].ratio_x()
        elif key == self.PROP_RATIO_Y:
            if len(self._itemlist) > 0:
                return self._itemlist[0].ratio_y()
        elif key == self.PROP_THUMB_URL:
            if len(self._itemlist) > 0:
                return self._itemlist[0].thumbnail_url()
        elif key == self.PROP_WEB_URL:
            if len(self._itemlist) > 0:
                return self._itemlist[0].webnail_url()
        elif key == self.PROP_WEB_Y:
            if len(self._itemlist) > 0:
                return self._itemlist[0].webnail_y()
        elif key == self.PROP_NUM_PICS:
            p = 0
            for entry in self._itemlist:
                p += entry.num_pic()
            return p
        elif key == self.PROP_NUM_VIDS:
            v = 0
            for entry in self._itemlist:
                v += entry.num_vid()
            return v
        elif key == self.PROP_NUM_GALS:
            g = 1
            for entry in self._itemlist:
                g += entry.num_gal()
            return g
        elif key == self.PROP_FILESIZE:
            fs = 0
            for entry in self.itemlist():
                fs += entry.filesize()
            return fs
        return default

    def keys(self):
        return self.PROPERTIES

    def prop_item_path(self, user=None):
        if user is None:
            propfile = self._rel_path.replace(os.path.sep, '_').replace(os.path.extsep, '_') + '_' + (pygal_user.get_session_user() or '').encode('utf-8') + '.json'
        else:
            propfile = self._rel_path.replace(os.path.sep, '_').replace(os.path.extsep, '_') + '_' + (user).encode('utf-8') + '.json'
        return os.path.join(config.iprop_folder, propfile)

    def uid(self):
        return fstools.uid(self.raw_path()) + '_' + rights_uid(pygal_user.get_session_user())

    #
    # Cached Properties
    #
    def filesize(self):
        return self.get(self.PROP_FILESIZE, 0)

    def len(self):
        return self.get(self.PROP_LEN, 0)

    def num_gal(self):
        return self.get(self.PROP_NUM_GALS)

    def num_pic(self):
        return self.get(self.PROP_NUM_PICS)

    def num_vid(self):
        return self.get(self.PROP_NUM_VIDS)

    def thumbnail_url(self):
        return self.get(self.PROP_THUMB_URL)

    def webnail_url(self):
        return self.get(self.PROP_WEB_URL)

    def webnail_y(self):
        return self.get(self.PROP_WEB_Y)

    def ratio_x(self):
        return self.get(self.PROP_RATIO_X, 1.0)

    def ratio_y(self):
        return self.get(self.PROP_RATIO_Y, 1.0)

    def time(self):
        return self.get(self.PROP_TIME, 0)

    #
    # Further Methods
    #
    def thumbnail_xy_max(self):
        return pygal_user.get_thumbnail_size()

    def thumbnail_x(self):
        return self.ratio_x() * self.thumbnail_xy_max()

    def thumbnail_y(self):
        return self.ratio_y() * self.thumbnail_xy_max()

    def actions(self):
        rv = list()
        rv.append(piclink(self.info_url(), 'Info', config.url_prefix + '/static/common/img/info.png'))
        if self.user_may_download():
            rv.append(piclink(self.download_url(), 'Download', config.url_prefix + '/static/common/img/download.png'))
        return rv

    def strfilesize(self, size=None):
        unit = {0: 'Byte', 1: 'kB', 2: 'MB', 3: 'GB', 4: 'TB'}
        size = size or self.filesize()
        u = 0
        while size > 1000.:
            size /= 1024.
            u += 1
        return '%.1f %s' % (size, unit[u])

    def get_infos(self):
        infos = list()

        def add_info(desc, info):
            if info is not None:
                infos.append([desc, info])

        add_info('Name:', self.name(True) or 'Root')
        add_info('Galeries:', '%d' % (self.num_gal()))
        add_info('Datavolume:', self.strfilesize())
        add_info('Pictures:', '%d' % self.num_pic())
        add_info('Videos:', '%d' % self.num_vid())
        return infos

    def admin_url(self):
        admin_url = config.url_prefix + prefix_admin
        if self.url(True):
            admin_url += '/' + self.url(True)
        return admin_url + self.str_request_args()

    def info_url(self):
        info_url = config.url_prefix + prefix_info
        if self.url(True):
            info_url += '/' + self.url(True)
        return info_url + self.str_request_args()

    def itemlist(self):
        if self._itemlist is None:
            self.__init_itemlist__()
        return self._itemlist

    def template(self):
        return 'overview.html'

    def strtime(self):
        tm = self.time()
        if tm is None:
            return ''
        return time.strftime("%d.%m.%Y - %H:%M:%S", time.gmtime(self.time()))

    def sort(self):
        def my_cmp(x, y):
            if x.time() > y.time():
                return 1
            elif y.time() > x.time():
                return -1
            elif x.name() > y.name():
                return 1
            elif y.name() > x.name():
                return -1
            else:
                return 0

        if self._itemlist is None:
            self.__init_itemlist__()
        self._itemlist.sort(cmp=my_cmp, reverse=True)

    def create_thumbnail(self):
        for item in self.itemlist():
            item.create_thumbnail()

    def create_webnail(self):
        for item in self.itemlist():
            item.create_webnail()


class cached_itemlist(itemlist, report.logit):
    LOG_PREFIX = 'cached_il:'

    def __init__(self, *args, **kwargs):
        itemlist.__init__(self, *args, **kwargs)
        if not self._create_cache:
            self._cached_data = caching.property_cache_json(itemlist(*args, **kwargs), self.prop_item_path(), load_all_on_init=True)

    def get(self, key, default=None):
        if not self._create_cache:
            self.logit_debug(logger, "Property request (%s) for %s", key, self.name())
            return self._cached_data.get(key, default, logger=logger)
        else:
            return itemlist.get(self, key, default)

    def cache_data(self):
        rv = list()
        users = [''] + auth.user_data_handler().users()
        for i in range(0, len(users)):
            entry = list()
            entry.append('Item data (%s)' % users[i])
            entry.append(decode(self.prop_item_path(users[i])))
            rv.append(entry)
        # Add Link
        for i in range(0, len(rv)):
            rv[i].append(self.cache_data_url(i))
        return rv
