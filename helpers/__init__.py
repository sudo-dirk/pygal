import json
import os
import pygal_config as config  # TODO: check posibility to get rid of this import
from pylibs import fstools
import shutil
import time
import urllib
import uuid


class database_handler(dict):
    KEY_DATA_ID = '_common_'
    KEY_DATA_ID_REL_PATH = 'rel_path'
    KEY_DATA_ID_TIMESTAMP_UPLOAD = 'upload_timestamp'
    KEY_DATA_ID_USERNAME_UPLOAD = 'upload_user_name'
    KEY_DATA_ID_SRC_IP_UPLOAD = 'upload_src_ip'

    def __init__(self, tag_path):
        self._id = 0
        self._tag_path = tag_path
        self._initialised = False

    def _load_tags(self):
        self._initialised = True
        try:
            dict.__init__(self, json.loads(open(self._tag_path, 'r').read()))
        except IOError:
            dict.__init__(self)
        for ident in self:
            try:
                if int(ident) > self._id:
                    self._id = int(ident)
            except ValueError:
                pass  # nothing to do
        if self.KEY_DATA_ID not in self:
            self[self.KEY_DATA_ID] = dict()
        if self.KEY_DATA_ID_REL_PATH not in self[self.KEY_DATA_ID]:
            try:
                self[self.KEY_DATA_ID][self.KEY_DATA_ID_REL_PATH] = self.rel_path()
            except:
                pass
            else:
                self._save_tags()

    def get_rel_path(self):
        if not self._initialised:
            self._load_tags()
        return self.get(self.KEY_DATA_ID, {}).get(self.KEY_DATA_ID_REL_PATH, '')

    def matches(self, query):
        if not self._initialised:
            self._load_tags()
        for tag_id in self.get_tag_id_list():
            if query.lower() in self.get_tag_text(tag_id).lower():
                return True
        return False

    def tag_id_exists(self, tag_id):
        if not self._initialised:
            self._load_tags()
        return tag_id in self and tag_id != self.KEY_DATA_ID

    def get_tag_id_list(self):
        if not self._initialised:
            self._load_tags()
        rv = self.keys()
        if self.KEY_DATA_ID in rv:
            rv.remove(self.KEY_DATA_ID)
        rv.sort()
        return rv

    def get_tag_wn_x(self, tag_id):
        if not self._initialised:
            self._load_tags()
        try:
            return int(self[tag_id]['x'] * self.webnail_x())
        except:
            return ''

    def get_tag_wn_y(self, tag_id):
        if not self._initialised:
            self._load_tags()
        try:
            return int(self[tag_id]['y'] * self.webnail_y())
        except:
            return ''

    def get_tag_wn_w(self, tag_id):
        if not self._initialised:
            self._load_tags()
        try:
            return int(self[tag_id]['w'] * self.webnail_x())
        except:
            return ''

    def get_tag_wn_h(self, tag_id):
        if not self._initialised:
            self._load_tags()
        try:
            return int(self[tag_id]['h'] * self.webnail_y())
        except:
            return ''

    def get_tag_wn_x2(self, tag_id):
        if not self._initialised:
            self._load_tags()
        try:
            return self.get_tag_wn_x(tag_id) + self.get_tag_wn_w(tag_id)
        except:
            return ''

    def get_tag_wn_y2(self, tag_id):
        if not self._initialised:
            self._load_tags()
        try:
            return self.get_tag_wn_y(tag_id) + self.get_tag_wn_h(tag_id)
        except:
            return ''

    def get_tag_text(self, tag_id):
        if not self._initialised:
            self._load_tags()
        try:
            return self[tag_id]['tag']
        except:
            return ''

    def get_tag_icon(self, tag_id):
        if not self._initialised:
            self._load_tags()
        return config.url_prefix + '/static/common/img/%d.png' % (int(tag_id) % 10)

    def get_upload_src_ip(self):
        if not self._initialised:
            self._load_tags()
        if self.KEY_DATA_ID_SRC_IP_UPLOAD in self[self.KEY_DATA_ID]:
            return self[self.KEY_DATA_ID][self.KEY_DATA_ID_SRC_IP_UPLOAD]
        else:
            return ''

    def get_upload_strtime(self):
        if not self._initialised:
            self._load_tags()
        if self.KEY_DATA_ID_TIMESTAMP_UPLOAD in self[self.KEY_DATA_ID]:
            return time.strftime("%d.%m.%Y - %H:%M:%S", time.gmtime(self[self.KEY_DATA_ID][self.KEY_DATA_ID_TIMESTAMP_UPLOAD]))
        else:
            return ''

    def get_upload_user(self):
        if not self._initialised:
            self._load_tags()
        if self.KEY_DATA_ID_USERNAME_UPLOAD in self[self.KEY_DATA_ID]:
            return self[self.KEY_DATA_ID][self.KEY_DATA_ID_USERNAME_UPLOAD]
        else:
            return ''

    def add_data(self, key, data):
        if not self._initialised:
            self._load_tags()
        self[self.KEY_DATA_ID][key] = data

    def add_tag_wn(self, tag, ident=None):
        if not self._initialised:
            self._load_tags()
        tag_dict = dict()
        tag_dict['tag'] = tag
        if ident is None:
            self._id += 1
            self[str(self._id)] = tag_dict
        else:
            self[str(ident)] = tag_dict
        self._save_tags()

    def add_tag_wn_xywh(self, x, y, w, h, tag, ident=None):
        if not self._initialised:
            self._load_tags()
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
        if not self._initialised:
            self._load_tags()
        self.add_tag_wn_xywh(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1), tag_text, tag_id)

    def delete_tag(self, tag_id):
        if not self._initialised:
            self._load_tags()
        if self.tag_id_exists(tag_id):
            del self[tag_id]
            self._save_tags()

    def _save_tags(self):
        if not self._initialised:
            self._load_tags()
        if self._tag_path is not None:
            with open(self._tag_path, 'w') as fh:
                fh.write(json.dumps(self, indent=4, sort_keys=True))

    def tag_has_coordinates(self, tag_id):
        if not self._initialised:
            self._load_tags()
        if self.get_tag_wn_x(tag_id) == '':
            return False
        if self.get_tag_wn_y(tag_id) == '':
            return False
        if self.get_tag_wn_w(tag_id) == '':
            return False
        if self.get_tag_wn_h(tag_id) == '':
            return False
        return True


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


