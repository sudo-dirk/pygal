import app
import auth
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
import pygal_config as config
from pylibs import fstools
import urllib

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
RESP_TYPE_REGISTER = 10
RESP_TYPE_UPLOAD = 11
RESP_TYPE_USERPROFILE = 12


def navigation_list(item_name):
    rv = list()
    rel_url = decode(os.path.join(item_name))
    while os.path.basename(rel_url):
        rv.insert(0, link(os.path.join(config.url_prefix or '/', rel_url), os.path.basename(rel_url)))
        rel_url = os.path.dirname(rel_url)
    if 'q' in flask.request.args:
        rv.insert(0, link(config.url_prefix + '/' + strargs(flask.request.args), lang.search_results % flask.request.args.get('q')))
        rv.insert(1, link(None, ''))
    return rv

def admin_actions(item):
    rv = list()
    rv.append(piclink(item.admin_url({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_PERMISSION}), 'Permissions', config.url_prefix + '/static/common/img/permission.png'))
    rv.append(piclink(item.admin_url({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_STAGING}), 'Staging', config.url_prefix + '/static/common/img/staging.png'))
    rv.append(piclink(item.admin_url({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_FOLDERS}), 'Folders', config.url_prefix + '/static/common/img/folders.png'))
    return rv


def get_form_user():
    user = flask.request.args.get(helpers.STR_ARG_ADMIN_USER, '')
    return flask.request.form.get(helpers.STR_ARG_ADMIN_USER, user)


def make_response(resp_type, item, tmc, error=None, info=None, hint=None):
    if resp_type is RESP_TYPE_ADD_TAG and item is not None:
        tag_id = flask.request.args.get(helpers.STR_ARG_TAG_INDEX)
        rv = flask.render_template('header.html', action_bar=item.actions(), error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title='Add Tag: %s' % item.name(), url_prefix=config.url_prefix)
        rv += flask.render_template('add_tag.html', item=item, tag_id=tag_id)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
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
            action = flask.request.form.get(helpers.STR_ARG_ADMIN_ACTION) or flask.request.args.get(helpers.STR_ARG_ADMIN_ACTION, helpers.STR_ARG_ADMIN_ACTION_COMMIT)
            if len(staging_content) > 0:
                container_uuid = flask.request.args.get(helpers.STR_ARG_ADMIN_CONTAINER) or flask.request.args.get(helpers.STR_ARG_ADMIN_CONTAINER, staging_content.keys()[0])
            else:
                container_uuid = None
            content = flask.render_template('admin.html', arg_name=helpers, action=action, admin_issue=admin_issue, container_uuid=container_uuid, containers=staging_content, item=item, pygal_user=auth.pygal_user, url_prefix=config.url_prefix)
            if len(staging_content) == 0:
                info = 'No data in Staging-Area'
        elif admin_issue == helpers.STR_ARG_ADMIN_ISSUE_FOLDERS:
            action = flask.request.args.get(helpers.STR_ARG_ADMIN_ACTION, helpers.STR_ARG_ADMIN_ACTION_CREATE)
            content = flask.render_template('admin.html', arg_name=helpers, action=action, admin_issue=admin_issue, item=item, pygal_user=auth.pygal_user)
        else:
            content = ''
            error = 'Unknown admin_issue="%s"' % admin_issue
        rv = flask.render_template('header.html', action_bar=admin_actions(item), error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=lang.admin, url_prefix=config.url_prefix)
        rv += content
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_DELETE and item is not None:
        rv = flask.render_template('header.html', action_bar=item.actions(), error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=lang.delete % item.name(True), url_prefix=config.url_prefix)
        rv += flask.render_template('delete.html', item=item)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_EMPTY and item is not None:
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title='', url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_FORM_DATA and item is not None:
        hint = 'Form args:\n' + json.dumps(flask.request.form, indent=4, sort_keys=True) + '\n\nArgs:\n' + json.dumps(flask.request.args, indent=4, sort_keys=True)
        hint = hint.replace('\n', '<br>').replace(' ', '&nbsp')
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title='', url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_HELP and item is not None:
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title='', url_prefix=config.url_prefix)
        rv += item.help_content()
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_INFO and item is not None:
        rv = flask.render_template('header.html', action_bar=item.actions(), error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=item.name(), url_prefix=config.url_prefix)
        index = int(flask.request.args.get(helpers.STR_ARG_CACHEDATA_INDEX, -1))
        modal_html = ''
        if index >= 0:
            data = item.cache_data()
            cache_filename = decode(os.path.basename(data[index][1]))
            if item.is_itemlist():
                try:
                    with open(encode(data[index][1]), 'r') as fh:
                        json_str = fh.read()
                except IOError:
                    json_str = ''
                modal_html = flask.render_template('single_json.html', item=item, json_str=json_str, filename=cache_filename)
            else:
                # TODO: implement a safe way returning the cache data files!
                if index in range(1, 7):
                    if index in range(1, 4):
                        url = item.thumbnail_url(index - 1)
                        xy_max = config.thumbnail_size_list[index - 1]
                    else:
                        url = item.webnail_url(index - 4)
                        xy_max = config.webnail_size_list[index - 4]
                    modal_html = flask.render_template('single_picture.html', item=item, x=int(xy_max * item.ratio_x()), y=int(xy_max * item.ratio_y()), xy_max=xy_max, url=url, filename=cache_filename)
                if index in [0, 7, 8]:
                    try:
                        with open(encode(data[index][1]), 'r') as fh:
                            json_str = fh.read()
                    except IOError:
                        json_str = ''
                    modal_html = flask.render_template('single_json.html', item=item, json_str=json_str, filename=cache_filename)
        rv += flask.render_template('info.html', modal_html=modal_html, item=item, pygal_user=auth.pygal_user)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_ITEM and item is not None:
        rv = flask.render_template('header.html', action_bar=item.actions(), error=error, hint=hint, info=info, is_slideshow=item.slideshow(), item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=item.name(), url_prefix=config.url_prefix)
        rv += flask.render_template('item_view.html', item=item)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_LOGIN and item is not None:
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=lang.login, url_prefix=config.url_prefix)
        rv += flask.render_template('login.html', item=item, lang=lang, url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_LOSTPASS and item is not None:
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=lang.lostpass, url_prefix=config.url_prefix)
        rv += flask.render_template('lostpass.html', item=item, lang=lang, url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_REGISTER and item is not None:
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=lang.register, url_prefix=config.url_prefix)
        rv += flask.render_template('register.html', item=item, lang=lang, url_prefix=config.url_prefix)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_UPLOAD and item is not None:
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=lang.upload, url_prefix=config.url_prefix)
        rv += flask.render_template('upload.html', config=config, item=item)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    elif resp_type is RESP_TYPE_USERPROFILE and item is not None:
        rv = flask.render_template('header.html', action_bar=[], error=error, hint=hint, info=info, item=item, lang=lang, navigation_list=navigation_list(item._rel_path), pygal_user=auth.pygal_user, title=lang.userprofile, url_prefix=config.url_prefix)
        rv += flask.render_template('userprofile.html', config=config, item=item, lang=lang, pygal_user=auth.pygal_user)
        rv += flask.render_template('footer.html', tmc=tmc, url_prefix=config.url_prefix)
        return rv
    else:
        return make_response(RESP_TYPE_EMPTY, item, error='Internal Error while generating response (unknown response type)!<br>resp_type: %d<br>type(item): %s' % (resp_type, str(type(item))))
