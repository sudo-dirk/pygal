import app_views
from helpers import url_extention
from app.base_func import base_func
import auth
import flask
import lang
from pygal_config import url_prefix
from pygal_config import admin_group
from app import prefix_login
from app import prefix_logout
from app import prefix_lostpass
from app import prefix_register


@base_func.route(prefix_logout + '/<itemname:item_name>')
@base_func.route(prefix_logout, defaults=dict(item_name=u''))
def logout(item_name):
    sdh = auth.session_data_handler()
    sdh.set_user(None)
    sdh.set_password(None)
    return flask.make_response(flask.redirect(url_prefix + url_extention(item_name)))


@base_func.route(prefix_login + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_login, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def login(item_name):
    if flask.request.method == 'GET':
        return app_views.make_response(app_views.RESP_TYPE_LOGIN, item_name, info=lang.info_login % (url_prefix + prefix_register + url_extention(item_name), url_prefix + prefix_lostpass + url_extention(item_name)))
    else:
        fusername = flask.request.form.get('login_username')
        fpassword = auth.password_salt_and_hash(flask.request.form.get('login_password'))
        udh = auth.user_data_handler(fusername)
        sdh = auth.session_data_handler()
        if udh.chk_password(fpassword, fusername):
            sdh.set_user(fusername)
            sdh.set_password(fpassword)
            return flask.make_response(flask.redirect(url_prefix + url_extention(item_name)))
        else:
            sdh = auth.session_data_handler()
            sdh.set_user(None)
            sdh.set_password(None)
            return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=lang.error_password_wrong_login)


@base_func.route(prefix_register + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_register, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def register(item_name):
    if flask.request.method == 'GET':
        return app_views.make_response(app_views.RESP_TYPE_REGISTER, item_name)
    else:
        fusername = flask.request.form.get('register_username')
        udh = auth.user_data_handler(fusername)
        sdh = auth.session_data_handler()
        fpassword1 = auth.password_salt_and_hash(flask.request.form.get('register_password1'))
        fpassword2 = auth.password_salt_and_hash(flask.request.form.get('register_password2'))
        femail = flask.request.form.get('register_email')
        if fusername in admin_group:
            return app_views.make_response(app_views.RESP_TYPE_REGISTER, item_name, error=lang.error_user_already_in_admin_group)
        elif udh.user_exists(fusername):
            return app_views.make_response(app_views.RESP_TYPE_REGISTER, item_name, error=lang.error_user_already_exists % (url_prefix + prefix_lostpass + url_extention(item_name)))
        elif fpassword1 != fpassword2:
            return app_views.make_response(app_views.RESP_TYPE_REGISTER, item_name, error=lang.error_passwords_not_equal_register)
        else:
            udh = auth.user_data_handler(fusername)
            udh.set_email(femail)
            udh.set_password(fpassword1)
            udh.store_user()
            sdh.set_user(fusername)
            sdh.set_password(fpassword1)
            return flask.make_response(flask.redirect(url_prefix + url_extention(item_name)))


@base_func.route(prefix_lostpass + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_lostpass, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def lostpass(item_name):
    if flask.request.method == 'GET':
        return app_views.make_response(app_views.RESP_TYPE_LOSTPASS, item_name, info=lang.info_lostpass)
    else:
        return app_views.make_response(app_views.RESP_TYPE_FORM_DATA, item_name, info='lostpass not yet implemented')
