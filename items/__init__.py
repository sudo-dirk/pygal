from pylibs import caching
import auth
from auth import pygal_user, session_data_handler
from auth import rights_uid
from database import database_handler
from database import indexed_search
import flask
import helpers
from helpers import encode
from helpers import decode
from helpers import piclink
from helpers import simple_info
from helpers import strargs
import lang
import logging
from pylibs.multimedia.picture import picture_info
from pylibs.multimedia.video import video_info
import os
from prefixes import prefix_add_tag
from prefixes import prefix_admin
from prefixes import prefix_delete
from prefixes import prefix_download
from prefixes import prefix_help
from prefixes import prefix_info
from prefixes import prefix_login
from prefixes import prefix_logout
from prefixes import prefix_lostpass
from prefixes import prefix_raw
from prefixes import prefix_register
from prefixes import prefix_slideshow
from prefixes import prefix_thumbnail
from prefixes import prefix_upload
from prefixes import prefix_userprofile
from prefixes import prefix_webnail
from pylibs import fstools
from pylibs import report
import shutil
import urllib
import uuid
import json
import pygal_config as config
import time
from sys import path


logger = logging.getLogger('pygal.items')


TYPE_ITEMLIST = 0
TYPE_BASEITEM = 1
TYPE_PICTURE = 2
TYPE_STAGING_BASEITEM = 3
TYPE_STAGING_PICVID = 4
TYPE_STAGING_ITEMLIST = 5
TYPE_VIDEO = 6


TYPE_NAMES = {
    TYPE_ITEMLIST: 'Galerries',
    TYPE_BASEITEM: 'Other Files',
    TYPE_PICTURE: 'Pictures',
    TYPE_VIDEO: 'Videos'
    }


def supported_extentions():
    from .picture import picture
    from .video import video
    return picture.mime_types.keys() + video.mime_types.keys()


def get_item_by_path(rel_path, base_path, slideshow, db_path, cache_path, force_user):
    from .picture import picture
    from .video import video

    path = os.path.join(base_path, rel_path)
    ext = os.path.splitext(path)[1][1:].lower()
    bil = itemlist(rel_path, base_path, slideshow, db_path, cache_path, force_user)
    if bil.exists():
        return bil
    possible_item_classes = [picture, video]
    for class_for_file in possible_item_classes:
        if ext in class_for_file.mime_types.keys():
            return class_for_file(rel_path, base_path, slideshow, db_path, cache_path, force_user)
    if config.multimedia_only:
        return None
    else:
        return base_item(rel_path, base_path, slideshow, db_path, cache_path, force_user)


def get_staging_item_by_path(rel_path, base_path, slideshow, db_path, cache_path, force_user):
    (slideshow, db_path, cache_path, force_user)  # unused paramter for compatibility with get_item_by_path
    bil = staging_itemlist(rel_path, base_path, False, None)
    if bil.exists() and not rel_path:
        return bil
    if os.path.splitext(rel_path)[1][1:] in supported_extentions():
        return staging_picviditem(rel_path, base_path, False, None, None, None)
    if config.multimedia_only:
        return None
    else:
        return staging_baseitem(rel_path, base_path, False, None, None, None)


