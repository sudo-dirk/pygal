#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from pylibs import caching
import calendar
from pylibs import fstools
import os
from PIL import Image
from PIL import ImageEnhance
from pylibs import report
import time

__version__ = '0.0.9'

from __init__ import base_info


class picture_edit(report.logit):
    LOG_PREFIX = 'PicEdit:'

    """
    Class to edit a picture. That means things like resize, rotate, join, ...

    :param str,file file_info: Name or Filehandle of the picture

    **Example:**

    .. code-block:: python

        pe = picture_edit(os.path.join(basepath, 'example', 'picture2.jpg'))
        pe.resize(300)
        pe.rotate(pe.ORIENTATION_RIGHT)
        icon = picture_edit(os.path.join(basepath, 'example', 'movie_96.png'))
        pe.join(icon, pe.JOIN_TOP_RIGHT)
        pe.save(os.path.join(basepath, 'picture2_300R.jpg'))

    This will create the picture *picture2_300R.jpg*. The picture is:

        * resized to a maximum size of 300 pixel
        * rotateted right (90°)
        * an icon has joint the picture in the top right edge
    """
    ORIENTATION_LEFT = 8
    ORIENTATION_RIGHT = 6
    ORIENTATION_TOP_DOWN = 3
    JOIN_TOP_LEFT = 1
    JOIN_TOP_RIGHT = 2
    JOIN_BOT_LEFT = 3
    JOIN_BOT_RIGHT = 4
    JOIN_CENTER = 5

    def __init__(self, file_info):
        self._file = file_info
        self._im = None

    def _filename(self):
        try:
            return os.path.basename(self._file)
        except AttributeError:  # seems to be a filehandle or so
            return '-'

    def get(self):
        """
        This returns a picture instance.

        :returns: PIL Image instance
        """
        if self._im is None:
            self._load_im()
        return self._im

    def resize(self, max_size, logger=None):
        """
        This resizes the picture without changing the ratio.

        :param max_size: The maximum size of x, y.
        """
        self.logit_debug(logger, 'Resizing picture %s to max %d pixel in whatever direction', self._filename(), max_size)
        if self._im is None:
            self._load_im()
        x, y = self._im.size
        xy_max = max(x, y)
        self._im = self._im.resize((int(x * float(max_size) / xy_max), int(y * float(max_size) / xy_max)), Image.NEAREST).rotate(0)

    def rotate(self, orientation, logger=None):
        """
        This rotates the picture.

        :param orientation: Orientation Information. See also self.ORIENTATION_*

        .. note::
          The orientation parameter can be taken from the exif-orientation to create a picture in the correct orientation.
        """
        angle = None
        if orientation == 3:
            angle = 180
        elif orientation == 6:
            angle = 270
        elif orientation == 8:
            angle = 90
        if angle is not None:
            self.logit_debug(logger, 'Rotating picture %s by %d°', self._filename(), angle)
            if self._im is None:
                self._load_im()
            self._im = self._im.rotate(angle, expand=True)

    def save(self, filename, logger=None):
        """
        This saves the picture.

        :param filename: The name and path of the file which will be created.

        .. note::
          The fileformat is **always** *JPEG*.
        """
        self.logit_debug(logger, 'Saving original file %s to %s', self._filename(), os.path.basename(filename))
        if self._im is not None:
            with open(filename, 'w') as fh:
                im = self._im.convert('RGB')
                im.save(fh, 'JPEG')

    def join(self, picture, joint_pos=JOIN_TOP_RIGHT, opacity=0.7, logger=None):
        """
        This joins another picture to this one.

        :param picture_edit picture: The picture to be joint.
        :param joint_pos: The position of picture in this picture. See also self.JOIN_*
        :param float opacity: The opacity of picture when joint (value between 0 and 1).

        .. note::
          joint_pos makes only sense if picture is smaller than this picture.
        """
        self.logit_debug(logger, 'Joining %s to %s', picture._filename(), self._filename())
        im2 = picture.get()
        im2 = self._rgba_copy(im2)
        # change opacity of im2
        alpha = im2.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        im2.putalpha(alpha)

        if self._im is None:
            self._load_im()
        self._im = self._rgba_copy(self._im)

        # create a transparent layer
        layer = Image.new('RGBA', self._im.size, (0, 0, 0, 0))
        # draw im2 in layer
        if joint_pos == self.JOIN_TOP_LEFT:
            layer.paste(im2, (0, 0))
        elif joint_pos == self.JOIN_TOP_RIGHT:
            layer.paste(im2, ((self._im.size[0] - im2.size[0]), 0))
        elif joint_pos == self.JOIN_BOT_LEFT:
            layer.paste(im2, (0, (self._im.size[1] - im2.size[1])))
        elif joint_pos == self.JOIN_BOT_RIGHT:
            layer.paste(im2, ((self._im.size[0] - im2.size[0]), (self._im.size[1] - im2.size[1])))
        elif joint_pos == self.JOIN_CENTER:
            layer.paste(im2, (int((self._im.size[0] - im2.size[0]) / 2), int((self._im.size[1] - im2.size[1]) / 2)))

        self._im = Image.composite(layer, self._im, layer)

    def _load_im(self):
        self._im = Image.open(self._file)

    def _rgba_copy(self, im):
        if im.mode != 'RGBA':
            return im.convert('RGBA')
        else:
            return im.copy()


