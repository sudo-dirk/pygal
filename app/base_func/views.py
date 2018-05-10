from app.base_func import base_func
import app_views
import auth
import flask
import helpers
import items
import lang
from prefixes import prefix_favourite
from prefixes import prefix_login
from prefixes import prefix_logout
from prefixes import prefix_lostpass
from prefixes import prefix_register
from prefixes import prefix_token
import pygal_config as config
from pygal_config import url_prefix
from pygal_config import admin_group


@base_func.route(prefix_favourite + '/<itemname:item_name>', methods=['GET', 'POST'])
@base_func.route(prefix_favourite, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def favourite(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None, False)
    info = None
    if i is not None:
        if auth.pygal_user.get_approved_session_user(i) in auth.pygal_user.users():
            if flask.request.method == 'GET':
                if flask.request.args.get(helpers.STR_ARG_FAVOURITE) == helpers.STR_ARG_FAVOURITE_ADD:
                    if i.add_favourite_of(auth.pygal_user.get_approved_session_user(i)):
                        info = 'Item %s added to favourites' % i.name()
                elif flask.request.args.get(helpers.STR_ARG_FAVOURITE) == helpers.STR_ARG_FAVOURITE_REMOVE:
                    if i.remove_favourite_of(auth.pygal_user.get_approved_session_user(i)):
                        info = 'Item %s removed from favourites' % i.name()
                else:
                    return flask.redirect(config.url_prefix + helpers.strargs({'q': 'favourite_of:%s' % auth.pygal_user.get_approved_session_user(i)}))
            if  flask.request.args.get(helpers.STR_ARG_REDIRECT_PARENT, None) is None:
                return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc, info=info)
            else:
                if i.is_a_searchresult():
                    raise "Vorheriges Element in der Suchuebersicht ist zu ermitteln, hier ist aber nur das Element selbst bekannt => Erzeugung der Suchliste und arbeiten in dieser Liste"
                    return flask.redirect(flask.request.url_root + helpers.strargs({'q': flask.request.args.get('q'), 'info': info}) + '#%s' % i.prv().id())
                else:
                    return flask.redirect(i.parent().item_url() + helpers.strargs({'info': info}) + '#%s' % i.id())
        else:
            return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error=lang.error_permission_denied)

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
            username = flask.request.form.get('register_username')
            password1 = auth.password_salt_and_hash(flask.request.form.get('register_password1'))
            password2 = auth.password_salt_and_hash(flask.request.form.get('register_password2'))
            email = flask.request.form.get('register_email')
            if username in admin_group:
                return app_views.make_response(app_views.RESP_TYPE_REGISTER, i, tmc, error=lang.error_user_already_in_admin_group)
            elif auth.user_data_handler().user_exists(username):
                return app_views.make_response(app_views.RESP_TYPE_REGISTER, i, tmc, error=lang.error_user_already_exists % (url_prefix + prefix_lostpass + helpers.url_extention(item_name)))
            elif password1 != password2:
                return app_views.make_response(app_views.RESP_TYPE_REGISTER, i, tmc, error=lang.error_passwords_not_equal_register)
            else:
                tl = auth.token_list()
                t = tl.create_new_token(config.token_valid_time, 
                                        type=tl.TYPE_ACCOUNT_CREATION,
                                        user=username,
                                        email=email,
                                        password=password1,
                                        ip=flask.request.remote_addr,
                                        url=flask.request.url_root[:-1] + config.url_prefix)
                helpers.mail.mail().send(email, helpers.mail.content_account_creation(t))
                return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc, info='Token for email confirmation send out')
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
            username = flask.request.form.get('lostpass_username')
            email = flask.request.form.get('lostpass_email')
            if auth.user_data_handler().user_exists(username):
                user = auth.user_data_handler(username)
            else:
                for username in auth.user_data_handler().users():
                    user = auth.user_data_handler(username)
                    if user.get_email() == email:
                        break
                    else:
                        user = None
            if user != None:
                tl = auth.token_list()
                t = tl.create_new_token(config.token_valid_time, 
                                        type=tl.TYPE_PW_RECOVERY,
                                        user=user._user,
                                        email=user.get_email(),
                                        ip=flask.request.remote_addr,
                                        url=flask.request.url_root[:-1] + config.url_prefix)
                helpers.mail.mail().send(user.get_email(), helpers.mail.content_pw_recovery(t))
            return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc, info='Recovery token send out, if user exists')
    flask.abort(404)


@base_func.route(prefix_token + '/<itemname:token_id>', methods=['GET', 'POST'])
@base_func.route(prefix_token, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def token(token_id):
    tmc = helpers.time_measurement()
    token_id = helpers.encode(token_id)
    i = items.get_item_by_path('', config.item_path, False, config.database_path, config.cache_path, None, False)
    if i is not None:
        tl = auth.token_list()
        if token_id in tl.keys():
            token = tl[token_id]
            if token.not_exceeded():
                if token['data'].get('type') == tl.TYPE_PW_RECOVERY:
                    if flask.request.method == 'GET':
                        return app_views.make_response(app_views.RESP_TYPE_PASSWORD_RECOVERY, i, tmc)
                    else:
                        password1 = flask.request.form.get('password1')
                        password2 = flask.request.form.get('password2')
                        if password1 != password2:
                            return app_views.make_response(app_views.RESP_TYPE_PASSWORD_RECOVERY, i, tmc, error=lang.error_passwords_not_equal_userprofile)
                        elif password1 == u'':
                            return app_views.make_response(app_views.RESP_TYPE_PASSWORD_RECOVERY, i, tmc, error=lang.error_password_empty_userprofile)
                        else:
                            udh = auth.user_data_handler(token['data'].get('user'))
                            udh.set_password(auth.password_salt_and_hash(password1))
                            udh.store_user()
                            tl.delete(token_id, True)
                            tl.clean()
                            tl.save()
                            return app_views.make_response(app_views.RESP_TYPE_LOGIN, i, tmc, info=lang.password_recovery_finished)
                elif token['data'].get('type') == tl.TYPE_ACCOUNT_CREATION:
                    username = token['data'].get('user')
                    password = token['data'].get('password')
                    email = token['data'].get('email')
                    # create useraccount
                    udh = auth.user_data_handler(username)
                    udh.set_email(email)
                    udh.set_password(password)
                    udh.store_user()
                    # send email to administrators
                    em = helpers.mail.mail()
                    em.send(helpers.mail.to_adr_admins(), helpers.mail.content_new_user(username))
                    # delete token and log action
                    tl.delete(token_id, True)
                    tl.clean()
                    tl.save()
                    return app_views.make_response(app_views.RESP_TYPE_LOGIN, i, tmc, info='User-Account had been created. Login and wait for Admin to grand access.')
                elif token['data'].get('type') == tl.TYPE_EMAIL_CONFIRMATION:
                    username = token['data'].get('user')
                    email = token['data'].get('email')
                    # change e-mail address
                    udh = auth.user_data_handler(username)
                    udh.set_email(email)
                    udh.store_user()
                    # delete token and log action
                    tl.delete(token_id, True)
                    tl.clean()
                    tl.save()
                    return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc, info='Your E-Mailaddress had been changed.')
                else:
                    return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, info='Recovery token handling not yet implemented')
            else:
                tl.clean()
                tl.save()
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error='Recovery token exceeded.')
        else:
            return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error='Recovery token does not exist.')
