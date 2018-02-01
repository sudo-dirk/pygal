#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: - add exception handling for query_parser (e.g.: date:[-2y to now])
#       - if create cache is executed, whoosh index will be created piece by piece (bad performance/ content expected?)
# QUESTIONS TO ASK: dynamic data no index from scratch, only add_document, update_document and delete_by_term -> create from scratch from time to time?
#                   saw exception somthing like writelock. What is a good strategy? wait and try again, queue?
#See: http://whoosh.readthedocs.io/en/latest/indexing.html

import datetime
import helpers
import json
import logging
import os
import pygal_config as config
from pylibs import fstools
from pylibs import report
import time
from whoosh import index
from whoosh.fields import Schema, ID, TEXT, DATETIME, NUMERIC
from whoosh.qparser import MultifieldParser
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh.index import EmptyIndexError


logger = logging.getLogger('pygal.items.database')


class database_handler(dict, report.logit):
    LOG_PREFIX = 'DBH:'
    #
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
            self.logit_debug(logger, 'Item-Data changed => updating index for %s', self._item_rel_path)
            isearch = indexed_search()
            isearch.update_document_by_rel_path(self._item_rel_path)
    
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
            return helpers.encode(rp)
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

    def get_upload_time(self):
        self._init_database_()
        if self.KEY_UPLOAD_TIMESTAMP in self[self.KEY_UPLOAD]:
            return self[self.KEY_UPLOAD][self.KEY_UPLOAD_TIMESTAMP]
        else:
            return None

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


