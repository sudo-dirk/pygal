#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# requirements: python-flask (>= 0.1.), python-pillow, ffmpeg


# TODO: - delete cache auf Seitenebene für Administratoren einführen
#       - tar statt zip in download + stream statt memory element
#       - Link zum Tag im Bild und in der Leiste nur dann, wenn user_may_edit
#       - Problem mit png und mit Bild in Linde/orig (Ausrichtung) - Test mit originaldaten erforderlich
#       - Zusätzlich Infos auf Info-Seite für itemlist (Datum, uid, ) siehe Bilder
#       - Select all Button bei der Administration der Rechte hinzufügen
#       - Restrukturierung (ggf. Auflösen der Unterscheidung base und item) + imports trennen from ... import a, b, c + imports nach alphabet sortieren
#       - Beispieldaten einfügen (Notwendigkeit auf Produktivsystem eine Liste von Quellen zu verarbeiten)
#       - Erweiterte Suche einbauen. Zugang über flash-Bereich analog login.
#       - Admin-User darf zu einem anderen Benutzer wechseln. Logout führt zu ursprünglichem Nutzer.
#       - Nach texten auf der Oberfläche suchen, die in das Modul lang gehören (z.B.: Button- und Labeltexte)
#       - Suche in Tag-Files verbessern (whoosh?, indexing) und nach Filenamen, ...?
#       - E-Mailbenachrichtigung bei neuem Benutzer und Passwortrücksetzung
###############################################################################################################
#       - Session nur für die jeweilige Unterseite anlegen (Test ob tiefere Seiten okay)
#       - Kurze Namen (Anfa...nde) (laenge aus pygal_config), onMouseover: Voller Name anzeigen
#       - Fehler abfangen (Zugriffsrechte items, cache, user.json)
#       - Sonderfunktionen hinzu (z.B.: Gruppenberechtigungen)


from datetime import timedelta
import flask
import optparse
import os
import logging
from pygal_config import DEBUG
from pygal_config import secret_key

static_folder = os.path.join('theme', 'static')
template_folder = os.path.join('theme', 'templates')

if __name__ == "__main__":
    from pygal_config import url_prefix
else:
    url_prefix = ''

if len(url_prefix) > 1:
    flask
    app = flask.Flask(__name__, static_folder=static_folder, template_folder=template_folder, static_url_path=url_prefix + '/static')
else:
    app = flask.Flask(__name__, static_folder=static_folder, template_folder=template_folder)

# set session lifetime, name, url_prefix
app.permanent_session_lifetime = timedelta(days=90)
app.config['SESSION_COOKIE_NAME'] = 'pygal_session'
app.config['SESSION_COOKIE_PATH'] = url_prefix or '/'

# creating logger for usage in other modules
app.debug_log_format = """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
File "%(pathname)s", line %(lineno)d, in %(funcName)s
%(asctime)s: %(levelname)-7s - %(message)s'"""

logger = app.logger
logger.setLevel(logging.DEBUG)

app.debug = DEBUG
app.secret_key = secret_key
from werkzeug.routing import BaseConverter


class ItemNameConverter(BaseConverter):
    """Like the default :class:`UnicodeConverter`, but it also matches
    slashes (except at the beginning AND end).
    This is useful for wikis and similar applications::
        Rule('/<itemname:wikipage>')
        Rule('/<itemname:wikipage>/edit')
    """
    regex = '[^/]+?(/[^/]+?)*'
    weight = 200
app.url_map.converters['itemname'] = ItemNameConverter


#
# registration of items
#
@app.route(url_prefix + '/' or '/')
def root():
    from app.items.views import item
    return item('')

from app.base_func import base_func
app.register_blueprint(base_func, url_prefix=url_prefix)
from app.items import item
app.register_blueprint(item, url_prefix=url_prefix)


if __name__ == "__main__":
    import pygal_config as config
    from items import cached_itemlist

    parser = optparse.OptionParser("usage: %prog [options] arg1 arg2")
    parser.add_option("-c", "--cache", action="store_true", dest="cache", default=False, help="create the cache files for all items (thumbnails, webnails, property cache)")
    (options, args) = parser.parse_args()
    if options.cache:
        il = cached_itemlist("", create_cache=True)
        il.create_thumbnail()
        il.create_webnail()
    else:
        app.run(config.ip_to_serve_from, 5000)