class staging_container(report.logit, dict):
    LOG_PREFIX = 'StageCont:'
    CONTAINER_INFO_FILE_EXTENTION = 'json'

    KEY_UUID = '_uuid_'
    KEY_CONTAINERNAME = '_container_name_'
    KEY_FILES = '_files'
    KEYS = [KEY_UUID, KEY_CONTAINERNAME]

    def __init__(self, staging_path, uuid_for_container, name, allowed_extentions):
        dict.__init__(self)
        self._staging_path = staging_path
        if uuid_for_container is None:
            self[self.KEY_UUID] = str(uuid.uuid4())
        else:
            self[self.KEY_UUID] = uuid_for_container
        self[self.KEY_CONTAINERNAME] = name
        self[self.KEY_FILES] = {}
        self._allowed_extentions = allowed_extentions
        self.load()


    def append_file_upload(self, file_storage, database):
        container_folder = os.path.dirname(self.get_container_file_path('dummy'))
        if not os.path.exists(container_folder):
            os.mkdir(container_folder)
        if self.is_allowed(file_storage.filename):
            file_storage.save(self.get_container_file_path(file_storage.filename))
            self[self.KEY_FILES][file_storage.filename] = database.get_database_content()
            self.save()
            return True
        return False

    def append_file_delete(self, filename, database):
        container_folder = os.path.dirname(self.get_container_file_path('dummy'))
        if not os.path.exists(container_folder):
            os.mkdir(container_folder)
        if os.path.exists(filename) and self.is_allowed(filename):
            print type(filename), filename
            print type(os.path.basename(filename)), os.path.basename(filename)
            shutil.copyfile(filename, self.get_container_file_path(os.path.basename(filename)))
            self[self.KEY_FILES][os.path.basename(filename)] = database
            self.save()

    def delete(self):
        shutil.rmtree(os.path.dirname(self.get_container_file_path('dummy')))
        os.remove(self.get_container_info_file_by_uuid(self[self.KEY_UUID]))

    def get_container_file_path(self, filename):
        if self._staging_path is None or self[self.KEY_UUID] is None:
            return None
        else:
            return os.path.join(self._staging_path, encode(self[self.KEY_UUID]), filename)

    def get_container_info_file_by_uuid(self, uuid):
        if self._staging_path is None or uuid is None:
            return None
        else:
            return os.path.join(self._staging_path, encode(uuid) + '.' + self.CONTAINER_INFO_FILE_EXTENTION)

    def get_container_name(self):
        return self.get(self.KEY_CONTAINERNAME)

    def get_uuid(self):
        return self.get(self.KEY_UUID)

    def is_allowed(self, filename):
        if self._allowed_extentions is None:
            return True
        else:
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in self._allowed_extentions:
                return True
        return False

    def is_empty(self):
        return len(self[self.KEY_FILES]) == 0

    def load(self):
        cif = self.get_container_info_file_by_uuid(self.get(self.KEY_UUID))
        if cif is not None and os.path.exists(cif):
            with open(cif, 'r') as fh:
                data = json.loads(fh.read())
            dict.__init__(self, data)

    def move(self, items_target_path, database_path, item_path):
        # iteration over files
        for filename in self[self.KEY_FILES].copy():
            database_filename = os.path.join(database_path, os.path.join(items_target_path, encode(filename)).replace(os.path.sep, '_').replace(os.path.extsep, '_') + '.json')
            item_filename = os.path.join(item_path, items_target_path, encode(filename))
            if not os.path.exists(database_filename) and not os.path.exists(item_filename) and fstools.is_writeable(os.path.dirname(database_filename)) and fstools.is_writeable(os.path.dirname(item_filename)):
                dbh = database_handler(database_filename, os.path.join(items_target_path, encode(filename)))
                dbh._init_database_(self[self.KEY_FILES][filename])
                self.logit_info(logger, 'Moving File %s to %s.', self.get_container_file_path(encode(filename)), item_filename)
                os.rename(self.get_container_file_path(encode(filename)), item_filename)
                del self[self.KEY_FILES][filename]
        if self.is_empty():
            self.delete()
        else:
            self.save()

    def save(self):
        cif = self.get_container_info_file_by_uuid(self.get(self.KEY_UUID))
        if cif is not None and len(self) > 0:
            # generate container_info_file
            with open(cif, 'w') as fh:
                fh.write(json.dumps(self, indent=4, sort_keys=True))


