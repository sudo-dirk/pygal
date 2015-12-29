#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# requirements: python-flask (>= 0.1.), python-pillow, ffmpeg


# TODO: - "python pygal.py -c" zum Erzeugen des Cache funktioniert nicht...
#       - pylibs in Orner pylibs verschieben und anpassen
#       - Berechtigungen im Auth File mit regex? statt Liste von Startwith...
#       - Suche führt zu Elementen, die wiederum zu einer Exception führen.
#       - Bei Suche die Actions Info, Download korrigieren (Info und Download der Suchergebnisse)
#       - Session nur für die jeweilige Unterseite anlegen (Test ob tiefere Seiten okay)
#       - Config Klasse zum Handeln von Parametern (Session, cfg-Datei, ....); webnail-size als session-parameter und default in user-data?
#       - __user__ - Seite implementieren, um Änderungen vornehmen zu können
#       - E-Mailbenachrichtigung bei neuem Benutzer
#       - Kurze Namen (Anfa...nde) (laenge aus pygal_config), onMouseover: Voller Name anzeigen
#       - Fehler abfangen (Zugriffsrechte items, cache, user.json)
#       - Sonderfunktionen hinzu (z.B.: Kommentar, Gruppeninfo für Rechte)

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
    parser.add_option("-c", "--cache", action="store_true", dest="cache", default=False, help="create the complete cached files (only)")
    (options, args) = parser.parse_args()
    if options.cache:
        il = cached_itemlist("", ignore_rights=True)
        il.create_thumbnail()
        il.create_webnail()
    else:
        app.run(config.ip_to_serve_from, 5000)
