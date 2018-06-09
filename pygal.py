#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# requirements: python-flask (>= 0.1.), python-pillow, ffmpeg, python-whoosh


# TODO: Add config specific link-list (Menu-Bar item) for e.g. impressum 
# TODO: Suchstring verbessern bei Suche mit Start bei Tags. Test 2 führt auch zu Test 1
# TODO: Link zur Suche in der Navi-Bar geht nicht (%3F statt ? und %3D statt = (quote...)
# TODO: Play-Symbol in die Mitte bei Videos

# TODO: Implementierung einer zufälligen reproduzierbaren sortierung

# TODO: Flat download implementieren
# TODO: Add user specified favourite searches (app_views/__init__.py/menu_bar)

# TODO: Implementierung einer Thumbnail-View (template) und Nutzung bei overview und items (next, prev)

# TODO: Fehler beim Setzen eines Favouriten (aus Suche heraus? Letztes Element einer Suche entfernen?)
# TODO: Autoplay for Audio/ Video in User Prefs

# TODO: No E-Mails from audio.mount-mockery.de (possibly after intial setup - no admin); Try to add a new user and find the error.
# TODO: Add clean cache to command line options (gallery-cache, item-cache, whoosh-index)
# TODO: Add and check ogg files and wav files (should be okay...) and also avprobe on such a system
# TODO: ??? Add Flat-Download ??? (all files in the root folder of the zip file)
# TODO: Improve view of checkbox and text (highlighting - red if checked. blue if not) for inverse right management! 
# TODO: Favoritenentfernung aus der Favouritenansicht vervollständigen
# TODO: X beim flash hinzu. Click setzt hide.
# TODO: Useranlegen ohne E-Mailbestätigung ermöglichen
# TODO: Intiale Inbetriebnahme erleichtern

# TODO: - Permission check of all pathes in pygal_config at startup to avoid runtime errors and data losses
#       - Folgeseiten von Staging überarbeiten:
#           - Nach Staging-Commit den Staging-Container beibehalten, wenn er noch existiert, sonst den ersten
#           - Nach Container delete in stagin bleiben und delete ausgewählt halten
#       - Bildgröße der Thumbs im Staging conainer ebenfalls mit der url übermitteln (s. thumb beim item - index=X)
#       - Aufklappen der Bäume im Admin-Dialog prüfen und neu festlegen + Bilderliste wie overview erzeugen (ggf. durch import von 'overview.html' im template.
#          - Admin - Folders: Tree eingeklappt darstellen
#       - Markierung des Ordner beibehalten, wenn in folder structure gewechselt wird zwischen delete und create
#       - Nutze AJAX in flask für das Suchelement, Aufbau der Seite ohne neu zu laden
#       - DEBUG output bei cache generierung immer aktivieren (unabhängig vom Parameter in der config)
#       - restlichen str_args -> helpers (login, logout, register, lostpass, userprefs, ...?)
#       - Löschdialog für Ordner (Anzeige aller Elemente)
#       - Staging Area und Delete-Page: Für delete und commit eine Auswahl ermöglichen (commit und delete aus Ordner)
#       - logging ergänzen mit erben der classe report.logit (itemlist, picture, ...)
#       - required attribut für js-tree in admin.staging
#       - Zusätzlich Infos auf Info-Seite für itemlist (Datum, uid, ) siehe Bilder
#       - Select all Button bei der Administration der Rechte hinzufügen
#       - Nach texten auf der Oberfläche suchen, die in das Modul lang gehören (z.B.: Button- und Labeltexte)
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
from pygal_config import theme_path
from auth import user_data_handler
from items.database import indexed_search
import sys

static_folder = os.path.join(theme_path, 'static')
template_folder = os.path.join(theme_path, 'templates')

if __name__ == "__main__":
    from pygal_config import url_prefix
else:
    url_prefix = ''


if len(url_prefix) > 1:
    app = flask.Flask('pygal', static_folder=static_folder, template_folder=template_folder, static_url_path=url_prefix + '/static')
else:
    app = flask.Flask('pygal', static_folder=static_folder, template_folder=template_folder)


# creating logger for usage in other modules
app.debug = DEBUG
log_level = logging.DEBUG
#
logger = logging.getLogger('app logger')
app.logger.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
handlers = []

if DEBUG:
    lh = logging.StreamHandler(sys.stdout)
    lh.setLevel(logging.DEBUG)
    lh.setFormatter(logging.Formatter("""[%(asctime)s] %(levelname)-7s: %(message)s - File "%(pathname)s", line %(lineno)d, in %(funcName)s"""))
    handlers.append(lh)
from logging.handlers import RotatingFileHandler
lh = RotatingFileHandler(os.path.join(os.path.dirname(__file__), 'error.log'), 'a', 50 * 1024 * 1024, 2)
lh.setLevel(logging.WARNING)
lh.setFormatter(logging.Formatter("""[%(asctime)s] %(levelname)-7s: %(message)s - File "%(pathname)s", line %(lineno)d, in %(funcName)s"""))
handlers.append(lh)
for lh in handlers:
    logger.addHandler(lh)

# set session lifetime, name, url_prefix
app.permanent_session_lifetime = timedelta(days=90)
app.config['SESSION_COOKIE_NAME'] = 'pygal_session'
app.config['SESSION_COOKIE_PATH'] = url_prefix or '/'

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
    parser.add_option("-i", "--whoosh-index", action="store_true", dest="index", default=False, help="creates the search index from scratch")
    (options, args) = parser.parse_args()
    if options.cache:
        for user in [''] + user_data_handler().users():
            il = itemlist("", config.item_path, False, config.database_path, config.cache_path, user, True)
            for i in range(0, len(config.thumbnail_size_list)):
                il.create_thumbnail(i)
            for i in range(0, len(config.webnail_size_list)):
                il.create_webnail(i)
    if options.index or options.cache:
        isearch = indexed_search(force_creation_from_scratch=True)
    if options.database:
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
            db_update_cleanup(itemlist("", config.item_path, False, config.database_path, config.cache_path, user, True))

    if not options.cache and not options.index and not options.database:
        app.run(config.ip_to_serve_from, 5000)