class gallery_urls(object):
    def _url(self, prefix=''):
            return config.url_prefix + prefix + ('/' + urllib.quote(self._rel_path) if self._rel_path else '')
        
    def item_url(self):
        return self._url()

    def add_tag_url(self, i=None):
        return self._url(prefix_add_tag) + strargs({} if i is None else {helpers.STR_ARG_TAG_INDEX: i})

    def admin_url(self, args={}):
        return self._url(prefix_admin) + strargs(args)

    def delete_url(self):
        return self._url(prefix_delete)

    def download_url(self):
        return self._url(prefix_download)

    def help_url(self, rel_path):
        return config.url_prefix + prefix_help + ('/' + rel_path if rel_path else '')

    def info_url(self, i=None):
        return self._url(prefix_info) + strargs({} if i is None else {helpers.STR_ARG_CACHEDATA_INDEX: i})

    def login_url(self):
        return self._url(prefix_login)

    def logout_url(self):
        return self._url(prefix_logout)

    def lostpass_url(self):
        return self._url(prefix_lostpass)

    def parent_url(self):
        return config.url_prefix + '/' + urllib.quote(os.path.dirname(self._rel_path))

    def register_url(self):
        return self._url(prefix_register)

    def raw_url(self):
        return self._url(prefix_raw)

    def slideshow_url(self):
        return self._url(prefix_slideshow) + '#main'

    def thumbnail_url(self, i=None):
        i = auth.session_data_handler().get_thumbnail_index() if i is None else i
        return self._url(prefix_thumbnail) + strargs({helpers.STR_ARG_THUMB_INDEX: i})

    def upload_url(self):
        return self._url(prefix_upload)

    def userprofile_url(self):
        return self._url(prefix_userprofile)

    def webnail_url(self, i=None):
        i = auth.session_data_handler().get_webnail_index() if i is None else i
        return self._url(prefix_webnail) + strargs({helpers.STR_ARG_WEB_INDEX: i})


class base_object(report.logit, gallery_urls):
    LOG_PREFIX = 'BaseObj:'
    ICON_SIZE = 128
    TYPE = None

    def __init__(self, rel_path, base_path, slideshow, force_user):
        self._rel_path = rel_path
        self._base_path = base_path
        self._slideshow = slideshow
        self._force_user = force_user
        self._get_item_by_path = get_item_by_path

    def __len__(self):
        return 1 if self.exists() else 0

    def actions(self):
        rv = list()
        rv.append(piclink(self.info_url(), 'Info', config.url_prefix + '/static/common/img/info.png'))
        if self.user_may_download():
            rv.append(piclink(self.download_url(), 'Download', config.url_prefix + '/static/common/img/download.png'))
        return rv

    def download_url(self):
        return gallery_urls.download_url(self) + (strargs({'q': flask.request.args.get('q')}) if self.is_a_searchresult() else '')

    def exists(self):
        return os.path.isfile(self.raw_path())

    def get_infos(self):
        infos = list()
        infos.append(simple_info('Name:', self.name(True) or 'Root'))
        infos.append(simple_info('Size:', self.strfilesize()))
        return infos

    def has_cache_data(self):
        return False

    def is_a_searchresult(self):
        try:
            return 'q' in flask.request.args
        except RuntimeError:
            # it seems to be the cache generation from command line
            return False

    def is_baseitem(self):
        return self.TYPE == TYPE_BASEITEM

    def is_itemlist(self):
        return self.TYPE == TYPE_ITEMLIST

    def is_picture(self):
        return self.TYPE == TYPE_PICTURE

    def is_video(self):
        return self.TYPE == TYPE_VIDEO

    def item_url(self):
        return gallery_urls.item_url(self) + (strargs({'q': flask.request.args.get('q')}) if self.is_a_searchresult() else '')

    def name(self, full_name=False):
        name = decode(os.path.basename(self._rel_path))
        if full_name:
            return name or 'Root'
        else:
            return os.path.splitext(name)[0] or 'Root'

    def raw_path(self):
        return os.path.join(self._base_path, self._rel_path)

    def slideshow(self):
        return self._slideshow

    def slideshow_url(self):
        return self._url(prefix_slideshow) + (strargs({'q': flask.request.args.get('q')}) if self.is_a_searchresult() else '') + '#main'

    def stay_time(self):
        return '4'

    def strfilesize(self, size=None):
        unit = {0: 'Byte', 1: 'kB', 2: 'MB', 3: 'GB', 4: 'TB'}
        size = size or self.filesize()
        u = 0
        while size > 1000.:
            size /= 1024.
            u += 1
        return '%.1f %s' % (size, unit[u])

    def strtime(self):
        tm = self.time()
        if tm is None:
            return ''
        return time.strftime("%d.%m.%Y - %H:%M:%S", time.gmtime(self.time()))

    def thumbnail_x(self):
        return self.ICON_SIZE

    def thumbnail_xy_max(self):
        return self.ICON_SIZE

    def thumbnail_y(self):
        return self.ICON_SIZE

    def time(self):
        return os.path.getctime(self.raw_path())

    def user_may_admin(self):
        return pygal_user.may_admin(self)

    def user_may_delete(self):
        return pygal_user.may_delete(self)

    def user_may_download(self):
        return pygal_user.may_download(self)

    def user_may_edit(self):
        return pygal_user.may_edit(self)

    def user_may_upload(self):
        return pygal_user.may_upload(self)

    def user_may_view(self):
        return pygal_user.may_view(self)


