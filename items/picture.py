#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import auth
from helpers import decode
from helpers import info_filename_by_relpath
from helpers import link
from helpers import piclink
from helpers import simple_info
import items
from items.database import indexed_search
import json
import logging
import os
import pygal_config as config
from pylibs import fstools
from pylibs.multimedia.picture import picture_edit
from pylibs.multimedia.picture import picture_info_cached
from pylibs.multimedia.picture import __version__
from pylibs import osm
from pylibs import report


logger = logging.getLogger('pygal.items.picture')


def is_picture(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in picture.mime_types.keys()


class picture(items.base_item, report.logit):
    TYPE = items.TYPE_PICTURE
    LOG_PREFIX = 'picture:'
    mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'jpe': 'image/jpeg', 'png': 'image/png', 'tif': 'image/tiff', 'tiff': 'image/tiff', 'gif': 'image/gif'}

    def __init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user):
        items.base_item.__init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user)
        self._xnail_info = None
        self._xnail_info_filename = os.path.join(cache_path, self.uid() + '.json')
        self._cache_path = cache_path
        self._citem_filename = os.path.join(cache_path, self.uid() + '_%s.jpg')
        self._info_filename = info_filename_by_relpath(rel_path) 
        self._info = picture_info_cached(self.raw_path(), self._info_filename, callback_on_data_storage=self._info_data_changed)

    def _info_data_changed(self):
        isearch = indexed_search()
        isearch.update_document_by_rel_path(self._rel_path)
        self.logit_debug(logger, 'Item-Data changed => updating index for %s', self.name())

    def _create_citem(self, size, force=False, logger=None):
        this_method_version = '.0.1.1'
        if self._xnail_info is None:
            try:
                with open(self._xnail_info_filename, 'r') as fh:
                    self._xnail_info = json.loads(fh.read())
            except:
                self._xnail_info = dict()
        VERSION = '__module_version_citem_creation_%d__' % size
        if force or not os.path.exists(self.citem_filename(size)) or self._xnail_info.get(VERSION) != __version__ + this_method_version:
            self.logit_info(logger, 'creating citem (%d) for %s', size, self.name())
            try:
                p = picture_edit(self.raw_path())
                p.resize(min(size, self.raw_xy_max()), logger=logger)
                p.rotate(self.orientation(), logger=logger)
            except IOError:
                self.logit_error(logger, 'error creating citem (%d) for %s', size, self.name())
            else:
                try:
                    p.save(self.citem_filename(size))
                except IOError:
                    self.logit_error(logger, 'Error creating citem (%d) for %s', size, self.name())
                else:
                    self._xnail_info[VERSION] = __version__ + this_method_version
                    try:
                        with open(self._xnail_info_filename, 'w') as fh:
                            fh.write(json.dumps(self._xnail_info, sort_keys=True, indent=4))
                    except IOError:
                        self.logit_warning(logger, 'Error while writing cache file (%s)', self._xnail_info_filename)

    def actions(self):
        rv = items.base_item.actions(self)
        if self.gps() is not None:
            rv.append(piclink(osm.landmark_link(self.gps()), 'GPS', config.url_prefix + '/static/common/img/earth.png'))
        return rv

    def aperture(self):
        fn = self._info.get(self._info.FNUMBER, None, logger=logger)
        if fn is None:
            return None
        else:
            num, denum = fn
            return 'F%.1f' % (float(num) / float(denum))

    def cache_data(self):
        rv = list()
        entry = list()
        entry.append('User data')
        entry.append(decode(self._db_filename))
        rv.append(entry)
        for i in range(0, len(config.thumbnail_size_list)):
            entry = list()
            entry.append('Thumbnail (%d)' % i)
            entry.append(decode(self._citem_filename % config.thumbnail_size_list[i]))
            rv.append(entry)
        for i in range(0, len(config.webnail_size_list)):
            entry = list()
            entry.append('Webnail (%d)' % i)
            entry.append(decode(self._citem_filename % config.webnail_size_list[i]))
            rv.append(entry)
        entry = list()
        entry.append(decode('Xnail creation version'))
        entry.append(decode(self._xnail_info_filename))
        rv.append(entry)
        entry = list()
        entry.append('Item data')
        entry.append(decode(self._info_filename))
        rv.append(entry)
        # Add Link
        for i in range(0, len(rv)):
            rv[i].append(self.info_url(i))
        return rv

    def camera(self):
        if self.manufactor() is None or self.model() is None:
            return None
        else:
            return '%s - %s' % (self.manufactor(), self.model())

    def delete(self):
        items.base_item.delete(self)
        if self.user_may_delete():
            for cf in fstools.filelist(self._cache_path, self.uid() + '*'):
                if os.path.exists(cf):
                    os.remove(cf)
            if os.path.exists(self._info_filename):
                os.remove(self._info_filename)

    def exposure_program(self):
        return self._info.get(self._info.EXPOSURE_PROGRAM, None, logger=logger)

    def citem_filename(self, size):
        return self._citem_filename % size

    def create_thumbnail(self, index):
        self._create_citem(config.thumbnail_size_list[index], logger=logger)

    def create_webnail(self, index):
        self._create_citem(config.webnail_size_list[index], logger=logger)

    def exposure_time(self):
        et = self._info.get(self._info.EXPOSURE_TIME, None, logger=logger)
        if et is None:
            return None
        else:
            return '%d/%d' % (et[0], et[1])

    def flash(self):
        return self._info.get(self._info.FLASH, None, logger=logger)

    def focal_length(self):
        fl = self._info.get(self._info.FOCAL_LENGTH, None, logger=logger)
        if fl is None:
            return None
        else:
            num, denum = fl
            return '%.2f mm' % (float(num) / float(denum))

    def get_infos(self):
        infos = items.base_item.get_infos(self)
        infos.append(simple_info('Resolution:', self.resolution()))
        infos.append(simple_info('Camera:', self.camera()))
        if self.gps() is not None:
            infos.append(simple_info('GPS:', link(osm.landmark_link(self.gps()), self.gps().__str__())))
        infos.append(simple_info('Flash:', self.flash()))
        infos.append(simple_info('FocalLength:', self.focal_length()))
        infos.append(simple_info('Aperture:', self.aperture()))
        infos.append(simple_info('ExposureTime:', self.exposure_time()))
        infos.append(simple_info('ExposureProgram:', self.exposure_program()))
        infos.append(simple_info('ISOSpeedRatings:', self.iso()))
        infos.append(simple_info('UID:', self.uid()))
        return infos

    def gps(self):
        try:
            gps_dict = self._info.get(self._info.GPS_INFO, None, logger=logger)
        except AttributeError:
            return None
        if gps_dict is None:
            return None
        else:
            return osm.coordinates(gps_dict)

    def gps_link(self):
        if self.gps() is None:
            return None
        else:
            return (osm.landmark_link(self.gps()), self.gps().__str__())

    def has_cache_data(self):
        return True

    def iso(self):
        iso = self._info.get(self._info.ISO, None, logger=logger)
        if iso is None:
            return None
        else:
            return '%d' % iso

    def manufactor(self):
        return self._info.get(self._info.MANUFACTOR, None, logger=logger)

    def model(self):
        return self._info.get(self._info.MODEL, None, logger=logger)

    def orientation(self):
        return self._info.get(self._info.ORIENTATION, logger)

    def ratio_x(self):
        w = self._info.get(self._info.WIDTH, logger)
        h = self._info.get(self._info.HEIGHT, logger)
        if self.orientation() in [6, 8]:
            return float(h) / max(w, h)  # rotation 90 or 270
        return float(w) / max(w, h)

    def ratio_y(self):
        w = self._info.get(self._info.WIDTH, logger)
        h = self._info.get(self._info.HEIGHT, logger)
        if self.orientation() in [6, 8]:
            return float(w) / max(w, h)
        return float(h) / max(w, h)

    def raw_x(self):
        return self._info.get(self._info.WIDTH, logger)
    
    def raw_xy_max(self):
        return max(self.raw_x(), self.raw_y())

    def raw_y(self):
        return self._info.get(self._info.HEIGHT, logger)
    
    def resolution(self):
        if self.raw_x() is None or self.raw_y() is None:
            return None
        else:
            return '%dx%d' % (self.raw_x(), self.raw_y())

    def stay_time(self):
        return 4

    def thumbnail_url(self, i=None):
        return items.base_object.thumbnail_url(self, i=i)

    def thumbnail_x(self):
        return int(self.thumbnail_xy_max() * self.ratio_x())

    def thumbnail_xy_max(self):
        sdh = auth.session_data_handler()
        return config.thumbnail_size_list[sdh.get_thumbnail_index()]

    def thumbnail_y(self):
        return int(self.thumbnail_xy_max() * self.ratio_y())

    def time(self):
        return self._info.get(self._info.TIME, 0, logger=logger)

    def uid(self):
        return fstools.uid(self.raw_path())

    def webnail_url(self, i=None):
        return items.base_object.webnail_url(self, i=i)

    def webnail_x(self):
        return self.webnail_xy_max() * self.ratio_x()

    def webnail_xy_max(self):
        sdh = auth.session_data_handler()
        return config.webnail_size_list[sdh.get_webnail_index()]

    def webnail_y(self):
        return self.webnail_xy_max() * self.ratio_y()
