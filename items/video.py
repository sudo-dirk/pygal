#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from helpers import simple_info
import items
from .picture import picture
import json
import logging
import os
import pygal_config as config
from pylibs import fstools
from pylibs.multimedia.picture import picture_edit
from pylibs.multimedia.video import __version__
from pylibs.multimedia.video import video_info_cached
from pylibs.multimedia.video import video_picture_edit


logger = logging.getLogger('pygal.items.video')


def is_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in video.mime_types.keys()


class video(picture):
    TYPE = items.TYPE_VIDEO
    LOG_PREFIX = 'video:'
    mime_types = {'avi': 'video/x-msvideo', 'mpg': 'video/mpeg', 'mpeg': 'video/mpeg', 'mpe': 'video/mpeg', 'mov': 'video/quicktime', 'qt': 'video/quicktime', 'mp4': 'video/mp4', 'webm': 'video/webm', 'ogv': 'video/ogg', 'flv': 'video/x-flv', '3gp': 'video/3gpp'}
    internal_player = ['mp4', 'webm', 'ogv', 'flv', '3gp']

    def __init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user, disable_whoosh):
        items.base_item.__init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user, disable_whoosh)
        self._xnail_info = None
        self._xnail_info_filename = os.path.join(cache_path, self.uid() + '.json')
        self._citem_filename = os.path.join(cache_path, self.uid() + '_%s.jpg')
        self._info_filename = os.path.join(cache_path, self.uid() + '_info.json')
        if disable_whoosh:
            self._info = video_info_cached(self.raw_path(), self._info_filename)
        else:
            self._info = video_info_cached(self.raw_path(), self._info_filename, callback_on_data_storage=self._info_data_changed)

    def _create_citem(self, size, force=False, logger=None):
        this_method_version = '0.1.2'
        if self._xnail_info is None:
            try:
                with open(self._xnail_info_filename, 'r') as fh:
                    self._xnail_info = json.loads(fh.read())
            except:
                self._xnail_info = dict()
        VERSION = '__module_version_citem_creation_%d__' % size
        WATERMARK = '__watermark_uid_citem_creation_%d__' % size
        watermark_path = os.path.join(config.theme_path, 'static', 'overlay', 'movie.png')
        if force or not os.path.exists(self.citem_filename(size)) or self._xnail_info.get(VERSION) != __version__ + this_method_version or self._xnail_info.get(WATERMARK) != fstools.uid(watermark_path):
            self.logit_info(logger, 'creating citem (%d) for %s', size, self.name())
            try:
                p = video_picture_edit(self.raw_path())
                p.resize(size, logger=logger)
                movie_icon = picture_edit(watermark_path)
                p.join(movie_icon, p.JOIN_TOP_RIGHT, 0.85, logger=logger)
            except IOError:
                self.logit_error(logger, 'error creating citem (%d) for %s', size, self.name())
            else:
                try:
                    p.save(self._citem_filename %size)
                except IOError:
                    self.logit_error(logger, 'error creating citem (%d) for %s', size, self.name())
                else:
                    self._xnail_info[VERSION] = __version__ + this_method_version
                    self._xnail_info[WATERMARK] = fstools.uid(watermark_path)
                    try:
                        with fstools.open_locked(self._xnail_info_filename, 'w') as fh:
                            fh.write(json.dumps(self._xnail_info, sort_keys=True, indent=4))
                    except IOError:
                        self.logit_warning(logger, 'Error while writing cache file (%s)', self._cache_filename)

    def duration(self):
        duration = self._info.get(self._info.DURATION, logger=logger)
        if duration is None:
            return None
        else:
            return '%.1fs' % (duration)

    def get_infos(self):
        infos = items.base_item.get_infos(self)
        infos.append(simple_info('Date:', self.strtime()))
        infos.append(simple_info('Name:', self.name(True)))
        infos.append(simple_info('Size:', self.strfilesize()))
        infos.append(simple_info('Resolution:', self.resolution()))
        infos.append(simple_info('Duration:', self.duration()))
        infos.append(simple_info('UID:', self.uid()))
        return infos

    def mime_type(self):
        return self.mime_types[os.path.splitext(self._rel_path)[1][1:]]

    def orientation(self):
        # TODO: implement orientation if available
        return 0

    def stay_time(self):
        if os.path.splitext(self._rel_path)[1][1:] in self.internal_player:
            return self._info.get(self._info.DURATION, 2, logger=logger) + 2
        else:
            return picture.stay_time(self)

    def use_internal_player(self):
        return os.path.splitext(self._rel_path)[1][1:] in self.internal_player
