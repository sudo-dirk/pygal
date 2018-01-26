#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# requirements: python-flask (>= 0.1.), python-pillow, ffmpeg


# TODO: - Der Bereich Admin, Upload, ... ist zu breit und der Anzeigename zu schmal. Prüfen des Verhaltens bei schmaler werdendem Fenster.
#       - Bildgröße in Staging Area scheint zwischen Rahmen und Bild unterschiedlich zu sein (Rahmen default?) Anzeige des Namens
#       - Aufklappen der Bäume im Admin-Dialog prüfen und neu festlegen + Bilderliste wie overview erzeugen (ggf. durch import von 'overview.html' im template.
#       - Ansicht der Cache Daten verbessern (modal dialog)
#       - Markierung des Ordner beibehalten, wenn in folder structure gewechselt wird zwischen delete und create
#       - Link zum Tag im Bild und in der Leiste nur dann, wenn user_may_edit
#       - Suche in Tag-Files verbessern (whoosh?, indexing) und nach Filenamen, ...?
#       - PullDownMenu bei Administration instead of form element in admin*.html
#       - DEBUG output bei cache generierung immer aktivieren (unabhängig vom Parameter in der config)
#       - switch user implementieren
#       - Timing Anzeige aufhübschen
#       - restlichen str_args -> helpers (login, logout, register, lostpass, userprefs, ...?)
#       - flask.redirect möglichst  eliminieren, vor allem neu eingebautes, da Meldungen hier nicht weitergereicht werden können.
#       - Löschdialog für Ordner (Anzeige aller Elemente)
#       - Staging Area und Delete-Page: Für delete und commit eine Auswahl ermöglichen (commit und delete aus Ordner)
#       - logging ergänzen mit erben der classe report.logit (itemlist, picture, ...)
#       - Sortierung einstellbar machen (Name, Zeit, ...) Änderung führt dazu, dass der Cache ungültig wird => Userdata und nicht Sessiondata
#       - required attribut für js-tree in admin.staging
#       - delete cache auf Seitenebene für Administratoren einführen
#       - Problem mit png und mit Bild in Linde/orig (Ausrichtung) - Test mit originaldaten erforderlich
#       - Zusätzlich Infos auf Info-Seite für itemlist (Datum, uid, ) siehe Bilder
#       - Select all Button bei der Administration der Rechte hinzufügen
#       - Beispieldaten einfügen
#       - Erweiterte Suche einbauen. Zugang über flash-Bereich analog login.
#       - Nach texten auf der Oberfläche suchen, die in das Modul lang gehören (z.B.: Button- und Labeltexte)
#       - E-Mailbenachrichtigung bei neuem Benutzer und Passwortrücksetzung, Upload, ...
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
from auth import user_data_handler

static_folder = os.path.join('theme', 'static')
template_folder = os.path.join('theme', 'templates')

if __name__ == "__main__":
    from pygal_config import url_prefix
else:
    url_prefix = ''

if len(url_prefix) > 1:
    app = flask.Flask('pygal', static_folder=static_folder, template_folder=template_folder, static_url_path=url_prefix + '/static')
else:
    app = flask.Flask('pygal', static_folder=static_folder, template_folder=template_folder)

# set session lifetime, name, url_prefix
app.permanent_session_lifetime = timedelta(days=90)
app.config['SESSION_COOKIE_NAME'] = 'pygal_session'
app.config['SESSION_COOKIE_PATH'] = url_prefix or '/'

# creating logger for usage in other modules
app.debug_log_format = """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
File "%(pathname)s", line %(lineno)d, in %(funcName)s
%(asctime)s: %(levelname)-7s - %(message)s'"""

app.logger.setLevel(logging.DEBUG)

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
    from app.items.views import item_view
    return item_view('')

from app.base_func import base_func
app.register_blueprint(base_func, url_prefix=url_prefix)
from app.items import item
app.register_blueprint(item, url_prefix=url_prefix)


if __name__ == "__main__":
    import pygal_config as config
    from items import itemlist

    parser = optparse.OptionParser("usage: %prog [options] arg1 arg2")
    parser.add_option("-c", "--cache", action="store_true", dest="cache", default=False, help="create the cache files for all items (thumbnails, webnails, property cache)")
    parser.add_option("-d", "--database", action="store_true", dest="database", default=False, help="updates and cleans the database files to the current storage version")
    (options, args) = parser.parse_args()
    if options.cache:
        for user in [''] + user_data_handler().users():
            il = itemlist("", config.item_path, False, config.database_path, config.cache_path, user)
            for i in range(0, len(config.thumbnail_size_list)):
                il.create_thumbnail(i)
            for i in range(0, len(config.webnail_size_list)):
                il.create_webnail(i)
    elif options.database:
        def db_update_cleanup(itemlist):
            for item in itemlist.get_itemlist():
                if item.is_itemlist():
                    db_update_cleanup(item)
                else:
                    if item.db_is_empty():
                        os.remove(item._db_filename)
                    else:
                        item._save_()
        for user in [''] + user_data_handler().users():
            db_update_cleanup(itemlist("", config.item_path, False, config.database_path, config.cache_path, user))
    else:
        app.run(config.ip_to_serve_from, 5000)
