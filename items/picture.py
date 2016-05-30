#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from items import base_item_props
from items import itemlist
from pylibs import osm
from app import piclink
from app import prefix_add_tag
from app import prefix_delete
from app import prefix_info
from app import prefix_thumbnail
from app import prefix_webnail
from pylibs.multimedia.picture import picture_info_cached
from pylibs.multimedia.picture import picture_edit
from pylibs.multimedia.picture import __version__
from pylibs import fstools
import json
import os
from pygal import logger
import pygal_config as config
import time


class tags(dict):
    DATA_ID = '_common_'

    def __init__(self):
        self._id = 0
        try:
            dict.__init__(self, json.loads(open(self.tag_path(), 'r').read()))
            for ident in self:
                if int(ident) > self._id:
                    self._id = int(ident)
        except:
            dict.__init__(self)
        if self.DATA_ID not in self:
            self[self.DATA_ID] = dict()
            self[self.DATA_ID]['rel_path'] = self.rel_path()
            self._save_tags()

    def tag_id_exists(self, tag_id):
        return tag_id in self and tag_id != self.DATA_ID

    def get_tag_id_list(self):
        rv = self.keys()
        rv.remove(self.DATA_ID)
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
        self.add_tag_wn_xywh(min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1), tag_text, tag_id)

    def delete_tag(self, tag_id):
        if self.tag_id_exists(tag_id):
            del self[tag_id]
            self._save_tags()

    def _save_tags(self):
        if self.tag_path() is not None:
            with open(self.tag_path(), 'w') as fh:
                fh.write(json.dumps(self, indent=3, sort_keys=True))



