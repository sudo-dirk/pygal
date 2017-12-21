#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from items import base_item_props
from pylibs.multimedia.picture import picture_edit
from pylibs.multimedia.video import video_info_cached
from pylibs.multimedia.video import video_picture_edit
from pylibs.multimedia.video import __version__
from pylibs import fstools
import json
import os
from picture import picture
from pygal import logger


class video(picture):
    LOG_PREFIX = 'video:'
    mime_types = {'avi': 'video/x-msvideo', 'mpg': 'video/mpeg', 'mpeg': 'video/mpeg', 'mpe': 'video/mpeg', 'mov': 'video/quicktime', 'qt': 'video/quicktime', 'mp4': 'video/mp4', 'webm': 'video/webm', 'ogv': 'video/ogg', 'flv': 'video/x-flv', '3gp': 'video/3gpp'}
    required_prop_keys = ['raw_x', 'raw_y', 'time', 'duration']
    internal_player = ['mp4', 'webm', 'ogv', 'flv', '3gp']
    prop_vers = 0.100

    def __init__(self, rel_path, request_args={}, parent=None, **kwargs):
        base_item_props.__init__(self, rel_path, request_args=request_args, parent=parent)
        self._info = video_info_cached(self.raw_path(), self.prop_item_path())
        self._citem_info = None

        self._parent = None
        self._prv = None
        self._nxt = None
        self._thumbnail_x = None
        self._thumbnail_y = None
        self._webnail_x = None
        self._webnail_y = None

    def num_pic(self):
        return 0

    def num_vid(self):
        return 1

    def num_gal(self):
        return 0

    def duration(self):
        duration = self._info.get(self._info.DURATION, logger=logger)
        if duration is None:
            return None
        else:
            return '%.1fs' % (duration)

    def get_infos(self):
        infos = list()

        def add_info(desc, info):
            if info is not None:
                infos.append([desc, info])

        add_info('Date:', self.strtime())
        add_info('Name:', self.name(True))
        add_info('Size:', self.strfilesize())
        add_info('Resolution:', self.resolution())
        add_info('Duration:', self.duration())
        add_info('UID:', self.uid())
        return infos

    def stay_time(self):
        if self.raw_ext() in self.internal_player:
            return self._info.get(self._info.DURATION, 2, logger=logger) + 2
        else:
            return picture.stay_time(self)

    def template(self):
        if self.raw_ext() in self.internal_player:
            return 'video.html'
        else:
            return 'picture.html'

    def _create_citem(self, size, force=False):
        this_method_version = '0.1.0'
        if self._citem_info is None:
            try:
                with open(self.prop_citem_path(), 'r') as fh:
                    self._citem_info = json.loads(fh.read())
            except:
                self._citem_info = dict()
        VERSION = '__module_version_citem_creation_%d__' % size
        WATERMARK = '__watermark_uid_citem_creation_%d__' % size
        watermark_path = os.path.join(os.path.join(os.path.dirname(__file__), '..'), 'theme', 'static', 'common', 'img', 'thumbnail_movie.png')
        if force or not os.path.exists(self._cimage_item_path(size)) or self._citem_info.get(VERSION) != __version__ + this_method_version or self._citem_info.get(WATERMARK) != fstools.uid(watermark_path):
            self.logit_info(logger, 'creating citem (%d) for %s', size, self.name())
            try:
                p = video_picture_edit(self.raw_path())
                p.resize(size, logger=logger)
                movie_icon = picture_edit(watermark_path)
                p.join(movie_icon, p.JOIN_TOP_RIGHT, 0.75, logger=logger)
            except IOError:
                self.logit_error(logger, 'error creating citem (%d) for %s', size, self.name())
            else:
                try:
                    p.save(self._cimage_item_path(size))
                except IOError:
                    self.logit_error(logger, 'error creating citem (%d) for %s', size, self.name())
                else:
                    self._citem_info[VERSION] = __version__ + this_method_version
                    self._citem_info[WATERMARK] = fstools.uid(watermark_path)
                    try:
                        with open(self.prop_citem_path(), 'w') as fh:
                            fh.write(json.dumps(self._citem_info, sort_keys=True, indent=4))
                    except IOError:
                        self.logit_warning(logger, 'Error while writing cache file (%s)', self._cache_filename)
