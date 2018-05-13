import subprocess
from pylibs import caching
from pylibs import fstools
import os
import pylibs.multimedia
from subprocess import CalledProcessError


class audio_info(pylibs.multimedia.base_info):
    LOG_PREFIX = 'AudInfo:'

    """Class to hold and handle information of an audio file. See also parent class :py:class:`multimedia.base_info`.

    :param str filename: Name of the audio file

    **Example:**

    .. code-block:: python

        a = audio_info(os.path.join(basepath, 'example', 'music.mp3'))
        for key in a.keys():
            print key, type(a.get(key)), a.get(key)

    Will result to the following output:

    .. code-block:: text

        album <type 'str'> A/B
        title <type 'str'> No Good
        track <type 'int'> 1
        artist <type 'str'> Kaleo
        genre <type 'str'> Rock
        year <type 'int'> 2016
        duration <type 'float'> 236.094694
    """
    DATA_VERSION_NUMBER = 0.2

    ALBUM = 'album'
    ARTIST = 'artist'
    BITRATE = 'bitrate'
    DURATION = 'duration'
    GENRE = 'genre'
    TITLE = 'title'
    TRACK = 'track'
    YEAR = 'year'
    TAG_TYPES = {ALBUM: unicode,
                 ARTIST: unicode,
                 BITRATE: int,
                 DURATION: float,
                 GENRE: unicode,
                 TITLE: unicode,
                 TRACK: int,
                 YEAR: int}

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

    def _get_info(self, logger=None):
        TAG_TRANSLATION = {'TAG:album': self.ALBUM,
                           'TAG:artist': self.ARTIST,
                           'bit_rate': self.BITRATE,
                           'duration': self.DURATION,
                           'TAG:genre': self.GENRE,
                           'TAG:title': self.TITLE,
                           'TAG:track': self.TRACK,
                           'TAG:date': self.YEAR}
        self._info = dict()
        try:
            try:
                ffprobe_txt = subprocess.check_output(self._avprobe_command())
            except OSError:
                ffprobe_txt = subprocess.check_output(self._ffprobe_command())
        except CalledProcessError:
            self.logit_error(logger, "Error processing %s", self.filename)
            ffprobe_txt = ''
        for line in ffprobe_txt.splitlines():
            try:
                key, val = [snippet.strip() for snippet in line.split('=')]
            except ValueError:
                continue
            else:
                if key in TAG_TRANSLATION and key not in self._info:
                    # some special interpretation
                    if key == 'TAG:track' and '/' in val:
                        val = val[:val.index('/')]
                    if key == 'TAG:date' and '-' in val:
                        val = val[:val.index('-')]
                    for i in ['utf-8', 'cp1252']:    
                        try:
                            val = val.decode(i)
                            break
                        except UnicodeEncodeError:
                            pass
                        except UnicodeDecodeError:
                            pass
                    try:
                        self._info[TAG_TRANSLATION[key]] = self.TAG_TYPES[TAG_TRANSLATION[key]](val)
                    except ValueError:
                        if val != '':
                            self.logit_error(logger, "Interpretation failed for %s: key (%s) value (%s)", self.filename, key, val)

    def __str__(self):
        try:
            return subprocess.check_output(self._avprobe_command())
        except OSError:
            return subprocess.check_output(self._ffprobe_command())


class audio_info_cached(audio_info):
    LOG_PREFIX = 'AudInfoCa:'

    """Class to hold and handle information of an audio file. See also parent class :py:class:`audio_info`.
    This class caches the information to have a faster access.

    :param str filename: path to the audio file
    :param str cache_filename: path to the cache file
    :param logger: Optionally logger instance to use instead of creating one

    **Example:**

    .. code-block:: python

        a = audio_info_cached(os.path.join(basepath, 'example', 'audio.mp3'), os.path.join(basepath, 'example', 'audio.json'))
        for key in a.keys():
            print key, type(a.get(key)), a.get(key)

    Will result to the following output:

    .. code-block:: text

        album <type 'str'> A/B
        title <type 'str'> No Good
        track <type 'int'> 1
        artist <type 'str'> Kaleo
        genre <type 'str'> Rock
        year <type 'int'> 2016
        duration <type 'float'> 236.094694
    """

    def __init__(self, filename, cache_filename, load_all_on_init=True, callback_on_data_storage=None):
        audio_info.__init__(self, filename)
        self._cached_data = caching.property_cache_json(audio_info(filename), cache_filename, load_all_on_init, callback_on_data_storage)

    def get(self, key, default=None, logger=None):
        """
        This gets an information of the video by a key.

        :param key: The key (name) of the information to get
        :param default: The default value to be returned, if no information with that key exists
        :returns: The information for the given key
        """
        self.logit_debug(logger, "Property request (%s) for %s", key, os.path.basename(self.filename))
        return self._cached_data.get(key, default, logger=logger)
