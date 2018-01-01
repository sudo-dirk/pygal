import auth
import flask
from helpers import decode
from helpers import link
from helpers import strargs
from helpers import url_extention
import json
import lang
import os
import pygal_config as config


RESP_TYPE_ADD_TAG = 0
RESP_TYPE_ADMIN_RIGHTS = 1
RESP_TYPE_ADMIN_USER_CHOOSE = 2
RESP_TYPE_DELETE = 3
RESP_TYPE_EMPTY = 4
RESP_TYPE_FORM_DATA = 5
RESP_TYPE_ITEM = 6
RESP_TYPE_LOGIN = 7
RESP_TYPE_LOSTPASS = 8
RESP_TYPE_REGISTER = 9
RESP_TYPE_USERPROFILE = 10

show_action_bar = {RESP_TYPE_ADD_TAG: True,
                   RESP_TYPE_ADMIN_RIGHTS: False,
                   RESP_TYPE_ADMIN_USER_CHOOSE: False,
                   RESP_TYPE_DELETE: True,
                   RESP_TYPE_EMPTY: False,
                   RESP_TYPE_FORM_DATA: False,
                   RESP_TYPE_ITEM: True,
                   RESP_TYPE_LOGIN: False,
                   RESP_TYPE_LOSTPASS: False,
                   RESP_TYPE_REGISTER: False,
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
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_extention=url_extention(item_name), navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], error=error, info=info, hint=hint)
    elif this is None:
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_extention=url_extention(item_name), navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], tag_id=tag_id, error=error, info=info, hint=hint)
    elif tag_id is None:
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_extention=url_extention(item_name), navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], this=this, error=error, info=info, hint=hint)
    else:
        return collector(title=title, pygal_user=auth.pygal_user, lang=lang, url_extention=url_extention(item_name), navigation_list=navigation_list(item_name), action_bar=show_action_bar[resp_type], this=this, tag_id=tag_id, error=error, info=info, hint=hint)


def get_footer_input():
    return collector()


def make_response(resp_type, item_name, item=None, error=None, info=None, hint=None):
    if resp_type is RESP_TYPE_ADD_TAG and item is not None:
        tag_id = flask.request.args.get('tag_id')
        rv = flask.render_template('header.html', input=get_header_input(resp_type, 'Add Tag: %s' % (item.name()), item_name, error, info, hint, item, tag_id))
        content_input = collector(this=item, tag_id=tag_id)
        rv += flask.render_template('add_tag.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_ADMIN_RIGHTS and item is not None:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.admin, item_name, error, info, hint, item))
        content_input = collector(pygal_user=auth.pygal_user, this=item, user_to_admin=flask.request.args.get('user'))
        rv += flask.render_template('admin_right_dialog.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_ADMIN_USER_CHOOSE:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.admin, item_name, error, info, hint, item))
        # TODO: create a template for this content
        for user in auth.user_data_handler().users():
            rv += '<form method="get" action=""> <input type="submit" value="%s" class="button" name="user"/></form><br>' % user
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
    elif resp_type is RESP_TYPE_ITEM and item is not None:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, item.name(), item_name, error, info, hint, item))
        content_input = collector(this=item)
        rv += flask.render_template(item.template(), input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_LOGIN:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.login, item_name, error, info, hint))
        content_input = collector(lang=lang, url_extention=url_extention(item_name))
        rv += flask.render_template('login.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_LOSTPASS:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.lostpass, item_name, error, info, hint))
        content_input = collector(lang=lang)
        rv += flask.render_template('lostpass.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_REGISTER:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.register, item_name, error, info, hint))
        content_input = collector(lang=lang)
        rv += flask.render_template('register.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    elif resp_type is RESP_TYPE_USERPROFILE:
        rv = flask.render_template('header.html', input=get_header_input(resp_type, lang.userprofile, item_name, error, info, hint))
        content_input = collector(config=config, pygal_user=auth.pygal_user, lang=lang, url_extention=url_extention(item_name))
        rv += flask.render_template('userprofile.html', input=content_input)
        rv += flask.render_template('footer.html', input=get_footer_input())
        return rv
    else:
        return make_response(RESP_TYPE_EMPTY, item_name, error='Internal Error while generating response (unknown response type)!<br>resp_type: %d<br>type(item): %s' % (resp_type, str(type(item))))
