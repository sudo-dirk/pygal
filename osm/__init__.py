#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Open Streetmap
==============

**Author:** Dirk Alders <d.alders@arcor.de>
"""

import math

MAP_MAPNIK = 'M'
"""MAP definition for Mapnik"""
MAP_OSMARENDER = 'O'
"""MAP definition for Osmarender"""
MAP_CYCLEMAP = '0'
"""MAP definition for Cyclemap"""
MAP_NONAME = 'N'
"""MAP definition for Noname"""


class coordinates(dict):
    LATITUDE = 'lat'
    LONGITUDE = 'lon'
    """This generates a dictionary including lat and lon.

    .. warning:: Documentation
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

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


def landmark_link(coordinates, zoom_level=13, map_code=MAP_MAPNIK):
    """This generates an url for marking a position in a map.

    .. warning:: Documentation
    """
    link = 'http://www.openstreetmap.org/?mlat=%(' + coordinates.LATITUDE + ')f&mlon=%(' + coordinates.LONGITUDE + ')f&zoom=%(zoom)d&layers=%(map)s'
    return link % {'lat': coordinates['lat'],
                   'lon': coordinates['lon'],
                   'zoom': zoom_level,
                   'map': map_code}

if __name__ == '__main__':
    c = coordinates((('lat', -14.128044), ('lon', 22.500000)))
    print c.__str__().encode('utf-8')
    print landmark_link(c)