class base_item(base_object, database_handler):
    LOG_PREFIX = 'BaseItem:'
    TYPE = TYPE_BASEITEM

    def __init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user):
        base_object.__init__(self, rel_path, base_path, slideshow, force_user)
        if db_path is not None:
            database_handler.__init__(self, helpers.db_filename_by_relpath(db_path, rel_path), rel_path)
        else:
            database_handler.__init__(self, None, rel_path)
        self._db_path = db_path
        self._cache_path = cache_path

    def actions(self):
        rv = base_object.actions(self)
        if self.user_may_edit():
            rv.append(piclink(self.add_tag_url(), 'Add Tag', config.url_prefix + '/static/common/img/edit.png'))
        if self.slideshow():
            rv.append(piclink(self.item_url(), 'Stop Slideshow', config.url_prefix + '/static/common/img/stop_slideshow.png'))
        else:
            rv.append(piclink(self.slideshow_url(), 'Start Slideshow', config.url_prefix + '/static/common/img/start_slideshow.png'))
        if self.user_may_delete():
            rv.append(piclink(self.delete_url(), 'Delete', config.url_prefix + '/static/common/img/delete.png'))
        return rv

    def cache_data(self):
        rv = list()
        entry = list()
        entry.append('User data')
        entry.append(decode(self._db_filename))
        rv.append(entry)
        # Add Link
        for i in range(0, len(rv)):
            rv[i].append(self.info_url(i))
        return rv


    def count(self, d):
        d[self.TYPE] += 1
        return d

    def delete(self):
        if self.user_may_delete():
            isearch = indexed_search()
            isearch.delete_document_by_rel_path(self._rel_path)
            if os.path.exists(self.raw_path()):
                os.remove(self.raw_path())
            if os.path.exists(self._db_filename):
                os.remove(self._db_filename)

    def filesize(self):
        return os.path.getsize(self.raw_path())

    def get_infos(self):
        infos = base_object.get_infos(self)
        infos.append(simple_info('Itemdate:', self.strtime()))
        if self._db_filename is not None:
            infos.append(simple_info('Uploaddate:', self.get_upload_strtime()))
            infos.append(simple_info('Uploaduser:', self.get_upload_user()))
            infos.append(simple_info('Upload IP:', self.get_upload_src_ip()))
        return infos

    def has_cache_data(self):
        return True

    def parent(self):
        return self._get_item_by_path(os.path.dirname(self._rel_path), self._base_path, self._slideshow, self._db_path, self._cache_path, self._force_user)

    def nxt(self):
        return self.parent().get_nxt(self)

    def prv(self):
        return self.parent().get_prv(self)

    def thumbnail_url(self, i=None):
        (i)
        mapping_dict = {
            'txt': 'text-plain.png', 'py': 'text-x-python.png', 'log': 'text-x-log.png', 'tex': 'text-x-tex.png', 'csv': 'text-csv.png',
            'pdf': 'application-pdf.png', 'doc': 'application-msword.png', 'docx': 'application-msword.png', 'xls': 'application-vnd.ms-excel.png',
            'xlsx': 'application-vnd.ms-excel.png', 'ppt': 'application-vnd.ms-powerpoint.png', 'pptx': 'application-vnd.ms-powerpoint.png',
            'tar': 'application-x-tar.png', 'tgz': 'application-x-compressed-tar.png', 'gz': 'application-x-gzip.png', 'zip': 'application-zip.png', '7z': 'application-x-7z-compressed.png',
            'mp3': 'audio-x-generic.png',
            'exe': 'application-x-executable.png',
            'ics': 'x-office-calendar.png', ' adr?': 'x-office-address-book.png',
            'jpg': 'application-x-egon.png', 'jpe': 'application-x-egon.png', 'jpeg': 'application-x-egon.png', 'tif': 'application-x-egon.png','tiff': 'application-x-egon.png',            
            'gif': 'application-x-egon.png', 'png': 'application-x-egon.png',
            'mp4': 'video-x-generic.png', 'avi': 'video-x-generic.png', 'mpg': 'video-x-generic.png', 'mpeg': 'video-x-generic.png','mpe': 'video-x-generic.png',            
            'mov': 'video-x-generic.png', 'qt': 'video-x-generic.png', 'webm': 'video-x-generic.png', 'mpeg': 'video-x-generic.png', 'ogv': 'video-x-generic.png',            
            'flv': 'video-x-generic.png', '3gp': 'video-x-generic.png'            
            }
        ext = os.path.splitext(self._rel_path)[1][1:].lower()
        return config.url_prefix + '/static/common/mimetype_icons/%s' % mapping_dict.get(ext, 'application-octet-stream.png')

    def webnail_url(self, i=None):
        return self.thumbnail_url(i)


