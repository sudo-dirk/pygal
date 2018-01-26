#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from helpers import encode
import pygal_config as config
import time

class database_handler(dict):
    KEY_REL_PATH = '_rel_path_'
    KEY_TAGS = '_tags_'
    KEY_TAGS_NAME = 'tag'
    KEY_TAGS_X = 'x'
    KEY_TAGS_Y = 'y'
    KEY_TAGS_W = 'w'
    KEY_TAGS_H = 'h'
    KEY_UPLOAD = '_upload_'
    KEY_UPLOAD_TIMESTAMP = 'upload_timestamp'
    KEY_UPLOAD_USERNAME = 'upload_user_name'
    KEY_UPLOAD_SRC_IP = 'upload_src_ip'
    KEY_VERSION = '_db_version_'
    VERSION = 0.1
    
    def __init__(self, db_filename, item_rel_path):
        self._db_filename = db_filename
        self._item_rel_path = item_rel_path
        self._initialised = False

    def _init_database_(self, init_data=None):
        if not self._initialised:
            if init_data is None:
                if self._db_filename is None:
                    data_dict = {}
                else:
                    try:
                        with open(self._db_filename, 'r') as fh:
                            data_dict = json.load(fh)
                    except IOError:
                        data_dict = {}
            else:
                data_dict = init_data.copy()
            version = data_dict.get(self.KEY_VERSION, None)
            if version == None:
                dict.__init__(self)
                self[self.KEY_UPLOAD] = {}
                self[self.KEY_TAGS] = {}
                for key in data_dict:
                    if key != '_common_':
                        self[self.KEY_TAGS][key] = data_dict[key]
                    else:
                        for common_key in data_dict['_common_']:
                            if common_key == 'rel_path':
                                self[self.KEY_REL_PATH] = data_dict['_common_']['rel_path']
                            elif common_key in [self.KEY_UPLOAD_SRC_IP, self.KEY_UPLOAD_TIMESTAMP, self.KEY_UPLOAD_USERNAME]:
                                self[self.KEY_UPLOAD][common_key] =  data_dict['_common_'][common_key]
            elif version == self.VERSION:
                dict.__init__(self, data_dict)
            #
            if self.get(self.KEY_REL_PATH, None) is None:
                self[self.KEY_REL_PATH] = self._item_rel_path
            self[self.KEY_VERSION] = self.VERSION
            #
            self._initialised = True
            #
            if self._db_filename is not None and version != self.VERSION or init_data is not None:
                self._save_()

    def _save_(self):
        if self._db_filename is not None and self._initialised:
            with open(self._db_filename, 'w') as fh:
                json.dump(self, fh, indent=4, sort_keys=True)
    
    def add_data(self, key, data):
        self._init_database_()
        if key in [self.KEY_UPLOAD_SRC_IP, self.KEY_UPLOAD_TIMESTAMP, self.KEY_UPLOAD_USERNAME]:
            self[self.KEY_UPLOAD][key] = data
            self._save_()

    def add_tag_wn(self, tag, ident=None):
        self._init_database_()
        if ident is None:
            tag_id = 1
            while str(tag_id) in self.get_tag_id_list():
                tag_id += 1
        else:
            tag_id = ident
        tag_dict = dict()
        tag_dict[self.KEY_TAGS_NAME] = tag
        self[self.KEY_TAGS][str(tag_id)] = tag_dict
        self._save_()

    def add_tag_wn_xywh(self, x, y, w, h, tag, ident=None):
        self._init_database_()
        if ident is None:
            tag_id = 1
            while str(tag_id) in self.get_tag_id_list():
                tag_id += 1
        else:
            tag_id = ident
        tag_dict = dict()
        tag_dict[self.KEY_TAGS_NAME] = tag
        tag_dict[self.KEY_TAGS_X] = float(x) / self.webnail_x()
        tag_dict[self.KEY_TAGS_Y] = float(y) / self.webnail_y()
        tag_dict[self.KEY_TAGS_W] = float(w) / self.webnail_x()
        tag_dict[self.KEY_TAGS_H] = float(h) / self.webnail_y()
        self[self.KEY_TAGS][str(tag_id)] = tag_dict
        self._save_()

    def add_tag_wn_x1y1x2y2(self, x1, y1, x2, y2, tag_text, tag_id=None):
        self.add_tag_wn_xywh(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1), tag_text, tag_id)

    def delete_tag(self, tag_id):
        self._init_database_()
        if self.tag_id_exists(tag_id):
            del self[self.KEY_TAGS][tag_id]
            self._save_()

    def get_database_content(self):
        self._init_database_()
        rv = self.copy()
        del(rv[self.KEY_REL_PATH])
        return rv

    def get_rel_path(self):
        self._init_database_()
        rp = self.get(self.KEY_REL_PATH)
        if rp is not None:
            return encode(rp)
        return ''

    def tag_id_exists(self, tag_id):
        self._init_database_()
        return tag_id in self[self.KEY_TAGS]

    def get_tag_id_list(self):
        self._init_database_()
        rv = self[self.KEY_TAGS].keys()
        rv.sort()
        return rv

    def get_tag_wn_x(self, tag_id):
        self._init_database_()
        try:
            return int(self[self.KEY_TAGS][tag_id]['x'] * self.webnail_x())
        except:
            return ''

    def get_tag_wn_y(self, tag_id):
        self._init_database_()
        try:
            return int(self[self.KEY_TAGS][tag_id]['y'] * self.webnail_y())
        except:
            return ''

    def get_tag_wn_w(self, tag_id):
        self._init_database_()
        try:
            return int(self[self.KEY_TAGS][tag_id]['w'] * self.webnail_x())
        except:
            return ''

    def get_tag_wn_h(self, tag_id):
        self._init_database_()
        try:
            return int(self[self.KEY_TAGS][tag_id]['h'] * self.webnail_y())
        except:
            return ''

    def get_tag_wn_x2(self, tag_id):
        self._init_database_()
        try:
            return self.get_tag_wn_x(tag_id) + self.get_tag_wn_w(tag_id)
        except:
            return ''

    def get_tag_wn_y2(self, tag_id):
        self._init_database_()
        try:
            return self.get_tag_wn_y(tag_id) + self.get_tag_wn_h(tag_id)
        except:
            return ''

    def get_tag_text(self, tag_id):
        self._init_database_()
        try:
            return self[self.KEY_TAGS][tag_id]['tag']
        except:
            return ''

    def get_tag_icon(self, tag_id):
        self._init_database_()
        return config.url_prefix + '/static/common/img/%d.png' % (int(tag_id) % 10)

    def get_upload_src_ip(self):
        self._init_database_()
        if self.KEY_UPLOAD_SRC_IP in self[self.KEY_UPLOAD]:
            return self[self.KEY_UPLOAD][self.KEY_UPLOAD_SRC_IP]
        else:
            return ''

    def get_upload_strtime(self):
        self._init_database_()
        if self.KEY_UPLOAD_TIMESTAMP in self[self.KEY_UPLOAD]:
            return time.strftime("%d.%m.%Y - %H:%M:%S", time.gmtime(self[self.KEY_UPLOAD][self.KEY_UPLOAD_TIMESTAMP]))
        else:
            return ''

    def get_upload_user(self):
        self._init_database_()
        if self.KEY_UPLOAD_USERNAME in self[self.KEY_UPLOAD]:
            return self[self.KEY_UPLOAD][self.KEY_UPLOAD_USERNAME]
        else:
            return ''

    def db_is_empty(self):
        self._init_database_()
        return len(self[self.KEY_UPLOAD]) == 0 and len(self[self.KEY_TAGS]) == 0

    def matches(self, query):
        self._init_database_()
        for tag_id in self.get_tag_id_list():
            if query.lower() in self.get_tag_text(tag_id).lower():
                return True
        return False

    def tag_has_coordinates(self, tag_id):
        self._init_database_()
        if self.get_tag_wn_x(tag_id) == '':
            return False
        if self.get_tag_wn_y(tag_id) == '':
            return False
        if self.get_tag_wn_w(tag_id) == '':
            return False
        if self.get_tag_wn_h(tag_id) == '':
            return False
        return True
