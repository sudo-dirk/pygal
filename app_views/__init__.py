import app
import auth
import binascii
import flask
import helpers
from helpers import encode
from helpers import decode
from helpers import link
from helpers import piclink
from helpers import strargs
import items
from items import staging_container
import json
import lang
import os
import prefixes
import pygal_config as config
from pylibs import fstools
from pylibs import osm
import urllib
from auth import pygal_user

RESP_TYPE_ADD_TAG = 0
RESP_TYPE_ADMIN = 1
RESP_TYPE_DELETE = 2
RESP_TYPE_EMPTY = 3
RESP_TYPE_FORM_DATA = 4
RESP_TYPE_HELP = 5
RESP_TYPE_INFO = 6
RESP_TYPE_ITEM = 7
RESP_TYPE_LOGIN = 8
RESP_TYPE_LOSTPASS = 9
RESP_TYPE_PASSWORD_RECOVERY = 10
RESP_TYPE_REGISTER = 11
RESP_TYPE_UPLOAD = 12
RESP_TYPE_USERPROFILE = 13

ACTION_INFO = 'info'
ACTION_DOWNLOAD = 'download'
ACTION_IS_FAVOURITE = 'is_favourite'
ACTION_FAVOURITE = 'favourite'
ACTION_EDIT = 'edit'
ACTION_PLAY = 'play'
ACTION_SHUFFLE = 'shuffle'
ACTION_STOP = 'stop'
ACTION_DELETE = 'delete'
ACTION_GPS = 'gps'

def menu_bar(item, resp_type):
    mbar = helpers.menu.menubar()
    if item.user_may_admin():
        entry = helpers.menu.menuentry('admin', False, lang.admin, resp_type == RESP_TYPE_ADMIN, item.admin_url(), 'admin')
        mbar.append(entry)
        for dropdown in admin_actions(item, None):
            entry.append_dropdown_element(dropdown)
    if item.user_may_upload():
        mbar.append(helpers.menu.menuentry('upload', False, lang.upload, resp_type == RESP_TYPE_UPLOAD, item.upload_url(), 'upload'))
    if pygal_user.get_approved_session_user(item) in pygal_user.users():
        mbar.append(helpers.menu.menuentry('user', False, lang.user, resp_type == RESP_TYPE_USERPROFILE, item.userprofile_url(), 'user'))
        mbar.append(helpers.menu.menuentry('logout', False, lang.logout, False, item.logout_url(), 'logout'))
        entry = helpers.menu.menuentry('favourite', True, lang.view_fav, False, item.favourite_url(), 'favourite')
        mbar.append(entry)
    else:
        mbar.append(helpers.menu.menuentry('login', False, lang.login, resp_type == RESP_TYPE_LOGIN, item.login_url(), 'login'))
    return mbar