class __itemlist__(base_object):
    LOG_PREFIX = 'Itemlist:'
    TYPE = TYPE_ITEMLIST

    def __init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user):
        base_object.__init__(self, rel_path, base_path, slideshow, force_user)
        self._db_path = db_path
        self._itemlist = None
        self._cache_path = cache_path
        self._sorted_itemlist = None
        self._thumb_item = None

    def __len__(self):
        return len(self.get_itemlist())

    def __init_itemlist__(self):
        if not self._itemlist:
            self._itemlist = []
            if self.is_a_searchresult():
                search_txt = flask.request.args.get('q', '')
                self.logit_info(logger, "Building itemlist with search text %s", search_txt)
                isearch = indexed_search()
                for rel_path in isearch.search(search_txt):
                    item = self._get_item_by_path(rel_path, self._base_path, self._slideshow, self._db_path, self._cache_path, self._force_user)
                    if item is not None and not item.is_itemlist() and item.exists() and item.user_may_view():  # entry is an supported item and access granted
                        self.logit_debug(logger, "%s matches the query - adding element", rel_path)
                        self._itemlist.append(item)
            else:
                if self.exists():
                    self.logit_info(logger, 'Building itemlist from filestructure %s', self._rel_path)
                    for entry in os.listdir(self.raw_path()):
                        entry_rel_path = os.path.join(self._rel_path, entry)
                        item = self._get_item_by_path(entry_rel_path, self._base_path, self._slideshow, self._db_path, self._cache_path, self._force_user)
                        if item is not None and len(item) > 0 and item.user_may_view():  # entry is an supported item and access granted
                            self._itemlist.append(item)

            def cmp_objects_reverse_chronologic(a, b):
                if a.time() > b.time():
                    return -1
                elif a.time() < b.time():
                    return 1
                elif a.name() > b.name():
                    return -1
                elif b.name() > a.name():
                    return 1
                else:
                    return 0
            #
            self._itemlist.sort(cmp=cmp_objects_reverse_chronologic)
            #
            self._initialised = True

    def create_thumbnail(self, index):
        for item in self.get_itemlist():
            if item.is_itemlist() or item.is_picture() or item.is_video():
                item.create_thumbnail(index)

    def create_webnail(self, index):
        for item in self.get_itemlist():
            if item.is_itemlist() or item.is_picture() or item.is_video():
                item.create_webnail(index)

    def count(self, d=None):
        if d is None:
            d = dict()
            for key in TYPE_NAMES:
                d[key] = 0
        if self.user_may_view() and len(self.get_itemlist()) > 0:
            d[self.TYPE] += 1
            for item in self.get_itemlist():
                d = item.count(d)
        return d

    def exists(self):
        return os.path.isdir(self.raw_path())

    def filesize(self):
        fs = 0
        for i in self.get_itemlist():
            fs += i.filesize()
        return fs

    def get_infos(self):
        infos = base_object.get_infos(self)
        composition_dict = self.item_composition()
        for key in composition_dict:
            infos.append(simple_info(TYPE_NAMES[int(key)], '%d' % composition_dict[key]))
        return infos

    def get_itemlist(self):
        self.__init_itemlist__()
        return self._itemlist

    def get_nxt(self, item):
        rpl = self.sorted_itemlist()
        try:
            index = rpl.index(item._rel_path)
        except ValueError:
            return None
        if index + 1 > len(rpl) - 1:
            return self.get_itemlist()[0]
        else:
            return self.get_itemlist()[index + 1]

    def get_prv(self, item):
        rpl = self.sorted_itemlist()
        try:
            index = rpl.index(item._rel_path)
        except ValueError:
            return None
        if index - 1 < 0:
            return self.get_itemlist()[len(rpl) - 1]
        else:
            return self.get_itemlist()[index - 1]

    def item_composition(self):
        return self.count()

    def name(self, full_name=False):
        if self.is_a_searchresult():
            return lang.search_results % flask.request.args.get('q', '')
        else:
            return base_object.name(self, full_name=full_name)

    def sorted_itemlist(self):
        return [item._rel_path for item in self.get_itemlist()]

    def thumb_item_rel_path(self):
        item = self
        while item.is_itemlist():
            try:
                item = item.get_itemlist()[0]
            except IndexError:
                return None
        return item._rel_path

    def thumb_item(self):
        if self._thumb_item is None:
            self._thumb_item = self._get_item_by_path(self.thumb_item_rel_path(), self._base_path, self._slideshow, self._db_path, self._cache_path, self._force_user)
        return self._thumb_item

    def thumbnail_x(self):
        return self.thumb_item().thumbnail_x()

    def thumbnail_xy_max(self):
        return self.thumb_item().thumbnail_xy_max()

    def thumbnail_y(self):
        return self.thumb_item().thumbnail_y()

    def thumbnail_url(self, i=None):
        return self.thumb_item().thumbnail_url(i)

    def time(self):
        return self.thumb_item().time()


