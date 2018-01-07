import app
import auth
import flask
from helpers import decode
from helpers import link
from helpers import staging_container
from helpers import strargs
from helpers import url_extention
import json
import lang
import os
import pygal_config as config
from pylibs import fstools

RESP_TYPE_ADD_TAG = 0
RESP_TYPE_ADMIN = 1
RESP_TYPE_CACHEDATAVIEW = 2
RESP_TYPE_DELETE = 3
RESP_TYPE_EMPTY = 4
RESP_TYPE_FORM_DATA = 5
RESP_TYPE_INFO = 6
RESP_TYPE_ITEM = 7
RESP_TYPE_LOGIN = 8
RESP_TYPE_LOSTPASS = 9
RESP_TYPE_REGISTER = 10
RESP_TYPE_UPLOAD = 11
RESP_TYPE_USERPROFILE = 12

show_action_bar = {RESP_TYPE_ADD_TAG: True,
                   RESP_TYPE_ADMIN: False,
                   RESP_TYPE_CACHEDATAVIEW: True,
                   RESP_TYPE_DELETE: True,
                   RESP_TYPE_EMPTY: False,
                   RESP_TYPE_FORM_DATA: False,
                   RESP_TYPE_INFO: True,
                   RESP_TYPE_ITEM: True,
                   RESP_TYPE_LOGIN: False,
                   RESP_TYPE_LOSTPASS: False,
                   RESP_TYPE_REGISTER: False,
                   RESP_TYPE_UPLOAD: False,
                   RESP_TYPE_USERPROFILE: False}


class collector(object):
    def __init__(self, **kwds):
        for key in kwds:
            setattr(self, key, kwds[key])

    def has_attr(self, name):
        return hasattr(self, name)


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


def get_header_input(resp_type, title, item_name, error, info, hint, this=None, tag_id=None):
    if this is None and tag_id is None:
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_prefix=config.url_prefix, url_extention=url_extention(item_name), app=app, navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], error=error, info=info, hint=hint)
    elif this is None:
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_prefix=config.url_prefix, url_extention=url_extention(item_name), app=app, navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], tag_id=tag_id, error=error, info=info, hint=hint)
    elif tag_id is None:
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_prefix=config.url_prefix, url_extention=url_extention(item_name), app=app, navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], this=this, error=error, info=info, hint=hint)
    else:
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_prefix=config.url_prefix, url_extention=url_extention(item_name), app=app, navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], this=this, tag_id=tag_id, error=error, info=info, hint=hint)


def get_footer_input():
    return collector()


def get_form_user():
    user = flask.request.args.get('user')
    if user == '':
        return None
    return user


