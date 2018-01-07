#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from auth import pygal_user
from items import base_item_props, cached_itemlist
from items import itemlist
from pylibs import osm
from helpers import piclink
from helpers import strargs
from helpers import decode
from app import prefix_cachedataview
from app import prefix_thumbnail
from app import prefix_webnail
from pylibs.multimedia.picture import picture_info_cached
from pylibs.multimedia.picture import picture_edit
from pylibs.multimedia.picture import __version__
from pylibs import fstools
import struct
import json
import os
from pygal import logger
from pylibs import report
import pygal_config as config
import time
import urllib


def is_picture(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in picture.mime_types.keys()


class picture(base_item_props, report.logit):
    LOG_PREFIX = 'picture:'
    mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'jpe': 'image/jpeg', 'png': 'image/png', 'tif': 'image/tiff', 'tiff': 'image/tiff', 'gif': 'image/gif'}
    required_prop_keys = ['raw_x', 'raw_y', 'time', 'orientation', 'manufactor', 'model']
    prop_vers = 0.1

    def __init__(self, rel_path, request_args={}, parent=None, slideshow=False, **kwargs):
        base_item_props.__init__(self, rel_path, request_args=request_args, slideshow=slideshow, parent=parent)
        self.logit_debug(logger, 'Initialising %s', self.name(True))
        self._info = picture_info_cached(self.raw_path(), self.prop_item_path())
        self._citem_info = None

        self._parent = None
        self._prv = None
        self._nxt = None
        self._thumbnail_x = None
        self._thumbnail_y = None
        self._webnail_x = None
        self._webnail_y = None

    def cache_data_url(self, i):
        cu = config.url_prefix + prefix_cachedataview
        if self._rel_path:
            cu += '/' + urllib.quote(self._rel_path)
        return cu + strargs({'index': str(i)})

    def cache_data(self):
        rv = list()
        for i in range(0, len(config.thumbnail_size_list)):
            entry = list()
            entry.append('Thumbnail (%d)' % i)
            entry.append(decode(self._cimage_item_path(config.thumbnail_size_list[i])))
            rv.append(entry)
        for i in range(0, len(config.webnail_size_list)):
            entry = list()
            entry.append('Webnail (%d)' % i)
            entry.append(decode(self._cimage_item_path(config.webnail_size_list[i])))
            rv.append(entry)
        entry = list()
        entry.append(decode('Xnail creation version'))
        entry.append(decode(self.prop_citem_path()))
        rv.append(entry)
        entry = list()
        entry.append('Item data')
        entry.append(decode(self.prop_item_path()))
        rv.append(entry)
        entry = list()
        entry.append('User data')
        entry.append(decode(self.tag_path()))
        rv.append(entry)
        # Add Link
        for i in range(0, len(rv)):
            rv[i].append(self.cache_data_url(i))
        return rv

    def num_pic(self):
        return 1

    def num_vid(self):
        return 0

    def num_gal(self):
        return 0

    def actions(self):
        rv = list()
        rv.append(piclink(self.info_url(), 'Info', config.url_prefix + '/static/common/img/info.png'))
        if self.user_may_edit():
            rv.append(piclink(self.add_tag_url(), 'Add Tag', config.url_prefix + '/static/common/img/edit.png'))
        if self.user_may_download():
            rv.append(piclink(self.download_url(), 'Download', config.url_prefix + '/static/common/img/download.png'))
        if self.gps() is not None:
            rv.append(piclink(self.gps_link()[0], 'GPS', config.url_prefix + '/static/common/img/earth.png'))
        if self.slideshow():
            rv.append(piclink(self.url(), 'Stop Slideshow', config.url_prefix + '/static/common/img/stop_slideshow.png'))
        else:
            rv.append(piclink(self.slideshow_url(), 'Start Slideshow', config.url_prefix + '/static/common/img/start_slideshow.png'))
        if self.user_may_delete():
            rv.append(piclink(self.delete_url(), 'Delete', config.url_prefix + '/static/common/img/delete.png'))
        return rv

    def aperture(self):
        fn = self._info.get(self._info.FNUMBER, None, logger=logger)
        if fn is None:
            return None
        else:
            num, denum = fn
            return 'F%.1f' % (float(num) / float(denum))

    def camera(self):
        if self.manufactor() is None or self.model() is None:
            return None
        else:
            return '%s - %s' % (self.manufactor(), self.model())

    def create_thumbnail(self, force=False, index=None):
        try:
            if index is None:
                self._create_citem(pygal_user.get_thumbnail_size(), force)
            else:
                self._create_citem(config.thumbnail_size_list[index], force)
        except RuntimeError:
            for thumbnail_size in config.thumbnail_size_list:
                self._create_citem(thumbnail_size, force)

    def create_webnail(self, force=False, index=None):
        try:
            if index is None:
                self._create_citem(pygal_user.get_webnail_size(), force)
            else:
                self._create_citem(config.webnail_size_list[index], force)
        except RuntimeError:
            for webnail_size in config.webnail_size_list:
                self._create_citem(webnail_size, force)

    def delete(self):
        base_item_props.delete(self)
        for folder in [config.citem_folder]:
            for filename in fstools.filelist(folder, self.uid() + '*'):
                os.remove(filename)
        os.remove(self.prop_item_path())

    def exposure_program(self):
        return self._info.get(self._info.EXPOSURE_PROGRAM, None, logger=logger)

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
        infos = list()

        def add_info(desc, info):
            if info is not None:
                infos.append([desc, info])

        add_info('Itemdate:', self.strtime())
        add_info('Name:', self.name(True))
        add_info('Uploaddate:', self.get_upload_strtime())
        add_info('Uploaduser:', self.get_upload_user())
        add_info('Upload IP:', self.get_upload_src_ip())
        add_info('Size:', self.strfilesize())
        add_info('Resolution:', self.resolution())
        add_info('Camera:', self.camera())
        add_info('GPS:', self.gps_link())
        add_info('Flash:', self.flash())
        add_info('FocalLength:', self.focal_length())
        add_info('Aperture:', self.aperture())
        add_info('ExposureTime:', self.exposure_time())
        add_info('ExposureProgram:', self.exposure_program())
        add_info('ISOSpeedRatings:', self.iso())
        add_info('UID:', self.uid())
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

    def nxt(self):
        return base_item_props.nxt(self, excluded_types=[itemlist, cached_itemlist])

    def orientation(self):
        return self._info.get(self._info.ORIENTATION, None, logger=logger)

    def prop_citem_path(self):
        return os.path.join(config.citem_folder, self.uid() + '.json')

    def prv(self):
        return base_item_props.prv(self, excluded_types=[itemlist, cached_itemlist])

    def raw_x(self):
        return self._info.get(self._info.WIDTH, logger=logger) or pygal_user.get_webnail_size()

    def raw_xy_max(self):
        return max(self.raw_x(), self.raw_y())

    def raw_y(self):
        return self._info.get(self._info.HEIGHT, logger=logger) or pygal_user.get_webnail_size()

    def ratio_x(self):
        return float(self.raw_x()) / max(self.raw_x(), self.raw_y())

    def ratio_y(self):
        return float(self.raw_y()) / max(self.raw_x(), self.raw_y())

    def resolution(self):
        if self.raw_x() is None or self.raw_y() is None:
            return None
        else:
            return '%dx%d' % (self.raw_x(), self.raw_y())

    def stay_time(self):
        return 4

    def strtime(self):
        tm = self.time()
        if tm is None:
            return ''
        return time.strftime("%d.%m.%Y - %H:%M:%S", time.gmtime(self.time()))

    def template(self):
        return 'picture.html'

    def thumbnail_item_path(self, index=None):
        if index is None:
            return self._cimage_item_path(pygal_user.get_thumbnail_size())
        else:
            return self._cimage_item_path(config.thumbnail_size_list[index])

    def thumbnail_url(self, i=None):
        if i is None:
            args = ''
        else:
            args = strargs({'index': str(i)})
        return config.url_prefix + prefix_thumbnail + ('/' + self.url(True) or '') + args

    def thumbnail_x(self):
        if not self._thumbnail_x:
            self._calc_thumbnail_res()
        return self._thumbnail_x or pygal_user.get_thumbnail_size()

    def thumbnail_xy_max(self):
        return max(self.thumbnail_x(), self.thumbnail_y())

    def thumbnail_y(self):
        if not self._thumbnail_y:
            self._calc_thumbnail_res()
        return self._thumbnail_y or pygal_user.get_thumbnail_size()

    def time(self):
        return self._info.get(self._info.TIME, 0, logger=logger)

    def webnail_item_path(self, index=None):
        if index is None:
            return self._cimage_item_path(pygal_user.get_webnail_size())
        else:
            return self._cimage_item_path(config.webnail_size_list[index])

    def webnail_url(self, i=None):
        if i is None:
            args = ''
        else:
            args = strargs({'index': str(i)})
        return config.url_prefix + prefix_webnail + ('/' + self.url(True) or '') +args

    def webnail_x(self):
        if not self._webnail_x:
            self._calc_webnail_res()
        return self._webnail_x or pygal_user.get_webnail_size()

    def webnail_y(self):
        if not self._webnail_y:
            self._calc_webnail_res()
        return self._webnail_y or pygal_user.get_webnail_size()

    def _calc_thumbnail_res(self):
        if not os.path.exists(self.thumbnail_item_path()):
            self.create_thumbnail()
        self._thumbnail_x, self._thumbnail_y = self._get_jpg_size(self.thumbnail_item_path())

    def _calc_webnail_res(self):
        if not os.path.exists(self.webnail_item_path()):
            self.create_webnail()
        self._webnail_x, self._webnail_y = self._get_jpg_size(self.webnail_item_path())

    def _cimage_item_path(self, size):
        return os.path.join(config.basepath, config.citem_folder, '%s_%d.jpg' % (self.uid(), size))

    def _create_citem(self, size, force=False):
        this_method_version = '.0.1.0'
        if self._citem_info is None:
            try:
                with open(self.prop_citem_path(), 'r') as fh:
                    self._citem_info = json.loads(fh.read())
            except:
                self._citem_info = dict()
        VERSION = '__module_version_citem_creation_%d__' % size
        if force or not os.path.exists(self._cimage_item_path(size)) or self._citem_info.get(VERSION) != __version__ + this_method_version:
            self.logit_info(logger, 'creating citem (%d) for %s', size, self.name())
            try:
                p = picture_edit(self.raw_path())
                p.resize(min(size, self.raw_xy_max()))
                p.rotate(self.orientation())
            except IOError:
                self.logit_error(logger, 'error creating citem (%d) for %s', size, self.name())
            else:
                try:
                    p.save(self._cimage_item_path(size))
                except IOError:
                    self.logit_error(logger, 'Error creating citem (%d) for %s', size, self.name())
                else:
                    self._citem_info[VERSION] = __version__ + this_method_version
                    try:
                        with open(self.prop_citem_path(), 'w') as fh:
                            fh.write(json.dumps(self._citem_info, sort_keys=True, indent=4))
                    except IOError:
                        self.logit_warning(logger, 'Error while writing cache file (%s)', self._cache_filename)

    def _get_jpg_size(self, filename):
        try:
            fhandle = open(filename, 'rb')
            fhandle.seek(0)     # Read 0xff next
            size = 2
            ftype = 0
            while not 0xc0 <= ftype <= 0xcf:
                fhandle.seek(size, 1)
                byte = fhandle.read(1)
                while ord(byte) == 0xff:
                    byte = fhandle.read(1)
                ftype = ord(byte)
                size = struct.unpack('>H', fhandle.read(2))[0] - 2
            # We are at a SOFn block
            fhandle.seek(1, 1)  # Skip `precision' byte.
            y, x = struct.unpack('>HH', fhandle.read(4))
            return x, y
        except Exception:   # IGNORE:W0703
            return None, None
