from app.items import item
from app import prefix_add_tag
from app import prefix_admin
from app import prefix_delete
from app import prefix_download
from app import prefix_slideshow
from app import prefix_thumbnail
from app import prefix_userprofile
from app import prefix_webnail
from app import prefix_raw
import app_views
from helpers import encode, url_extention
import auth
import flask
from items import get_class_for_item
from items import itemlist
import lang
import os
import pygal_config as config
import StringIO
import zipfile


@item.route(prefix_admin + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_admin, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def admin(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        i = c(item_name, flask.request.args)
        if auth.pygal_user.may_admin():
            if 'user' in flask.request.args:
                user = flask.request.args.get('user')
                info = None
                if 'action' in flask.request.form:
                    delete_rights = flask.request.form.get('delete-rights').split(',')
                    download_right = flask.request.form.get('download-right') == 'true'
                    edit_rights = flask.request.form.get('edit-rights').split(',')
                    view_rights = flask.request.form.get('view-rights').split(',')
                    udh = auth.user_data_handler(user)
                    udh.set_rights_delete(delete_rights)
                    udh.set_rights_download(download_right)
                    udh.set_rights_edit(edit_rights)
                    udh.set_rights_view(view_rights)
                    udh.store_user()
                    info = "Rights for %s changed. Check rights for safety reasons." % user
                if user in auth.pygal_user.user_data.users():
                    return app_views.make_response(app_views.RESP_TYPE_ADMIN_RIGHTS, item_name, item=i, info=info)
                else:
                    return app_views.make_response(app_views.RESP_TYPE_ITEM, item_name, item=i, error=lang.error_permission_denied)
            else:
                return app_views.make_response(app_views.RESP_TYPE_ADMIN_USER_CHOOSE, item_name, info=lang.info_choose_user)
        else:
            return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=lang.error_permission_denied)
    flask.abort(404)


@item.route(prefix_thumbnail + '/<itemname:item_name>')
def thumbnail(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args)
        if item.user_may_view():
            item.create_thumbnail()
            thumbnail_item_path = item.thumbnail_item_path()
            if os.path.exists(thumbnail_item_path):
                return flask.send_file(thumbnail_item_path)
    flask.abort(404)


@item.route(prefix_userprofile + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_userprofile, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def userprofile(item_name):
    if flask.request.method == 'GET':
        return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, hint=lang.hint_resolution)
    else:
        user = auth.pygal_user.session_data.get_user()
        thumbnail_size_index = int(flask.request.form.get('select_thumbnail_size'))
        webnail_size_index = int(flask.request.form.get('select_webnail_size'))
        password_current = auth.password_salt_and_hash(flask.request.form.get('userprofile_password_current'))
        password1 = flask.request.form.get('userprofile_password1')
        password2 = flask.request.form.get('userprofile_password2')
        email = flask.request.form.get('userprofile_email')
        sdh = auth.session_data_handler()
        udh = auth.user_data_handler(sdh.get_user())
        sdh.set_thumbnail_size_index(thumbnail_size_index)
        sdh.set_webnail_size_index(webnail_size_index)
        udh.set_email(email)
        if flask.request.form.get('userprofile_password_current') != u'':
            if not auth.pygal_user.user_data.chk_password(password_current, user) or not password_current == auth.pygal_user.session_data.get_password():
                return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, error=lang.error_password_wrong_userprofile)
            elif password1 != password2:
                return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, error=lang.error_passwords_not_equal_userprofile)
            elif password1 == u'':
                return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, error=lang.error_password_empty_userprofile)
            else:
                sdh.set_password(auth.password_salt_and_hash(password1))
                udh.set_password(auth.password_salt_and_hash(password1), user)
        udh.store_user()
        return flask.redirect(config.url_prefix + url_extention(item_name))


@item.route(prefix_webnail + '/<itemname:item_name>')
def webnail(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args)
        if item.user_may_view():
            item.create_webnail()
            webnail_item_path = item.webnail_item_path()
            if os.path.exists(webnail_item_path):
                return flask.send_file(webnail_item_path)
    flask.abort(404)