def make_response(resp_type, item_name, item=None, error=None, info=None, hint=None):
    if resp_type is RESP_TYPE_ADD_TAG and item is not None:
        tag_id = flask.request.args.get('tag_id')
        rv = flask.render_template('header.html', input=get_header_input(resp_type, 'Add Tag: %s' % (item.name()), item_name, error, info, hint, item, tag_id))
        content_input = collector(this=item, tag_id=tag_id)
        rv += flask.render_template('add_tag.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_ADMIN:
        admin_issue = flask.request.args.get('admin_issue', 'permission')
        if admin_issue == 'permission':
            rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.admin, item_name, error, info, hint, item))
            content_input = collector(pygal_user=auth.pygal_user, this=item, user_to_admin=get_form_user(), lang=lang, url_prefix=config.url_prefix, app=app, url_extention=url_extention(item_name), admin_issue=admin_issue)
            rv += flask.render_template('admin.html', input=content_input)
            rv += flask.render_template('footer.html', input=get_footer_input())
            return rv
        elif admin_issue == 'staging':
            action = flask.request.args.get('action', 'commit')
            # read staging data
            staging_content = dict()
            for scif in fstools.filelist(config.staging_path, '*' + staging_container.CONTAINER_INFO_FILE_EXTENTION):
                sc = staging_container(None, None, None, None, None, None)
                sc.load(scif)
                staging_content[sc.get(sc.KEY_UUID)] = sc
            # create response
            if len(staging_content) > 0:
                container_uuid = flask.request.args.get('container_uuid', staging_content.values()[0].get(staging_container.KEY_UUID))
                content_input = collector(pygal_user=auth.pygal_user, this=item, url_prefix=config.url_prefix, app=app, containers=staging_content, container_uuid=container_uuid, admin_issue=admin_issue, action=action)
                content = flask.render_template('admin.html', input=content_input)
                info = None
            else:
                content = ''
                info = 'No data in Staging-Area'
            rv = flask.render_template('header.html', input=get_header_input(resp_type, 'Staging', item_name, error, info, hint))
            rv += content
            rv += flask.render_template('footer.html', input=get_footer_input(), info=info)
            return rv
        elif admin_issue == 'folder structure':
            action = flask.request.args.get('action', 'create')
            rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.admin, item_name, error, info, hint, item))
            content_input = collector(pygal_user=auth.pygal_user, this=item, admin_issue=admin_issue, action=action)
            rv += flask.render_template('admin.html', input=content_input)
            rv += flask.render_template('footer.html', input=get_footer_input())
            return rv
        else:
            return make_response(RESP_TYPE_EMPTY, item_name, error='Unknown admin_issue="%s"' % admin_issue)
    elif resp_type is RESP_TYPE_CACHEDATAVIEW and item is not None:
        index = int(flask.request.args.get('index', '0'))
        data = item.cache_data()
        cache_filename = decode(os.path.basename(data[index][1]))
        rv = flask.render_template('header.html', input=get_header_input(resp_type, cache_filename, item_name, error, info, hint, item))
        if item.is_itemlist():
            try:
                with open(data[index][1], 'r') as fh:
                    json_str = fh.read()
            except IOError:
                json_str = ''
            content_input = collector(datatemplate='single_json.html', this=item, json_str=json_str, filename=cache_filename)
            rv += flask.render_template('cachedataview.html', input=content_input)
        else:
            if index in [0, 1, 2, 3, 4, 5]:
                if index in [0, 1, 2]:
                    url = item.thumbnail_url(index)
                    xy_max = config.thumbnail_size_list[index]
                else:
                    url = item.webnail_url(index - 3)
                    xy_max = config.webnail_size_list[index - 3]
                content_input = collector(datatemplate='single_picture.html', this=item, x=int(xy_max * item.ratio_x()), y=int(xy_max * item.ratio_y()), xy_max=xy_max, url=url, filename=cache_filename)
                rv += flask.render_template('cachedataview.html', input=content_input)
            if index in [6, 7, 8]:
                try:
                    with open(data[index][1], 'r') as fh:
                        json_str = fh.read()
                except IOError:
                    json_str = ''
                content_input = collector(datatemplate='single_json.html', this=item, json_str=json_str, filename=cache_filename)
                rv += flask.render_template('cachedataview.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_DELETE and item is not None:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, 'Delete: %s' % (item.name()), item_name, error, info, hint, item))
        content_input = collector(this=item)
        rv += flask.render_template('delete.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_EMPTY:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, '', item_name, error, info, hint))
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_FORM_DATA:
        hint = 'Form args:\n' + json.dumps(flask.request.form, indent=4, sort_keys=True) + '\n\nArgs:\n' + json.dumps(flask.request.args, indent=4, sort_keys=True)
        hint = hint.replace('\n', '<br>').replace(' ', '&nbsp')
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.title_info, item_name, error, info, hint))
        return rv
    elif resp_type is RESP_TYPE_INFO and item is not None:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, item.name(), item_name, error, info, hint, item))
        content_input = collector(pygal_user=auth.pygal_user, this=item)
        rv += flask.render_template('info.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_ITEM and item is not None:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, item.name(), item_name, error, info, hint, item))
        content_input = collector(this=item)
        rv += flask.render_template(item.template(), input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_LOGIN:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.login, item_name, error, info, hint))
        content_input = collector(lang=lang, url_prefix=config.url_prefix, url_extention=url_extention(item_name), app=app)
        rv += flask.render_template('login.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_LOSTPASS:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.lostpass, item_name, error, info, hint))
        content_input = collector(lang=lang, url_prefix=config.url_prefix, url_extention=url_extention(item_name), app=app)
        rv += flask.render_template('lostpass.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_REGISTER:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.register, item_name, error, info, hint))
        content_input = collector(lang=lang, url_prefix=config.url_prefix, url_extention=url_extention(item_name), app=app)
        rv += flask.render_template('register.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_UPLOAD:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.upload, item_name, error, info, hint))
        content_input = collector(config=config, url_extention=url_extention(item_name), app=app)
        rv += flask.render_template('upload.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_USERPROFILE:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.userprofile, item_name, error, info, hint))
        content_input = collector(config=config, pygal_user=auth.pygal_user, lang=lang, url_extention=url_extention(item_name), app=app)
        rv += flask.render_template('userprofile.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    else:
        return make_response(RESP_TYPE_EMPTY, item_name, error='Internal Error while generating response (unknown response type)!<br>resp_type: %d<br>type(item): %s' % (resp_type, str(type(item))))
