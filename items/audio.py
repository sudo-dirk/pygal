#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import helpers
import items
from items.database import indexed_search
import os
from pylibs.audio.mp3 import audio_info_cached
from pylibs import fstools

import logging
logger = logging.getLogger('app logger')


def is_audio(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in audio.mime_types.keys()


class audio(items.base_item):
    TYPE = items.TYPE_AUDIO
    LOG_PREFIX = 'audio:'
    mime_types = {'mp3': 'audio/mpeg'}  # TODO: add and test -> , 'ogg': 'audio/ogg', 'wav': 'audio/wav'}

    def __init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user, disable_whoosh):
        items.base_item.__init__(self, rel_path, base_path, slideshow, db_path, cache_path, force_user, disable_whoosh)
        self._info_filename = helpers.info_filename_by_relpath(rel_path)
        if disable_whoosh:
            self._info = audio_info_cached(self.raw_path(), self._info_filename)
        else:
            self._info = audio_info_cached(self.raw_path(), self._info_filename, callback_on_data_storage=self._info_data_changed)

    def _info_data_changed(self):
        isearch = indexed_search()
        isearch.update_document_by_rel_path(self._rel_path)
        self.logit_debug(logger, 'Item-Data changed => updating index for %s', self.name())

    def album(self):
        return helpers.decode(self._info.get(self._info.ALBUM, logger=logger) or '-')

    def bitrate(self):
        return self._info.get(self._info.BITRATE, logger=logger)

    def cache_data(self):
        #return items.base_item.cache_data(self)
        rv = list()
        entry = list()
        entry.append('User data')
        entry.append(helpers.decode(self._db_filename))
        rv.append(entry)
        entry = list()
        entry.append('Item data')
        entry.append(helpers.decode(self._info_filename))
        rv.append(entry)
        # Add Link
        for i in range(0, len(rv)):
            rv[i].append(self.info_url(i))
        return rv

    def duration(self):
        return self._info.get(self._info.DURATION, logger=logger)

    def genre(self):
        return helpers.decode(self._info.get(self._info.GENRE, logger=logger) or '-')

    def get_infos(self, short=False):
        if short:
            infos = []
        else:
            infos = items.base_item.get_infos(self)
        infos.append(helpers.simple_info('Artist:', self.interpret()))
        infos.append(helpers.simple_info('Album:', self.album()))
        infos.append(helpers.simple_info('Genre:', self.genre()))
        infos.append(helpers.simple_info('Duration:', self.str_duration()))
        infos.append(helpers.simple_info('Bitrate:', str(self.str_bitrate())))
        infos.append(helpers.simple_info('Year:', str(self.year())))
        infos.append(helpers.simple_info('Track:', str(self.track())))
        return infos

    def interpret(self):
        return helpers.decode(self._info.get(self._info.ARTIST, logger=logger) or '-')

    def mime_type(self):
        return self.mime_types[os.path.splitext(self._rel_path)[1][1:]]

    def name(self, full_name=False):
        track = self.track()
        name = self._info.get(self._info.TITLE, None, logger=logger)
        if name is not None and track is not None:
            return helpers.decode('%02d - %s' % (track, name))
        if name is not None:
            return helpers.decode(name)
        return items.base_item.name(self, full_name=full_name)

    def stay_time(self):
        return self.duration() or 10 + 2

    def str_bitrate(self):
        bitrate = int(self.bitrate())
        return '%d.%02d kbit/s' % (bitrate/1000, bitrate%1000/10)

    def str_duration(self):
        duration = int(self.duration())
        return '%d:%02d' % (duration/60, duration%60)

    def time(self):
        return 0

    def track(self):
        return self._info.get(self._info.TRACK, logger=logger) or 0

    def uid(self):
        return fstools.uid(self.raw_path())

    def year(self):
        return self._info.get(self._info.YEAR, logger=logger) or 0