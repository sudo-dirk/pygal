from app.base_func import base_func
import app_views
import auth
import flask
import helpers
import items
import lang
from prefixes import prefix_login
from prefixes import prefix_logout
from prefixes import prefix_lostpass
from prefixes import prefix_register
import pygal_config as config
from pygal_config import url_prefix
from pygal_config import admin_group


@base_func.route(prefix_logout + '/<itemname:item_name>')
@base_func.route(prefix_logout, defaults=dict(item_name=u''))
def logout(item_name):
    sdh = auth.session_data_handler()
    sdh.set_user(None)
    sdh.set_password(None)
    return flask.make_response(flask.redirect(url_prefix + helpers.url_extention(item_name)))


@base_func.route(prefix_login + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_login, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def login(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None, False)
    if i is not None:
        if flask.request.method == 'GET':
            return app_views.make_response(app_views.RESP_TYPE_LOGIN, i, tmc, info=lang.info_login % (url_prefix + prefix_register + helpers.url_extention(item_name), url_prefix + prefix_lostpass + helpers.url_extention(item_name)))
        else:
            fusername = flask.request.form.get('login_username')
            fpassword = auth.password_salt_and_hash(flask.request.form.get('login_password'))
            udh = auth.user_data_handler(fusername)
            sdh = auth.session_data_handler()
            if udh.chk_password(fpassword, fusername):
                sdh.set_user(fusername)
                sdh.set_password(fpassword)
                return flask.make_response(flask.redirect(url_prefix + helpers.url_extention(item_name)))
            else:
                sdh = auth.session_data_handler()
                sdh.set_user(None)
                sdh.set_password(None)
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error=lang.error_password_wrong_login)
    flask.abort(404)


@base_func.route(prefix_register + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_register, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def register(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None, False)
    if i is not None:
        if flask.request.method == 'GET':
            return app_views.make_response(app_views.RESP_TYPE_REGISTER, i, tmc)
        else:
            fusername = flask.request.form.get('register_username')
            udh = auth.user_data_handler(fusername)
            sdh = auth.session_data_handler()
            fpassword1 = auth.password_salt_and_hash(flask.request.form.get('register_password1'))
            fpassword2 = auth.password_salt_and_hash(flask.request.form.get('register_password2'))
            femail = flask.request.form.get('register_email')
            if fusername in admin_group:
                return app_views.make_response(app_views.RESP_TYPE_REGISTER, i, tmc, error=lang.error_user_already_in_admin_group)
            elif udh.user_exists(fusername):
                return app_views.make_response(app_views.RESP_TYPE_REGISTER, i, tmc, error=lang.error_user_already_exists % (url_prefix + prefix_lostpass + helpers.url_extention(item_name)))
            elif fpassword1 != fpassword2:
                return app_views.make_response(app_views.RESP_TYPE_REGISTER, i, tmc, error=lang.error_passwords_not_equal_register)
            else:
                udh = auth.user_data_handler(fusername)
                udh.set_email(femail)
                udh.set_password(fpassword1)
                udh.store_user()
                sdh.set_user(fusername)
                sdh.set_password(fpassword1)
                return flask.make_response(flask.redirect(url_prefix + helpers.url_extention(item_name)))
    flask.abort(404)


@base_func.route(prefix_lostpass + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_lostpass, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def lostpass(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None, False)
    if i is not None:
        if flask.request.method == 'GET':
            return app_views.make_response(app_views.RESP_TYPE_LOSTPASS, i, tmc, info=lang.info_lostpass)
        else:
            return app_views.make_response(app_views.RESP_TYPE_FORM_DATA, i, tmc, info='lostpass not yet implemented')
    flask.abort(404)