class __itemlist_prepared_cache__(__itemlist__):
    CACHE_KEY_FILESIZE = 'filesize'
    CACHE_KEY_ITEM_COMPOSITION = 'item_composition'
    CACHE_KEY_SORTED_ITEMLIST = 'sorted_itemlist'
    CACHE_KEY_THUMB_ITEM_REL_PATH = 'thumb_item_rel_path'
    CACHE_KEYS = [CACHE_KEY_FILESIZE, CACHE_KEY_ITEM_COMPOSITION, CACHE_KEY_SORTED_ITEMLIST, CACHE_KEY_THUMB_ITEM_REL_PATH]
    VERS = 2

    def __init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user):
        __itemlist__.__init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user)

    def data_version(self):
        return self.VERS

    def get(self, key, default=None):
        if key == self.CACHE_KEY_FILESIZE:
            return __itemlist__.filesize(self)
        elif key == self.CACHE_KEY_ITEM_COMPOSITION:
            return __itemlist__.item_composition(self)
        elif key == self.CACHE_KEY_SORTED_ITEMLIST:
            self._sorted_itemlist = __itemlist__.sorted_itemlist(self)
            return self._sorted_itemlist
        elif key == self.CACHE_KEY_THUMB_ITEM_REL_PATH:
            return __itemlist__.thumb_item_rel_path(self)
        return default

    def filesize(self):
        return self.get(self.CACHE_KEY_FILESIZE)

    def item_composition(self):
        return self.get(self.CACHE_KEY_ITEM_COMPOSITION)

    def keys(self):
        return self.CACHE_KEYS

    def sorted_itemlist(self):
        # TODO: check for a better solution to avoid encode decode errors (itemnames are converted from str to unicode after they are stored in cache file)
        sil = self.get(self.CACHE_KEY_SORTED_ITEMLIST)
        for i in range(0, len(sil)):
            if isinstance(sil[i], unicode):
                sil[i] = sil[i].encode('utf-8')
        return sil

    def thumb_item_rel_path(self):
        # TODO: check for a better solution to avoid encode decode errors (itemnames are converted from str to unicode after they are stored in cache file)
        rv = self.get(self.CACHE_KEY_THUMB_ITEM_REL_PATH)
        if isinstance(rv, unicode):
            rv = rv.encode('utf-8')
        return rv

    def uid(self):
        return fstools.uid(self.raw_path()) + '_' + rights_uid(pygal_user.get_session_user() if self._force_user is None else self._force_user)