def action_bar(item, resp_type=None, itemlist=False):
    try:
        gps_link = osm.landmark_link(item.gps())
    except AttributeError:
        gps_link = None
    actions = {
        ACTION_DELETE: {'name': 'Delete',
                        'active': resp_type == RESP_TYPE_DELETE,
                        'url': item.delete_url(),
                        'icon': 'delete'},
        ACTION_DOWNLOAD: {'name': 'Download',
                          'active': False,
                          'url': item.download_url(),
                          'icon': 'download'},
        ACTION_EDIT:{'name': 'Add Tag',
                     'active': resp_type == RESP_TYPE_ADD_TAG,
                     'url': item.add_tag_url(),
                     'icon': 'edit'},
        ACTION_FAVOURITE:{'name': 'Add Favourite',
                          'active': False,
                          'url': item.favourite_url(helpers.STR_ARG_FAVOURITE_ADD, itemlist),
                          'icon': 'favourite'},
        ACTION_GPS:{'name': 'GPS',
                    'active': False,
                    'url': gps_link,
                    'icon': 'gps'},
        ACTION_INFO: {'name': 'Info',
                      'active': resp_type == RESP_TYPE_INFO,
                      'url': item.info_url(),
                      'icon': 'info'},
        ACTION_IS_FAVOURITE:{'name': 'Remove Favourite',
                             'active': False,
                             'url': item.favourite_url(helpers.STR_ARG_FAVOURITE_REMOVE, itemlist),
                             'icon': 'is_favourite'},
        ACTION_PLAY:{'name': 'Start Slideshow',
                     'active': False,
                     'url': item.slideshow_url(),
                     'icon': 'play'},
        ACTION_SHUFFLE:{'name': 'Shuffle',
                        'active': helpers.STR_ARG_SHUFFLE in flask.request.args,
                        'url': item.item_url(mask_request_shuffle=True) if helpers.STR_ARG_SHUFFLE in flask.request.args else item.item_url(shuffle=binascii.hexlify(os.urandom(24))),
                        'icon': 'shuffle'},
        ACTION_STOP:{'name': 'Stop Slideshow',
                     'active': False,
                     'url': item.item_url(),
                     'icon': 'stop'},
        }
    abar = helpers.menu.menubar()
    for key in item.actions():
        if key in actions and (key != ACTION_SHUFFLE or not itemlist):
            entry = helpers.menu.menuentry(key, True, **actions[key])
            abar.append(entry)
            if key == ACTION_DOWNLOAD:
                entry.append_dropdown_element(helpers.menu.menuentry(ACTION_DOWNLOAD, True, 'Download (Folder)', False, item.download_url(), 'download'))
                entry.append_dropdown_element(helpers.menu.menuentry(ACTION_DOWNLOAD+'_flat', True, 'Download (Flat)', False, item.download_url(True), 'download_flat'))
    return abar


def navigation_list(item_name):
    rv = list()
    rel_url = decode(item_name)
    args = {}
    if helpers.STR_ARG_SHUFFLE in flask.request.args:
        args[helpers.STR_ARG_SHUFFLE] = flask.request.args.get(helpers.STR_ARG_SHUFFLE)
    while os.path.basename(rel_url):
        rv.insert(0, link(os.path.join(config.url_prefix or '/', rel_url), os.path.basename(rel_url), args=args))
        rel_url = os.path.dirname(rel_url)
    if 'q' in flask.request.args:
        rv.insert(0, link(config.url_prefix + '/', lang.search_results % flask.request.args.get('q'), flask.request.args))
        rv.insert(1, link(None, ''))
    args = {}
    if helpers.STR_ARG_SHUFFLE in flask.request.args:
        args[helpers.STR_ARG_SHUFFLE] = flask.request.args.get(helpers.STR_ARG_SHUFFLE)
    rv.insert(0, link(config.url_prefix + '/', 'Home', args))
    return rv


def admin_actions(item, current_issue):
    abar = helpers.menu.menubar()
    abar.append(helpers.menu.menuentry('permission', True, 'Permissions', helpers.STR_ARG_ADMIN_ISSUE_PERMISSION == current_issue, item.admin_url({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_PERMISSION}), 'permission'))
    abar.append(helpers.menu.menuentry('staging', True, 'Staging', helpers.STR_ARG_ADMIN_ISSUE_STAGING == current_issue, item.admin_url({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_STAGING}), 'staging'))
    abar.append(helpers.menu.menuentry('folder', True, 'Folders', helpers.STR_ARG_ADMIN_ISSUE_FOLDERS == current_issue, item.admin_url({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_FOLDERS}), 'folder'))
    return abar

def get_form_user():
    user = flask.request.args.get(helpers.STR_ARG_ADMIN_USER, '')
    return flask.request.form.get(helpers.STR_ARG_ADMIN_USER, user)