@item.route(prefix_raw + '/<itemname:item_name>')
def raw(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args)
        if item.user_may_download():
            raw_path = item.raw_path()
            if os.path.isfile(raw_path):
                return flask.send_file(raw_path)
    flask.abort(404)


@item.route(prefix_download + '/<itemname:item_name>')
@item.route(prefix_download, defaults=dict(item_name=u''))
def download(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args)
        if item.user_may_download():
            raw_path = item.raw_path()
            if os.path.isfile(raw_path):
                return flask.send_file(raw_path, as_attachment=True)
            elif os.path.isdir(raw_path):
                def add_to_archive(arc, item):
                    for entry in item.itemlist():
                        if os.path.isfile(entry.raw_path()):
                            arc.write(entry.raw_path(), entry._rel_path)
                        else:
                            add_to_archive(arc, entry)
                mf = StringIO.StringIO()
                with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_STORED) as zf:
                    add_to_archive(zf, item)
                response = flask.make_response(mf.getvalue())
                response.headers['Content-Type'] = 'application/zip'
                response.headers["Content-Disposition"] = 'attachment; filename="%s.zip"' % item.name()
                return response
    flask.abort(404)


@item.route(prefix_add_tag + '/<itemname:item_name>', methods=['GET', 'POST'])
def add_tag(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name)
        if item.exists() and type(item) is not itemlist:
            if item.user_may_edit():
                if flask.request.method == 'GET':
                    return app_views.make_response(app_views.RESP_TYPE_ADD_TAG, item_name, item=item)
                elif flask.request.method == 'POST' and flask.request.form.get('tag_submit') == '1':
                    tag_id = flask.request.form.get('tag_id', None)
                    action = flask.request.form.get('action')
                    if action == 'Submit Tag':       # EDIT/ ADD
                        tag_text = flask.request.form.get('tag_text')
                        try:
                            x1 = int(flask.request.form.get('x1'))
                            x2 = int(flask.request.form.get('x2'))
                            y1 = int(flask.request.form.get('y1'))
                            y2 = int(flask.request.form.get('y2'))
                        except ValueError:
                            item.add_tag_wn(tag_text, tag_id)
                        else:
                            item.add_tag_wn_x1y1x2y2(x1, y1, x2, y2, tag_text, tag_id)
                        info = lang.info_tag_added % (tag_text)
                    elif action == 'Delete Tag':     # DELETE
                        tag_text = item.get_tag_text(tag_id)
                        item.delete_tag(tag_id)
                        info = lang.info_tag_deleted % (tag_text)
                    return app_views.make_response(app_views.RESP_TYPE_ITEM, item_name, item, info=info)
            else:
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=lang.error_permission_denied)
    flask.abort(404)


@item.route(prefix_delete + '/<itemname:item_name>', methods=['GET', 'POST'])
def delete(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args)
        if item.exists() and type(item) is not itemlist:
            if item.user_may_delete():
                if flask.request.method == 'GET':
                    return app_views.make_response(app_views.RESP_TYPE_DELETE, item_name, item)
                elif flask.request.method == 'POST' and flask.request.form.get('delete_submit') == '1':
                    item.delete()
                    return flask.redirect(item.parent_url())
            else:
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=lang.error_permission_denied)
    flask.abort(404)


@item.route(prefix_slideshow + '/<itemname:item_name>', methods=['GET', 'POST'])
def slideshow(item_name):
    return item(item_name, slideshow=True)


@item.route('/<itemname:item_name>', methods=['GET', 'POST'])
def item(item_name, slideshow=False):
    item_name = encode(item_name)
    if flask.request.args.get('search_request', None) is None:
        c = get_class_for_item(item_name)
    else:
        c = get_class_for_item(item_name, force_uncached=True, force_list=True)
    if c:
        item = c(item_name, flask.request.args, slideshow=slideshow)
        if item.exists():
            if item.user_may_view() or type(item) is itemlist:
                return app_views.make_response(app_views.RESP_TYPE_ITEM, item_name, item=item)
            else:
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=lang.error_permission_denied)
    flask.abort(404)
