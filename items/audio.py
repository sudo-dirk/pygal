#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import items
import os


def is_audio(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in audio.mime_types.keys()


class audio(items.base_item):
    TYPE = items.TYPE_AUDIO
    LOG_PREFIX = 'audio:'
    mime_types = {'mp3': 'audio/mpeg'}  # TODO: add and test -> , 'ogg': 'audio/ogg', 'wav': 'audio/wav'}

    def mime_type(self):
        return self.mime_types[os.path.splitext(self._rel_path)[1][1:]]

    def stay_time(self):
        # TODO: use stay_time from file parameters (after id3 had been implemented)
        return 60