def make_response(resp_type, item, tmc, error=None, info=None, hint=None):
    hint = hint or flask.request.args.get('hint')
    info = info or flask.request.args.get('info')
    error = error or flask.request.args.get('error')
    if resp_type is RESP_TYPE_ADD_TAG and item is not None:
        tag_id = flask.request.args.get(helpers.STR_ARG_TAG_INDEX)
        rv = flask.render_template(
            'header.html',
            title='Add Tag: %s' % item.name(),
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path), 
            action_bar=action_bar(item, resp_type),
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('add_tag.html', item=item, tag_id=tag_id)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_ADMIN and item is not None:
        # read staging data
        staging_content = dict()
        admin_issue = flask.request.form.get(helpers.STR_ARG_ADMIN_ISSUE) or flask.request.args.get(helpers.STR_ARG_ADMIN_ISSUE, helpers.STR_ARG_ADMIN_ISSUE_PERMISSION)
        if admin_issue == helpers.STR_ARG_ADMIN_ISSUE_PERMISSION:
            content = flask.render_template('admin.html', arg_name=helpers, admin_issue=admin_issue, item=item, lang=lang, pygal_user=auth.pygal_user, user_to_admin=get_form_user())
        elif admin_issue == helpers.STR_ARG_ADMIN_ISSUE_STAGING:
            for scif in fstools.filelist(config.staging_path, '*' + staging_container.CONTAINER_INFO_FILE_EXTENTION):
                sc = items.staging_itemlist('', os.path.splitext(scif)[0], False, None)
                staging_content[sc.get(sc.KEY_UUID)] = sc
            # create response
            action = flask.request.form.get(helpers.STR_ARG_ACTION) or flask.request.args.get(helpers.STR_ARG_ACTION, helpers.STR_ARG_ADMIN_ACTION_COMMIT)
            if len(staging_content) > 0:
                container_uuid = flask.request.args.get(helpers.STR_ARG_ADMIN_CONTAINER) or flask.request.args.get(helpers.STR_ARG_ADMIN_CONTAINER, staging_content.keys()[0])
            else:
                container_uuid = None
            content = flask.render_template('admin.html', arg_name=helpers, action=action, admin_issue=admin_issue, container_uuid=container_uuid, containers=staging_content, item=item, pygal_user=auth.pygal_user, url_prefix=config.url_prefix)
            if len(staging_content) == 0:
                info = 'No data in Staging-Area'
        elif admin_issue == helpers.STR_ARG_ADMIN_ISSUE_FOLDERS:
            action = flask.request.args.get(helpers.STR_ARG_ACTION, helpers.STR_ARG_ADMIN_ACTION_CREATE)
            content = flask.render_template('admin.html', arg_name=helpers, action=action, admin_issue=admin_issue, item=item, pygal_user=auth.pygal_user)
        else:
            content = ''
            error = 'Unknown admin_issue="%s"' % admin_issue
        rv = flask.render_template(
            'header.html',
            title=lang.admin,
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=admin_actions(item, admin_issue),
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += content
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_DELETE and item is not None:
        rv = flask.render_template(
            'header.html',
            title=lang.delete % item.name(True),
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=action_bar(item, resp_type),
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('delete.html', item=item)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_EMPTY and item is not None:
        rv = flask.render_template(
            'header.html',
            title='',
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_FORM_DATA and item is not None:
        hint = 'Form args:\n' + json.dumps(flask.request.form, indent=4, sort_keys=True) + '\n\nArgs:\n' + json.dumps(flask.request.args, indent=4, sort_keys=True)
        hint = hint.replace('\n', '<br>').replace(' ', '&nbsp')
        rv = flask.render_template(
            'header.html',
            title='',
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_HELP and item is not None:
        rv = flask.render_template(
            'header.html',
            title='Help on Search',
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += item.help_content()
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_INFO and item is not None:
        rv = flask.render_template(
            'header.html',
            title=item.name(),
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=action_bar(item, resp_type),
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        index = int(flask.request.args.get(helpers.STR_ARG_CACHEDATA_INDEX, -1))
        if index >= 0:
            data = item.cache_data()
            cache_filename = decode(os.path.basename(data[index][1]))
            if item.is_itemlist():
                try:
                    with open(encode(data[index][1]), 'r') as fh:
                        json_str = fh.read()
                except IOError:
                    json_str = ''
                rv += flask.render_template('modal_json.html', item=item, json_str=json_str, filename=cache_filename)
            else:
                # TODO: implement a safe way returning the cache data files!
                if index in range(1, 7) and not item.is_audio():
                    if index in range(1, 4):
                        url = item.thumbnail_url(index - 1)
                        xy_max = config.thumbnail_size_list[index - 1]
                    else:
                        url = item.webnail_url(index - 4)
                        xy_max = config.webnail_size_list[index - 4]
                    rv += flask.render_template('modal_picture.html', item=item, x=int(xy_max * item.ratio_x()), y=int(xy_max * item.ratio_y()), xy_max=xy_max, full_url=url, filename=cache_filename)
                if index is 1 and item.is_audio():
                    try:
                        with open(encode(data[index][1]), 'r') as fh:
                            json_str = fh.read()
                    except IOError:
                        json_str = ''
                    rv += flask.render_template('modal_json.html', item=item, json_str=json_str, filename=cache_filename)
                if index in [0, 7, 8]:
                    try:
                        with open(encode(data[index][1]), 'r') as fh:
                            json_str = fh.read()
                    except IOError:
                        json_str = ''
                    rv += flask.render_template('modal_json.html', item=item, json_str=json_str, filename=cache_filename)
        rv += flask.render_template('info.html', item=item, pygal_user=auth.pygal_user)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_ITEM and item is not None:
        if item.slideshow():
            if config.inverse_sorting:
                next_item_url = item.nxt().slideshow_url()
            else:
                next_item_url = item.prv().slideshow_url()
        rv = flask.render_template(
            'header.html',
            title=item.name(),
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=action_bar(item, resp_type),
            url_prefix=config.url_prefix, 
            error=error, hint=hint, info=info,
            slideshow={'stay_time': item.stay_time(), 'next_url': next_item_url} if item.slideshow() else None)
        rv += flask.render_template('item_view.html', item=item, action_bar_fkt=action_bar)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_LOGIN and item is not None:
        rv = flask.render_template(
            'header.html',
            title=lang.login,
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('login.html', item=item, lang=lang, url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_LOSTPASS and item is not None:
        rv = flask.render_template(
            'header.html',
            title=lang.lostpass,
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('lostpass.html', item=item, lang=lang, url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_PASSWORD_RECOVERY and item is not None:
        rv = flask.render_template(
            'header.html',
            title=lang.password_recovery,
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('password_recovery.html', lang=lang, target_url=config.url_prefix or '/')
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_REGISTER and item is not None:
        rv = flask.render_template(
            'header.html',
            title=lang.register,
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('register.html', item=item, lang=lang, url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_UPLOAD and item is not None:
        rv = flask.render_template(
            'header.html',
            title=lang.upload,
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('upload.html', config=config, item=item)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    elif resp_type is RESP_TYPE_USERPROFILE and item is not None:
        rv = flask.render_template(
            'header.html',
            title=lang.userprofile,
            search=lang.search,
            menu_bar=menu_bar(item, resp_type),
            navigation_list=navigation_list(item._rel_path),
            action_bar=[],
            url_prefix=config.url_prefix,
            error=error, hint=hint, info=info)
        rv += flask.render_template('userprofile.html', config=config, item=item, lang=lang, pygal_user=auth.pygal_user)
        rv += flask.render_template('footer.html', user_links=config.user_links, tmc=tmc, url_prefix=config.url_prefix, error=error, hint=hint, info=info, debug=config.DEBUG, full_url=helpers.full_url())
        return rv
    else:
        return make_response(RESP_TYPE_EMPTY, item, error='Internal Error while generating response (unknown response type)!<br>resp_type: %d<br>type(item): %s' % (resp_type, str(type(item))))
