#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Open Streetmap
==============

**Author:** Dirk Alders <d.alders@arcor.de>
"""

import math

__VERSION__ = '0.1.2'


MAP_STANDARD = 'N'
"""MAP definition for Standard Map"""
MAP_LOCAL_TRAFIC = 'TN'
"""MAP definition for Local Trafic Map"""
MAP_CYCLEMAP = 'CN'
"""MAP definition for Cyclemap"""
MAP_HUMANITARIAN = 'HN'
"""MAP definition for Humanitarian Map"""


class coordinates(dict):
    LATITUDE = 'lat'
    LONGITUDE = 'lon'
    """This generates a dictionary including lat and lon.

    .. warning:: Documentation
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __unicode__(self):
        return unicode(self.__str__())

    def __str__(self):
        def to_string(lon_or_lat, plus_minus=('N', 'S')):
            degrees = int(lon_or_lat)
            lon_or_lat -= degrees
            minutes = int(lon_or_lat * 60)
            lon_or_lat = lon_or_lat * 60 - minutes
            seconds = lon_or_lat * 60
            pm = 0 if degrees >= 0 else 1
            return u"%d°%d'%.4f''%s" % (abs(degrees), abs(minutes), abs(seconds), plus_minus[pm])
        lon = self.get(self.LONGITUDE)
        lat = self.get(self.LATITUDE)
        return to_string(lat) + ' ' + to_string(lon, ['E', 'W'])


def landmark_link(coordinates, zoom_level=13, map_code=MAP_STANDARD):
    """This generates an url for marking a position in a map.

    .. warning:: Documentation
    """
    link = 'http://www.openstreetmap.org?mlat=%(' + coordinates.LATITUDE + ')f&mlon=%(' + coordinates.LONGITUDE + ')f&zoom=%(zoom)d&layers=%(map)s'
    return link % {coordinates.LATITUDE: coordinates[coordinates.LATITUDE],
                   coordinates.LONGITUDE: coordinates[coordinates.LONGITUDE],
                   'zoom': zoom_level,
                   'map': map_code}