def coordinates(gps_exif):
    # GPS_TAGS = {
    #    0x0000: ('GPSVersionID', ),
    #    0x0001: ('GPSLatitudeRef', ),
    #    0x0002: ('GPSLatitude', ),
    #    0x0003: ('GPSLongitudeRef', ),
    #    0x0004: ('GPSLongitude', ),
    #    0x0005: ('GPSAltitudeRef', ),
    #    0x0006: ('GPSAltitude', ),
    #    0x0007: ('GPSTimeStamp', ),
    #    0x0008: ('GPSSatellites', ),
    #    0x0009: ('GPSStatus', ),
    #    0x000A: ('GPSMeasureMode', ),
    #    0x000B: ('GPSDOP', ),
    #    0x000C: ('GPSSpeedRef', ),
    #    0x000D: ('GPSSpeed', ),
    #    0x000E: ('GPSTrackRef', ),
    #    0x000F: ('GPSTrack', ),
    #    0x0010: ('GPSImgDirectionRef', ),
    #    0x0011: ('GPSImgDirection', ),
    #    0x0012: ('GPSMapDatum', ),
    #    0x0013: ('GPSDestLatitudeRef', ),
    #    0x0014: ('GPSDestLatitude', ),
    #    0x0015: ('GPSDestLongitudeRef', ),
    #    0x0016: ('GPSDestLongitude', ),
    #    0x0017: ('GPSDestBearingRef', ),
    #    0x0018: ('GPSDestBearing', ),
    #    0x0019: ('GPSDestDistanceRef', ),
    #    0x001A: ('GPSDestDistance', )
    # }
    """
    GPS tags
    """
    def lat_lon_cal(lon_or_lat):
        lon_lat = 0.
        fac = 1.
        for num, denum in lon_or_lat:
            lon_lat += float(num) / float(denum) * fac
            fac *= 1. / 60.
        return lon_lat
    try:
        return dict((('lat', lat_lon_cal(gps_exif[0x0002])), ('lon', lat_lon_cal(gps_exif[0x0004]))))
    except KeyError:
        return None


def exiftime_to_gmtime(exif_time):
    tm_tup = time.strptime(exif_time, "%Y:%m:%d %H:%M:%S")
    return calendar.timegm(tm_tup)


def strip(txt):
    return txt.strip()