class indexed_search(report.logit):
    # TODO: implement incremental init over all documents (update/ delete) and missing items (add) and check performance again
    LOG_PREFIX = 'WHOOSH:'
    #
    DATA_VERS = 1
    UPDATE_STRATEGY_INCREMANTAL = False

    def __init__(self):
        self.schema = Schema(
            rel_path=ID(unique=True, stored=True), 
            index_vers=NUMERIC(stored=True),
            type=TEXT,
            path=TEXT, 
            # user_data
            user_data_uid=TEXT(stored=True),
            tags=TEXT, 
            upload_user=TEXT, 
            upload_ip=TEXT, 
            upload_date=DATETIME,
            # item info data
            item_data_uid=TEXT(stored=True),
            date=DATETIME,
            height=NUMERIC,
            width=NUMERIC,
            camera=TEXT,
            orientation=NUMERIC,
            flash=TEXT,
            aperture=NUMERIC,
            focal_length=NUMERIC,
            exposure_time=NUMERIC,
            exposure_program=TEXT,
            iso=NUMERIC,
            duration=NUMERIC)
        try:
            self.load_index()
        except EmptyIndexError:
            self.logit_info(logger, 'Initialising index from scratch caused by non existing index')
            self.create_index_from_scratch()
        else:
            if self.UPDATE_STRATEGY_INCREMANTAL:
                self.update_index_incremental()
                self.logit_info(logger, 'Previous stored Index loaded and updated incrementally')
            else:
                with self.ix.searcher() as searcher:
                    for field in searcher.all_stored_fields():
                        index_version = field.get('index_vers')
                        if index_version is not None:
                            break
                if index_version != self.DATA_VERS:
                    self.logit_info(logger, 'Initialising index from scratch caused by new data version %d -> %d', index_version, self.DATA_VERS)
                    self.create_index_from_scratch()
                else:
                    self.logit_info(logger, 'Previous stored Index loaded')

    def load_index(self):
        self.ix = index.open_dir(config.whoosh_path)

    def wrap_data_and_call_method(self, rel_path, method):
        from video import is_video
        from picture import is_picture
        # database content
        db_filename = helpers.db_filename_by_relpath(config.database_path, rel_path)
        info_filename = helpers.info_filename_by_relpath(rel_path)
        if os.path.isfile(db_filename) or (os.path.isfile(info_filename) and (is_picture(rel_path) or is_video(rel_path))):
            self.logit_debug(logger, 'Adding/ Updating index document %s', rel_path)
            if os.path.isfile(db_filename):
                db = database_handler(db_filename, None)
                # User-Data
                tags = u' '.join([helpers.decode(db.get_tag_text(tag_id)) for tag_id in db.get_tag_id_list()]) + u' '
                upload_user = helpers.decode(db.get_upload_user()) 
                upload_ip = helpers.decode(db.get_upload_src_ip())
                upload_date = datetime.datetime.fromtimestamp(db.get_upload_time()) if db.get_upload_time() is not None else None
            else:
                tags = None
                upload_user = None
                upload_ip = None
                upload_date = None
            # info content
            if os.path.isfile(info_filename):
                with open(info_filename, 'r') as fh:
                    info = json.load(fh)
                    # Item-Data
                    if is_picture(rel_path):
                        from pylibs.multimedia.picture import picture_info
                        item_date = datetime.datetime.fromtimestamp(info.get(picture_info.TIME)) if info.get(picture_info.TIME) is not None else None
                        item_height = info.get(picture_info.HEIGHT) if info.get(picture_info.HEIGHT) is not None else None
                        item_width = info.get(picture_info.WIDTH) if info.get(picture_info.WIDTH) is not None else None
                        item_camera = helpers.decode(info.get(picture_info.MANUFACTOR) or '') + u' ' + helpers.decode(info.get(picture_info.MODEL) or '')
                        item_orientation = info.get(picture_info.ORIENTATION) if info.get(picture_info.ORIENTATION) is not None else None
                        item_flash = helpers.decode(info.get(picture_info.FLASH)) if info.get(picture_info.FLASH) is not None else None
                        try:
                            item_aperture = float(info.get(picture_info.FNUMBER)[0]) / float(info.get(picture_info.FNUMBER)[0])
                        except TypeError:
                            item_aperture = None
                        try:
                            item_focal_length = float(info.get(picture_info.FOCAL_LENGTH)[0]) / float(info.get(picture_info.FOCAL_LENGTH)[0])
                        except TypeError:
                            item_focal_length = None
                        try:
                            item_exposure_time = float(info.get(picture_info.EXPOSURE_TIME)[0]) / float(info.get(picture_info.EXPOSURE_TIME)[0])
                        except TypeError:
                            item_exposure_time = None
                        item_exposure_program = helpers.decode(info.get(picture_info.EXPOSURE_PROGRAM)) if info.get(picture_info.EXPOSURE_PROGRAM) is not None else None
                        item_iso = info.get(picture_info.ISO) if info.get(picture_info.ISO) is not None else None
                        # TODO: Add GPS info to whoosh index (Item-Data)
                        """
                            GPS_INFO = 'GPSInfo'
                        """
                        item_duration = None
                    elif is_video(rel_path):
                        from pylibs.multimedia.video import video_info
                        item_date = datetime.datetime.fromtimestamp(info.get(video_info.TIME)) if info.get(video_info.TIME) is not None else None
                        item_height = info.get(video_info.HEIGHT) if info.get(video_info.HEIGHT) is not None else None
                        item_width = info.get(video_info.WIDTH) if info.get(video_info.WIDTH) is not None else None
                        item_duration = info.get(video_info.DURATION) if info.get(video_info.DURATION) is not None else None
                        # TODO: Add ratio to whoosh index (Item-Data)
                        """
                            RATIO = 'ratio'
                        """
                        item_camera = None
                        item_orientation = None
                        item_flash = None
                        item_aperture = None
                        item_focal_length = None
                        item_exposure_time = None
                        item_exposure_program = None
                        item_iso = None
            else:
                item_date=None
                item_height=None
                item_width=None
                item_camera=None
                item_orientation=None
                item_flash=None
                item_aperture=None
                item_focal_length=None
                item_exposure_time=None
                item_exposure_program=None
                item_iso=None
                item_duration=None
            method(
                rel_path=helpers.decode(rel_path),
                index_vers=self.DATA_VERS,
                type=u' '.join([u'video' if is_video(rel_path) else u'picture' if is_picture(rel_path) else '', helpers.decode(os.path.splitext(rel_path)[1][1:])]), 
                path=helpers.decode(' '.join(rel_path.split(os.path.sep)).strip()),
                # User-Data
                user_data_uid=helpers.decode(fstools.uid(db_filename)),
                tags=tags,
                upload_user=upload_user, 
                upload_ip=upload_ip,
                upload_date=upload_date,
                # Item-Data
                item_data_uid=helpers.decode(fstools.uid(info_filename)),
                date=item_date,
                height=item_height,
                width=item_width,
                camera=item_camera,
                orientation=item_orientation,
                flash=item_flash,
                aperture=item_aperture,
                focal_length=item_focal_length,
                exposure_time=item_exposure_time,
                exposure_program=item_exposure_program,
                iso=item_iso,
                duration=item_duration)
        else:
            method(
                rel_path=helpers.decode(rel_path),
                index_vers=self.DATA_VERS,
                type=u' '.join([u'video' if is_video(rel_path) else u'picture' if is_picture(rel_path) else '', helpers.decode(os.path.splitext(rel_path)[1][1:])]), 
                path=helpers.decode(' '.join(rel_path.split(os.path.sep)).strip()),
                # User-Data
                user_data_uid=helpers.decode(fstools.uid(db_filename)),
                # Item-Data
                item_data_uid=helpers.decode(fstools.uid(info_filename)))
            
    def create_index_from_scratch(self):
        self.ix = index.create_in(config.whoosh_path, schema=self.schema)
        writer = self.ix.writer()
        #
        # iteration over all existing items
        for filename in fstools.filelist(config.item_path):
            rel_path = filename[len(config.item_path)+1:]
            self.wrap_data_and_call_method(rel_path, writer.add_document)
        writer.commit()

    def update_index_incremental(self):
        # rel_path list for identification of missing documents in the index
        rel_paths = set()
        for filename in fstools.filelist(config.item_path):
            rel_paths.add(filename[len(config.item_path)+1:])

        # Update existing documents
        writer = self.ix.writer()
        with self.ix.searcher() as searcher:
            for document in searcher.all_stored_fields():
                rel_path = document.get('rel_path')
                db_filename = helpers.db_filename_by_relpath(config.database_path, rel_path)
                db_uid = helpers.decode(fstools.uid(db_filename))
                info_filename = helpers.info_filename_by_relpath(rel_path)
                info_uid = helpers.decode(fstools.uid(info_filename))
                index_version = document.get('index_vers')
                if rel_path in rel_paths:
                    rel_paths.remove(rel_path)
                    if index_version != self.DATA_VERS:
                        self.create_index_from_scratch()
                        return
                    elif db_uid != document.get('user_data_uid') or info_uid != document.get('item_data_uid'):
                        self.wrap_data_and_call_method(rel_path, writer.update_document)
                else:
                    self.logit_debug(logger, 'Deleting index document for %s', rel_path)
                    writer.delete_by_term("rel_path", rel_path)

        # Add missing documents
        for rel_path in rel_paths:
            self.wrap_data_and_call_method(rel_path, writer.add_document)
        writer.commit()
            
    def delete_document_by_rel_path(self, rel_path):
        if not self.UPDATE_STRATEGY_INCREMANTAL:
            self.logit_debug(logger, 'Deleting index document for %s', rel_path)
            writer = self.ix.writer()
            writer.delete_by_term("rel_path", rel_path)
            writer.commit()

    def update_document_by_rel_path(self, rel_path):
        if not self.UPDATE_STRATEGY_INCREMANTAL:
            db_filename = helpers.db_filename_by_relpath(config.database_path, rel_path)
            db_uid = helpers.decode(fstools.uid(db_filename))
            info_filename = helpers.info_filename_by_relpath(rel_path)
            info_uid = helpers.decode(fstools.uid(info_filename))
            with self.ix.searcher() as searcher:
                document = searcher.document(rel_path=rel_path)
            
            if document is None or db_uid != document.get('user_data_uid') or info_uid != document.get('item_data_uid'):
                writer = self.ix.writer()
                self.logit_debug(logger, 'Updating index document for %s', rel_path)
                self.wrap_data_and_call_method(rel_path, writer.update_document)
                writer.commit()

    def search(self, search_txt):
        qp = MultifieldParser(["tags", "path"], schema=self.ix.schema)
        qp.add_plugin(DateParserPlugin(free=True))
        q = qp.parse(search_txt)

        with self.ix.searcher() as s:
            results = s.search(q, limit=None)
            return [helpers.encode(hit.get('rel_path')) for hit in results]