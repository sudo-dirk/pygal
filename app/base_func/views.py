from app import collector
from app import encode
from app import url_extention
from app.base_func import base_func
from auth import pygal_user
import flask
from items import itemlist
import lang
from pygal_config import url_prefix

from app import prefix_search
from app import prefix_login
from app import prefix_logout
from app import prefix_lostpass
from app import prefix_register
from app import prefix_userprofile


@base_func.route(prefix_search + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_search, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def search(item_name):
    item_name = encode(item_name)
    if not item_name:
        il = itemlist('', request_args=flask.request.args, prefix=prefix_search)
    else:
        il_root = itemlist('', request_args=flask.request.args, prefix=prefix_search)
        index = il_root.index_by_rel_path(item_name)
        if index >= 0:
            il = il_root[index]
        else:
            return item_name
    inp = collector(title=il.name(), url_prefix=url_prefix, url_extention=url_extention(item_name), this=il, pygal_user=pygal_user, lang=lang)
    rv = flask.render_template('header.html', input=inp)
    rv += flask.render_template(il.template(), input=inp)
    rv += flask.render_template('footer.html', input=inp)
    return rv


@base_func.route(prefix_login + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_login, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def login(item_name):
    if flask.request.method == 'GET':
        inp = collector(title=lang.login, url_prefix=url_prefix, url_extention=url_extention(item_name), pygal_user=pygal_user, lang=lang)
        rv = flask.render_template('header.html', input=inp)
        rv += flask.render_template('login.html', input=inp)
        rv += flask.render_template('footer.html', input=inp)
        return rv
    else:
        return pygal_user.login_by_form(flask.request.form, url_extention(item_name))


@base_func.route(prefix_logout + '/<itemname:item_name>')
@base_func.route(prefix_logout, defaults=dict(item_name=u''))
def logout(item_name):
    return pygal_user.logout(url_extention(item_name))


@base_func.route(prefix_register + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_register, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def register(item_name):
    if flask.request.method == 'GET':
        inp = collector(title=lang.register, url_prefix=url_prefix, url_extention=url_extention(item_name), pygal_user=pygal_user, lang=lang)
        rv = flask.render_template('header.html', input=inp)
        rv += flask.render_template('register.html', input=inp)
        rv += flask.render_template('footer.html', input=inp)
        return rv
    else:
        return pygal_user.create_user_by_form(flask.request.form, url_extention(item_name))


@base_func.route(prefix_userprofile + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_userprofile, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def userprofile(item_name):
    # if flask.request.method == 'GET':
        inp = collector(title=lang.userprofile, url_prefix=url_prefix, url_extention=url_extention(item_name), pygal_user=pygal_user, lang=lang)
        rv = flask.render_template('header.html', input=inp)
        rv += flask.render_template('userprofile.html', input=inp)
        rv += flask.render_template('footer.html', input=inp)
        return rv


@base_func.route(prefix_lostpass + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_lostpass, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def lostpass(item_name):
    if flask.request.method == 'GET':
        inp = collector(title='Lostpass', url_prefix=url_prefix, url_extention=url_extention(item_name), pygal_user=pygal_user, lang=lang)
        rv = flask.render_template('header.html', input=inp)
        rv += flask.render_template('lostpass.html', input=inp)
        rv += flask.render_template('footer.html', input=inp)
        return rv
    else:
        return 'not yet implemented'