#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# TODO: video_picture_edit kommentieren und subprocess statt os.popen

from pylibs import caching
import calendar
import os
from pylibs import fstools
from PIL import Image
from pylibs.multimedia.picture import picture_edit
import StringIO
import subprocess
from pylibs import report
import time

__version__ = '0.0.9'

from __init__ import base_info


class video_picture_edit(picture_edit):
    """
    Class to get a picture from a video. . See also parent class :py:class:`multimedia.picture.picture_edit`.

    :param str filename: Name of the picture

    **Example:**

    .. code-block:: python

        vpe = video_picture_edit(os.path.join(basepath, 'example', 'video.3gp'))
        vpe.rotate(vpe.ORIENTATION_LEFT)
        vpe.save(os.path.join(basepath, 'video.jpg'))

    This will create the picture *video.jpg*. The picture is:

        * the first picture of video.3gp
        * rotateted left (90°)
    """
    def save(self, filename):
        """
        This saves the picture.

        :param filename: The name and path of the file which will be created.

        .. note::
          The fileformat is **always** *JPEG*.
        """
        if self._im is None:
            self._load_im()
        picture_edit.save(self, filename)

    def _load_im(self):
        ffmpeg = os.popen('ffmpeg -ss 0.5 -i "' + self._file + '" -vframes 1 -f image2pipe pipe:1 2> /dev/null')
        ffmpeg_handle = StringIO.StringIO(ffmpeg.read())
        if ffmpeg.close() is None:
            self._im = Image.open(ffmpeg_handle)
        vi = video_info(self._file)
        self._im = self._im.resize((vi.get(vi.WIDTH), vi.get(vi.HEIGHT)), Image.NEAREST).rotate(0)


class video_info(base_info):
    LOG_PREFIX = 'VidInfo:'

    """Class to hold and handle information of a video. See also parent class :py:class:`multimedia.base_info`.

    :param str filename: Name of the picture

    **Example:**

    .. code-block:: python

        v = video_info(os.path.join(basepath, 'example', 'video.3gp'))
        for key in v.keys():
            print key, type(v.get(key)), v.get(key)

    Will result to the following output:

    .. code-block:: text

        duration <type 'float'> 3.964
        width <type 'int'> 800
        height <type 'int'> 480
        ratio <type 'str'> 5:3
        time <type 'int'> 1414951903
    """
    DATA_VERSION_NUMBER = 0.2

    TIME = 'time'
    DURATION = 'duration'
    HEIGHT = 'height'
    WIDTH = 'width'
    RATIO = 'ratio'
    TAG_TYPES = {TIME: str,
                 DURATION: float,
                 HEIGHT: int,
                 WIDTH: int,
                 RATIO: str}

    def data_version(self):
        """
        Returns the data creation method version.

        :returns: version number
        :rtype: float
        """
        return self.DATA_VERSION_NUMBER

    def uid(self):
        """
        Returns the uid of the source file.

        :returns: unique id
        :rtype: str
        """
        return fstools.uid(self.filename)

    def _ffprobe_command(self):
        return ['ffprobe', '-v', 'quiet', '-show_format', '-show_streams', self.filename]

    def _avprobe_command(self):
        return ['avprobe', '-v', 'quiet', '-show_format', '-show_streams', self.filename]

    def _get_info(self):
        TAG_TRANSLATION = {'TAG:creation_time': self.TIME,
                           'creation_time': self.TIME,
                           'duration': self.DURATION,
                           'height': self.HEIGHT,
                           'width': self.WIDTH,
                           'display_aspect_ratio': self.RATIO}
        self._info = dict()
        try:
            ffprobe_txt = subprocess.check_output(self._avprobe_command())
        except OSError:
            ffprobe_txt = subprocess.check_output(self._ffprobe_command())
        for line in ffprobe_txt.splitlines():
            try:
                key, val = [snippet.strip() for snippet in line.split('=')]
            except ValueError:
                continue
            else:
                if key in TAG_TRANSLATION and key not in self._info:
                    try:
                        self._info[TAG_TRANSLATION[key]] = self.TAG_TYPES[TAG_TRANSLATION[key]](val)
                    except ValueError:
                        pass
        # rework some information...
        if self.TIME in self._info:
            try:
                self._info[self.TIME] = self._info[self.TIME][:self._info[self.TIME].index('.')]
            except ValueError:
                pass # time string seems to have no '.' 
            self._info[self.TIME] = self._info[self.TIME].replace('T', ' ').replace('/', '').replace('\\', '')
            format_string = '%Y-%m-%d %H:%M:%S'
            try:
                self._info[self.TIME] = calendar.timegm(time.strptime(self._info[self.TIME], format_string))
            except ValueError:
                self._info[self.TIME] = 1
        if self.WIDTH in self._info and self.RATIO in self._info:
            x, y = [int(num) for num in self._info[self.RATIO].replace('\\', '').split(':')]
            if x != 0 and y != 0:
                self._info[self.HEIGHT] = int(round(self._info[self.WIDTH] * float(y) / float(x)))

    def __str__(self):
        try:
            return subprocess.check_output(self._avprobe_command())
        except OSError:
            return subprocess.check_output(self._ffprobe_command())


class video_info_cached(video_info):
    LOG_PREFIX = 'VidInfoCa:'

    """Class to hold and handle information of a video. See also parent class :py:class:`video_info`.
    This class caches the information to have a faster access.

    :param str filename: path to the picture
    :param str cache_filename: path to the cache file
    :param logger: Optionally logger instance to use instead of creating one

    **Example:**

    .. code-block:: python

        v = video_info_cached(os.path.join(basepath, 'example', 'video.3gp'))
        for key in v.keys():
            print key, type(v.get(key)), v.get(key)

    Will result to the following output:

    .. code-block:: text

        duration <type 'float'> 3.964
        width <type 'int'> 800
        height <type 'int'> 480
        ratio <type 'str'> 5:3
        time <type 'int'> 1414951903
    """

    def __init__(self, filename, cache_filename, load_all_on_init=True):
        video_info.__init__(self, filename)
        self._cached_data = caching.property_cache_json(video_info(filename), cache_filename, load_all_on_init)

    def get(self, key, default=None, logger=None):
        """
        This gets an information of the video by a key.

        :param key: The key (name) of the information to get
        :param default: The default value to be returned, if no information with that key exists
        :returns: The information for the given key
        """
        self.logit_debug(logger, "Property request (%s) for %s", key, os.path.basename(self.filename))
        return self._cached_data.get(key, default, logger=logger)
