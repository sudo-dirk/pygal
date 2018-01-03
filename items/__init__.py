from pylibs import caching
import os
from app import base_item, prefix_slideshow
from app import base_list
from app import prefix_add_tag
from app import prefix_admin
from app import prefix_delete
from app import prefix_info
from helpers import link
from helpers import piclink
from helpers import strargs
from auth import rights_uid
from auth import pygal_user
import lang
from pylibs import fstools
import json
import pygal_config as config
import time
from pygal import logger
from pylibs import report


class tags(dict):
    DATA_ID = '_common_'

    def __init__(self, tag_path):
        self._id = 0
        self._tag_path = tag_path
        try:
            dict.__init__(self, json.loads(open(self._tag_path, 'r').read()))
            for ident in self:
                if int(ident) > self._id:
                    self._id = int(ident)
        except:
            dict.__init__(self)
        else:
            if self.DATA_ID not in self:
                self[self.DATA_ID] = dict()
                try:
                    self[self.DATA_ID]['rel_path'] = self.rel_path()
                except:
                    pass
                else:
                    self._save_tags()

    def get_rel_path(self):
        return self.get(self.DATA_ID, {}).get('rel_path', '')

    def matches(self, query):
        for tag_id in self.get_tag_id_list():
            if query.lower() in self.get_tag_text(tag_id).lower():
                return True
        return False

    def tag_id_exists(self, tag_id):
        return tag_id in self and tag_id != self.DATA_ID

    def get_tag_id_list(self):
        rv = self.keys()
        if self.DATA_ID in rv:
            rv.remove(self.DATA_ID)
        rv.sort()
        return rv

    def get_tag_wn_x(self, tag_id):
        try:
            return int(self[tag_id]['x'] * self.webnail_x())
        except:
            return ''

    def get_tag_wn_y(self, tag_id):
        try:
            return int(self[tag_id]['y'] * self.webnail_y())
        except:
            return ''

    def get_tag_wn_w(self, tag_id):
        try:
            return int(self[tag_id]['w'] * self.webnail_x())
        except:
            return ''

    def get_tag_wn_h(self, tag_id):
        try:
            return int(self[tag_id]['h'] * self.webnail_y())
        except:
            return ''

    def get_tag_wn_x2(self, tag_id):
        try:
            return self.get_tag_wn_x(tag_id) + self.get_tag_wn_w(tag_id)
        except:
            return ''

    def get_tag_wn_y2(self, tag_id):
        try:
            return self.get_tag_wn_y(tag_id) + self.get_tag_wn_h(tag_id)
        except:
            return ''

    def get_tag_text(self, tag_id):
        try:
            return self[tag_id]['tag']
        except:
            return ''

    def get_tag_icon(self, tag_id):
        return config.url_prefix + '/static/common/img/%d.png' % (int(tag_id) % 10)

    def add_tag_wn(self, tag, ident=None):
        tag_dict = dict()
        tag_dict['tag'] = tag
        if ident is None:
            self._id += 1
            self[str(self._id)] = tag_dict
        else:
            self[str(ident)] = tag_dict
        self._save_tags()

    def add_tag_wn_xywh(self, x, y, w, h, tag, ident=None):
        tag_dict = dict()
        tag_dict['x'] = float(x) / self.webnail_x()
        tag_dict['y'] = float(y) / self.webnail_y()
        tag_dict['w'] = float(w) / self.webnail_x()
        tag_dict['h'] = float(h) / self.webnail_y()
        tag_dict['tag'] = tag
        if ident is None:
            self._id += 1
            self[str(self._id)] = tag_dict
        else:
            self[str(ident)] = tag_dict
        self._save_tags()

    def add_tag_wn_x1y1x2y2(self, x1, y1, x2, y2, tag_text, tag_id=None):
        self.add_tag_wn_xywh(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1), tag_text, tag_id)

    def delete_tag(self, tag_id):
        if self.tag_id_exists(tag_id):
            del self[tag_id]
            self._save_tags()

    def _save_tags(self):
        if self._tag_path is not None:
            with open(self.tag_path(), 'w') as fh:
                fh.write(json.dumps(self, indent=3, sort_keys=True))

    def tag_has_coordinates(self, tag_id):
        if self.get_tag_wn_x(tag_id) == '':
            return False
        if self.get_tag_wn_y(tag_id) == '':
            return False
        if self.get_tag_wn_w(tag_id) == '':
            return False
        if self.get_tag_wn_h(tag_id) == '':
            return False
        return True


class base_item_props(base_item, tags):
    required_prop_keys = []
    prop_vers = 0.0

    def __init__(self, rel_path, request_args={}, slideshow=False, parent=None):
        base_item.__init__(self, rel_path, request_args=request_args, slideshow=slideshow, parent=parent)
        tags.__init__(self, self.tag_path())
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
        tagfile = os.path.splitext(self._rel_path)[0].replace(os.path.sep, '_') + '.json'
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
        propfile = os.path.splitext(self._rel_path)[0].replace(os.path.sep, '_') + '.prop'
        return os.path.join(config.iprop_folder, propfile)

    def slideshow_url(self):
        return self.base_url(prefix_slideshow) + strargs(self._request_args) + '#main'

    def is_a_searchitem(self):
        return 'q' in self._request_args


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
                t = tags(f)
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

    def prop_item_path(self):
        propfile = os.path.splitext(self._rel_path)[0].replace(os.path.sep, '_') + '_' + (pygal_user.get_session_user() or 'None').encode('utf-8') + '.prop'
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