class itemlist(__itemlist_prepared_cache__):
    def __init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user):
        __itemlist_prepared_cache__.__init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user)
        self._cache_path = cache_path

        user = session_data_handler().get_user() if force_user is None else force_user
        self._cached_data = caching.property_cache_json(__itemlist_prepared_cache__(rel_path, base_path, slideshow, db_path, cache_path, force_user), self._prop_file(user), load_all_on_init=True)

    def __init_itemlist__(self):
        if self.is_a_searchresult():
            __itemlist_prepared_cache__.__init_itemlist__(self)
        else:
            sil = self.sorted_itemlist()
            if not self._itemlist:
                logger.info('Building itemlist from cache %s', self._rel_path)
                self._itemlist = []
                for itemname in sil:
                    item = self._get_item_by_path(str(itemname), self._base_path, self._slideshow, self._db_path, self._cache_path, self._force_user)
                    if item.user_may_view():
                        self._itemlist.append(item)

    def _prop_file(self, user):
        return os.path.join(self._cache_path, self._rel_path.replace(os.path.sep, '_').replace(os.path.extsep, '_') + '_' + (user).encode('utf-8') + '.json')

    def cache_data(self):
        rv = list()
        for user in [''] + auth.user_data_handler().users():
            entry = list()
            entry.append('')
            entry.append(decode(self._prop_file(user)))
            rv.append(entry)
        # Add Link
        for i in range(0, len(rv)):
            rv[i].append(self.info_url(i))
        return rv

    def get(self, key, default=None):
        if self.is_a_searchresult():  # no cache for searchresults
            return __itemlist_prepared_cache__.get(self, key, default)
        else:
            return self._cached_data.get(key, default, logger=logger)

    def has_cache_data(self):
        return True


class staging_itemlist(staging_container, __itemlist__):
    TYPE = TYPE_STAGING_ITEMLIST

    def __init__(self, rel_path, base_path, slideshow, db_path):
        uuid = os.path.basename(base_path)
        staging_container.__init__(self, config.staging_path, uuid, None, None)
        #
        base_object.__init__(self, rel_path, base_path, slideshow, None)
        self._db_path = db_path
        self._itemlist = None
        self._cache_path = None
        self._get_item_by_path = get_staging_item_by_path
        self.__init_itemlist__()


class staging_baseitem(base_item):
    TYPE = TYPE_STAGING_BASEITEM

    def actions(self):
        return []

    def user_may_view(self):
        return True


class staging_picviditem(staging_baseitem):
    TYPE = TYPE_STAGING_PICVID

    def thumbnail_url(self, i=None):
        (i)
        return self.admin_url({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_STAGING,
                               helpers.STR_ARG_ADMIN_ACTION: helpers.STR_ARG_ADMIN_ACTION_THUMB,
                               helpers.STR_ARG_ADMIN_CONTAINER: os.path.basename(self._base_path),
                               helpers.STR_ARG_ADMIN_NAME: self._rel_path})

    def thumbnail_x(self):
        from .picture import picture
        from .video import video
        ext = os.path.splitext(self._rel_path)[1][1:]
        if ext in picture.mime_types.keys():
            i = picture_info(os.path.join(self._base_path, self._rel_path))
        else:
            i = video_info(os.path.join(self._base_path, self._rel_path))
        w = float(i.get(i.WIDTH))
        h = float(i.get(i.HEIGHT))
        return int(pygal_user.get_thumbnail_size() * w / max(w, h))

    def thumbnail_xy_max(self):
        return max(self.thumbnail_x(), self.thumbnail_y())

    def thumbnail_y(self):
        from .picture import picture
        from .video import video
        ext = os.path.splitext(self._rel_path)[1][1:]
        if ext in picture.mime_types.keys():
            i = picture_info(os.path.join(self._base_path, self._rel_path))
        else:
            i = video_info(os.path.join(self._base_path, self._rel_path))
        w = float(i.get(i.WIDTH))
        h = float(i.get(i.HEIGHT))
        return int(pygal_user.get_thumbnail_size() * h / max(w, h))