class picture_info(base_info):
    LOG_PREFIX = 'PicInfo:'

    """Class to hold and handle information of a picture. See also parent class :py:class:`multimedia.base_info`.

    :param str filename: Name of the picture

    **Example:**

    .. code-block:: python

        p = picture_info(os.path.join(basepath, 'example', 'picture1.jpg'))
        for key in p.keys():
            print key, type(p.get(key)), p.get(key)

    Will result to the following output:

    .. code-block:: text

        orentation <type 'int'> 8
        height <type 'int'> 2736
        width <type 'int'> 3648
        time <type 'int'> 1414690147
        model <type 'unicode'> DSC-HX9V
        manufactor <type 'unicode'> SONY
    """
    DATA_VERSION_NUMBER = 0.2
    EXIF_TAGS = {
        0x0100: ('ImageWidth', ),
        0x0101: ('ImageLength', ),
        0x0102: ('BitsPerSample', ),
        0x0103: ('Compression',
                 {1: 'Uncompressed TIFF',
                  6: 'JPEG Compressed'}),
        0x0106: ('PhotometricInterpretation', ),
        0x010A: ('FillOrder', ),
        0x010D: ('DocumentName', ),
        0x010E: ('ImageDescription', ),
        0x010F: ('Make', ),
        0x0110: ('Model', ),
        0x0111: ('StripOffsets', ),
        0x0112: ('Orientation',
                 {1: 'Horizontal (normal)',
                  2: 'Mirrored horizontal',
                  3: 'Rotated 180',
                  4: 'Mirrored vertical',
                  5: 'Mirrored horizontal then rotated 90 CCW',
                  6: 'Rotated 90 CW',
                  7: 'Mirrored horizontal then rotated 90 CW',
                  8: 'Rotated 90 CCW'}),
        0x0115: ('SamplesPerPixel', ),
        0x0116: ('RowsPerStrip', ),
        0x0117: ('StripByteCounts', ),
        0x011A: ('XResolution', ),
        0x011B: ('YResolution', ),
        0x011C: ('PlanarConfiguration', ),
        0x0128: ('ResolutionUnit',
                 {1: 'Not Absolute',
                  2: 'Pixels/Inch',
                  3: 'Pixels/Centimeter'}),
        0x012D: ('TransferFunction', ),
        0x0131: ('Software', ),
        0x0132: ('DateTime', ),
        0x013B: ('Artist', ),
        0x013E: ('WhitePoint', ),
        0x013F: ('PrimaryChromaticities', ),
        0x0156: ('TransferRange', ),
        0x0200: ('JPEGProc', ),
        0x0201: ('JPEGInterchangeFormat', ),
        0x0202: ('JPEGInterchangeFormatLength', ),
        0x0211: ('YCbCrCoefficients', ),
        0x0212: ('YCbCrSubSampling', ),
        0x0213: ('YCbCrPositioning', ),
        0x0214: ('ReferenceBlackWhite', ),
        0x828D: ('CFARepeatPatternDim', ),
        0x828E: ('CFAPattern', ),
        0x828F: ('BatteryLevel', ),
        0x8298: ('Copyright', ),
        0x829A: ('ExposureTime', ),
        0x829D: ('FNumber', ),
        0x83BB: ('IPTC/NAA', ),
        0x8769: ('ExifOffset', ),
        0x8773: ('InterColorProfile', ),
        0x8822: ('ExposureProgram',
                 {0: 'Unidentified',
                  1: 'Manual',
                  2: 'Program Normal',
                  3: 'Aperture Priority',
                  4: 'Shutter Priority',
                  5: 'Program Creative',
                  6: 'Program Action',
                  7: 'Portrait Mode',
                  8: 'Landscape Mode'}),
        0x8824: ('SpectralSensitivity', ),
        0x8825: ('GPSInfo', ),
        0x8827: ('ISOSpeedRatings', ),
        0x8828: ('OECF', ),
        # print as string
        0x9000: ('ExifVersion', lambda x: ''.join(map(chr, x))),
        0x9003: ('DateTimeOriginal', ),
        0x9004: ('DateTimeDigitized', ),
        0x9101: ('ComponentsConfiguration',
                 {0: '',
                  1: 'Y',
                  2: 'Cb',
                  3: 'Cr',
                  4: 'Red',
                  5: 'Green',
                  6: 'Blue'}),
        0x9102: ('CompressedBitsPerPixel', ),
        0x9201: ('ShutterSpeedValue', ),
        0x9202: ('ApertureValue', ),
        0x9203: ('BrightnessValue', ),
        0x9204: ('ExposureBiasValue', ),
        0x9205: ('MaxApertureValue', ),
        0x9206: ('SubjectDistance', ),
        0x9207: ('MeteringMode',
                 {0: 'Unidentified',
                  1: 'Average',
                  2: 'CenterWeightedAverage',
                  3: 'Spot',
                  4: 'MultiSpot'}),
        0x9208: ('LightSource',
                 {0: 'Unknown',
                  1: 'Daylight',
                  2: 'Fluorescent',
                  3: 'Tungsten',
                  10: 'Flash',
                  17: 'Standard Light A',
                  18: 'Standard Light B',
                  19: 'Standard Light C',
                  20: 'D55',
                  21: 'D65',
                  22: 'D75',
                  255: 'Other'}),
        0x9209: ('Flash', {0: 'No',
                           1: 'Fired',
                           5: 'Fired (?)',  # no return sensed
                           7: 'Fired (!)',  # return sensed
                           9: 'Fill Fired',
                           13: 'Fill Fired (?)',
                           15: 'Fill Fired (!)',
                           16: 'Off',
                           24: 'Auto Off',
                           25: 'Auto Fired',
                           29: 'Auto Fired (?)',
                           31: 'Auto Fired (!)',
                           32: 'Not Available'}),
        0x920A: ('FocalLength', ),
        0x927C: ('MakerNote', ),
        # print as string
        0x9286: ('UserComment', lambda x: ''.join(map(chr, x))),
        0x9290: ('SubSecTime', ),
        0x9291: ('SubSecTimeOriginal', ),
        0x9292: ('SubSecTimeDigitized', ),
        # print as string
        0xA000: ('FlashPixVersion', lambda x: ''.join(map(chr, x))),
        0xA001: ('ColorSpace', ),
        0xA002: ('ExifImageWidth', ),
        0xA003: ('ExifImageLength', ),
        0xA005: ('InteroperabilityOffset', ),
        0xA20B: ('FlashEnergy', ),               # 0x920B in TIFF/EP
        0xA20C: ('SpatialFrequencyResponse', ),  # 0x920C    -  -
        0xA20E: ('FocalPlaneXResolution', ),     # 0x920E    -  -
        0xA20F: ('FocalPlaneYResolution', ),     # 0x920F    -  -
        0xA210: ('FocalPlaneResolutionUnit', ),  # 0x9210    -  -
        0xA214: ('SubjectLocation', ),           # 0x9214    -  -
        0xA215: ('ExposureIndex', ),             # 0x9215    -  -
        0xA217: ('SensingMethod', ),             # 0x9217    -  -
        0xA300: ('FileSource',
                 {3: 'Digital Camera'}),
        0xA301: ('SceneType',
                 {1: 'Directly Photographed'}),
        0xA302: ('CVAPattern',),
    }
    """
    dictionary of main EXIF tag names first element of tuple is tag name, optional second element is another dictionary giving names to values
    """
    HEIGHT = 'ExifImageLength'
    MANUFACTOR = 'Make'
    MODEL = 'Model'
    ORIENTATION = 'Orientation'
    TIME = 'DateTimeOriginal'
    WIDTH = 'ExifImageWidth'
    FLASH = 'Flash'
    FNUMBER = 'FNumber'
    FOCAL_LENGTH = 'FocalLength'
    EXPOSURE_TIME = 'ExposureTime'
    EXPOSURE_PROGRAM = 'ExposureProgram'
    GPS_INFO = 'GPSInfo'
    ISO = 'ISOSpeedRatings'
    TAG_TYPES = {EXPOSURE_TIME: None,
                 EXPOSURE_PROGRAM: EXIF_TAGS[0x8822][1].get,
                 FLASH: EXIF_TAGS[0x9209][1].get,
                 FNUMBER: None,
                 FOCAL_LENGTH: None,
                 GPS_INFO: coordinates,
                 HEIGHT: None,
                 ISO: None,
                 MANUFACTOR: strip,
                 MODEL: strip,
                 ORIENTATION: None,
                 TIME: exiftime_to_gmtime,
                 WIDTH: None}

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

    def _get_exif(self):
        with open(self.filename, 'rb') as ifh:
            im = Image.open(ifh)
            try:
                return dict(im._getexif().items())
            except:
                return {}

    def _get_info(self):
        self._info = dict()
        with open(self.filename, 'rb') as ifh:
            im = Image.open(ifh)
            try:
                exif = dict(im._getexif().items())
            except:
                exif = dict()
            if not self.WIDTH in exif or exif[self.WIDTH] is None:
                exif[self.WIDTH] = im.size[0]
            if not self.HEIGHT in exif or exif[self.HEIGHT] is None:
                exif[self.HEIGHT] = im.size[1]
            for key in exif:
                key_name = self.EXIF_TAGS.get(key, [key])[0]
                if key_name in self.TAG_TYPES:
                    if self.TAG_TYPES[key_name] is not None:
                        self._info[key_name] = self.TAG_TYPES[key_name](exif[key])
                    else:
                        self._info[key_name] = exif[key]

    def __str__(self):
        rv = ''
        exif = self._get_exif()
        for eid in exif:
            try:
                name = self.EXIF_TAGS[eid][0] + ' '
            except KeyError:
                name = ''
            name += '(%#x): ' % eid
            try:
                value = '%s (%d)' % (self.EXIF_TAGS[eid][1][exif[eid]], exif[eid])
            except:
                value = str(exif[eid])
            rv += name + ' ' + value + '\n'
        return rv