class staging_container(dict):
    CONTAINER_INFO_FILE_EXTENTION = 'json'

    KEY_TIMESTAMP = database_handler.KEY_DATA_ID_TIMESTAMP_UPLOAD
    KEY_UUID = '_uuid_'
    KEY_CONTAINER_FILES = 'container_files'
    KEY_USERNAME = database_handler.KEY_DATA_ID_USERNAME_UPLOAD
    KEY_CONTAINERNAME = 'container_name'
    KEY_SRC_IP = database_handler.KEY_DATA_ID_SRC_IP_UPLOAD

    DATABASE_KEYS = [KEY_TIMESTAMP, KEY_USERNAME, KEY_SRC_IP]
    """
    Class handle a staging container

    :param str staging_path: The path, where the staging items will be stored
    :param instance filelist: A list of file instance which has at least the following variables and methods (.filename, .save(path))
    :param str uploading_user: The user which uploaded the files
    :param method allowed_extentions: A list of allowed extentions for the files
    :param str name: The name of the Container
    :param str src_ip: The IP oft the client uploading the files
    """

    def __init__(self, staging_path, filelist, allowed_extentions, uploading_user, name, src_ip):
        dict.__init__(self)
        # system
        self._staging_path = staging_path
        self._filelist = filelist
        self._allowed_extentions = allowed_extentions
        # generated information
        self[self.KEY_TIMESTAMP] = time.time()
        self[self.KEY_UUID] = str(uuid.uuid4())
        # given information
        if filelist is not None:
            self[self.KEY_CONTAINER_FILES] = [f.filename for f in filelist]
        else:
            self[self.KEY_CONTAINER_FILES] = list()
        self[self.KEY_USERNAME] = uploading_user
        self[self.KEY_CONTAINERNAME] = name
        self[self.KEY_SRC_IP] = src_ip

    def allowed_files(self):
        if self._allowed_extentions is None:
            return self.get(self.KEY_CONTAINER_FILES)
        else:
            rv = list()
            for filename in self.get(self.KEY_CONTAINER_FILES):
                if '.' in filename and filename.rsplit('.', 1)[1].lower() in self._allowed_extentions:
                    rv.append(filename)
            return rv

    def rejected_files(self):
        rv = list()
        if self._allowed_extentions is not None:
            for filename in self.get(self.KEY_CONTAINER_FILES):
                if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in self._allowed_extentions):
                    rv.append(filename)
        return rv

    def save(self):
        if self._staging_path is not None and len(self.allowed_files()) > 0:
            # generate container_info_file
            cif = os.path.join(self._staging_path, self.get(self.KEY_UUID) + '.' + self.CONTAINER_INFO_FILE_EXTENTION)
            with open(cif, 'w') as fh:
                fh.write(json.dumps(self, indent=4, sort_keys=True))
            # generate container_files
            if self._filelist is not None:
                file_path = os.path.join(self._staging_path, self.get(self.KEY_UUID))
                os.mkdir(file_path)
                for f in self._filelist:
                    if f.filename in self.allowed_files():
                        f.save(os.path.join(file_path, f.filename))

    def get_container_info_file_by_uuid(self, uuid):
        if self._staging_path is None:
            return None
        else:
            return os.path.join(self._staging_path, uuid + '.' + self.CONTAINER_INFO_FILE_EXTENTION)

    def get_container_file_path(self, filename):
        if self._staging_path is None or self[self.KEY_UUID] is None:
            return None
        else:
            return os.path.join(self._staging_path, self[self.KEY_UUID], filename)

    def load(self, container_info_file):
        self._staging_path = os.path.dirname(container_info_file)
        with open(container_info_file, 'r') as fh:
            data = json.loads(fh.read())
        dict.__init__(self, data)

    def delete(self):
        shutil.rmtree(os.path.join(self._staging_path, self[self.KEY_UUID]))
        os.remove(self.get_container_info_file_by_uuid(self[self.KEY_UUID]))

    def is_empty(self):
        return len(self[self.KEY_CONTAINER_FILES]) == 0

    def move(self, items_target_path, database_path, item_path):
        # iteration over files
        for filename in list(self[self.KEY_CONTAINER_FILES]):
            database_filename = os.path.join(database_path, os.path.join(items_target_path, filename).replace(os.path.sep, '_').replace(os.path.extsep, '_') + '.json')
            item_filename = os.path.join(item_path, items_target_path, filename)
            if not os.path.exists(database_filename) and not os.path.exists(item_filename) and fstools.is_writeable(os.path.dirname(database_filename)) and fstools.is_writeable(os.path.dirname(item_filename)):
                dbh = database_handler(database_filename)
                for key in self.DATABASE_KEYS:
                    dbh.add_data(key, self.get(key))
                dbh._save_tags()
                os.rename(self.get_container_file_path(filename), item_filename)
                self[self.KEY_CONTAINER_FILES].remove(filename)
        if self.is_empty():
            self.delete()
        else:
            self.save()


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
        return '/' + urllib.quote(item_name)
    else:
        return ''