class picture(base_item_props, tags):
    mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'jpe': 'image/jpeg', 'png': 'image/png', 'tif': 'image/tiff', 'tiff': 'image/tiff', 'gif': 'image/gif'}
    required_prop_keys = ['raw_x', 'raw_y', 'time', 'orientation', 'manufactor', 'model']
    prop_vers = 0.1

    def __init__(self, rel_path, request_args={}, prefix='', parent=None, **kwargs):
        base_item_props.__init__(self, rel_path, request_args=request_args, prefix=prefix, parent=parent)
        tags.__init__(self)
        logger.debug('Initialising %s', self.name(True))
        self._info = picture_info_cached(self.raw_path(), self.prop_item_path(), logger=logger)
        self._citem_info = None

        self._parent = None
        self._prv = None
        self._nxt = None
        self._thumbnail_x = None
        self._thumbnail_y = None
        self._webnail_x = None
        self._webnail_y = None

    def num_pic(self):
        return 1

    def num_vid(self):
        return 0

    def num_gal(self):
        return 0

    def actions(self):
        rv = list()
        # rv.append(piclink(self.edit_url(), 'Edit', config.url_prefix + '/static/pygal_theme/img/edit.png'))
        if self._prefix != prefix_info:
            rv.append(piclink(self.info_url(), 'Info', config.url_prefix + '/static/common/img/info.png'))
        if self._prefix != prefix_add_tag:
            rv.append(piclink(self.add_tag_url(), 'Add Tag', config.url_prefix + '/static/common/img/edit.png'))
        if self.user_may_download():
            rv.append(piclink(self.download_url(), 'Download', config.url_prefix + '/static/common/img/download.png'))
        if self.gps() is not None:
            rv.append(piclink(self.gps_link()[0], 'GPS', config.url_prefix + '/static/common/img/earth.png'))
        # rv.append(piclink(self.info_url(), 'Lock', config.url_prefix + '/static/pygal_theme/img/lock.png'))
        if self.slideshow():
            rv.append(piclink(self.url(), 'Stop Slideshow', config.url_prefix + '/static/common/img/stop_slideshow.png'))
        else:
            rv.append(piclink(self.slideshow_url(), 'Start Slideshow', config.url_prefix + '/static/common/img/start_slideshow.png'))
        if self.user_may_delete() and self._prefix != prefix_delete:
            rv.append(piclink(self.delete_url(), 'Delete', config.url_prefix + '/static/common/img/delete.png'))
        return rv

    def aperture(self):
        fn = self._info.get(self._info.FNUMBER, None)
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

    def create_thumbnail(self, force=False):
        self._create_citem(config.thumbnail_size, force)

    def create_webnail(self, force=False):
        self._create_citem(config.webnail_size, force)

    def delete(self):
        base_item_props.delete(self)
        for folder in [config.citem_folder]:
            for filename in fstools.filelist(folder, self.uid() + '*'):
                os.remove(filename)
        os.remove(self.prop_item_path())

    def exposure_program(self):
        return self._info.get(self._info.EXPOSURE_PROGRAM, None)

    def exposure_time(self):
        et = self._info.get(self._info.EXPOSURE_TIME, None)
        if et is None:
            return None
        else:
            return '%d/%d' % (et[0], et[1])

    def flash(self):
        return self._info.get(self._info.FLASH, None)

    def focal_length(self):
        fl = self._info.get(self._info.FOCAL_LENGTH, None)
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

        add_info('Date:', self.strtime())
        add_info('Name:', self.name(True))
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
            gps_dict = self._info.get(self._info.GPS_INFO, None)
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
        iso = self._info.get(self._info.ISO, None)
        if iso is None:
            return None
        else:
            return '%d' % iso

    def manufactor(self):
        return self._info.get(self._info.MANUFACTOR, None)

    def model(self):
        return self._info.get(self._info.MODEL, None)

    def nxt(self):
        return base_item_props.nxt(self, excluded_types=[itemlist])

    def orientation(self):
        return self._info.get(self._info.ORIENTATION, None)

    def parent(self):
        if self._parent is None:
            self._parent = itemlist(os.path.dirname(self._rel_path), prefix=self._prefix, request_args=self._request_args)
        return self._parent

    def prop_citem_path(self):
        return os.path.join(config.citem_folder, self.uid() + '.prop')

    def prv(self):
        return base_item_props.prv(self, excluded_types=[itemlist])

    def raw_x(self):
        return self._info.get(self._info.WIDTH, config.webnail_size)

    def raw_y(self):
        return self._info.get(self._info.HEIGHT, config.webnail_size)

    def resolution(self):
        if self.raw_x() is None or self.raw_y() is None:
            return None
        else:
            return '%dx%d' % (self.raw_x(), self.raw_y())

    def stay_time(self):
        return 4

    def strtime(self):
        return time.strftime("%d.%m.%Y - %H:%M:%S", time.gmtime(self.time()))

    def template(self):
        return 'picture.html'

    def thumbnail_item_path(self):
        return self._cimage_item_path(config.thumbnail_size)

    def thumbnail_url(self):
        return config.url_prefix + prefix_thumbnail + '/' + self.url(True) or ''

    def thumbnail_x(self):
        if not self._thumbnail_x:
            self._calc_thumbnail_res()
        return self._thumbnail_x or config.thumbnail_size

    def thumbnail_xy_max(self):
        return max(self.thumbnail_x(), self.thumbnail_y())

    def thumbnail_y(self):
        if not self._thumbnail_y:
            self._calc_thumbnail_res()
        return self._thumbnail_y or config.thumbnail_size

    def time(self):
        return self._info.get(self._info.TIME, 0)

    def webnail_item_path(self):
        return self._cimage_item_path(config.webnail_size)

    def webnail_url(self):
        return config.url_prefix + prefix_webnail + '/' + self.url(True) or ''

    def webnail_x(self):
        if not self._webnail_x:
            self._calc_webnail_res()
        return self._webnail_x or config.webnail_size

    def webnail_y(self):
        if not self._webnail_y:
            self._calc_webnail_res()
        return self._webnail_y or config.webnail_size

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
            logger.info('creating citem (%d) for %s', size, self.name())
            try:
                p = picture_edit(self.raw_path())
                p.resize(size)
                p.rotate(self.orientation())
            except IOError:
                logger.error('error creating citem (%d) for %s', size, self.name())
            else:
                try:
                    p.save(self._cimage_item_path(size))
                except IOError:
                    logger.error('error creating citem (%d) for %s', size, self.name())
                else:
                    self._citem_info[VERSION] = __version__ + this_method_version
                    try:
                        with open(self.prop_citem_path(), 'w') as fh:
                            fh.write(json.dumps(self._citem_info, sort_keys=True, indent=4))
                    except IOError:
                        logger.warning('Error while writing cache file (%s)', self._cache_filename)

    def _get_jpg_size(self, filename):
        import struct
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