class picture_info_cached(picture_info):
    LOG_PREFIX = 'PicInfoCa:'

    """Class to hold and handle information of a picture. See also parent class :py:class:`picture_info`.
    This class caches the information to have a faster access.

    :param str filename: path to the picture
    :param str cache_filename: path to the cache file
    :param logger: Optionally logger instance to use instead of creating one

    **Example:**

    .. code-block:: python

        p = picture_info_cached(os.path.join(basepath, 'example', 'picture1.jpg'), os.path.join(basepath, 'picture1.json'))
        for key in p.keys():
            print key, type(p.get(key)), p.get(key)

    Will result to the following output:

    .. code-block:: text

        orentation <type 'int'> 8
        height <type 'int'> 2736
        width <type 'int'> 3648
        time <type 'int'> 1414690147
        model <type 'unicode'> DSC-HX9V
        manufactor <type 'unicode'> SONY
        gps <type 'dict'> {u'11': [12853, 10000], u'10': u'3', u'13': [2661, 1000], u'12': u'K', u'15': [34519, 100], u'14': u'T', u'17': [23725, 100], u'16': u'M', u'18': u'WGS-84', u'30': 0, u'29': u'2014:10:30', u'1': u'N', u'0': [2, 3, 0, 0], u'3': u'E', u'2': [[53, 1], [59, 1], [35037, 1000]], u'5': 1, u'4': [[11, 1], [22, 1], [30873, 1000]], u'7': [[15, 1], [29, 1], [7951, 1000]], u'6': [8320, 1000], u'9': u'A'}
    """

    def __init__(self, filename, cache_filename, load_all_on_init=True, callback_on_data_storage=None):
        picture_info.__init__(self, filename)
        self._cached_data = caching.property_cache_json(picture_info(filename), cache_filename, load_all_on_init, callback_on_data_storage)

    def get(self, key, default=None, logger=None):
        """
        This gets an information of the picture by a key.

        :param key: The key (name) of the information to get
        :param default: The default value to be returned, if no information with that key exists
        :returns: The information for the given key
        """
        self.logit_debug(logger, "Property request (%s) for %s", key, os.path.basename(self.filename))
        return self._cached_data.get(key, default, logger=logger)
