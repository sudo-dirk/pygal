from app.items import item
from app import prefix_add_tag
from app import prefix_admin
from app import prefix_cachedataview
from app import prefix_delete
from app import prefix_download
from app import prefix_info
from app import prefix_slideshow
from app import prefix_thumbnail
from app import prefix_upload
from app import prefix_userprofile
from app import prefix_webnail
from app import prefix_raw
import app_views
from helpers import encode
from helpers import url_extention
from helpers import staging_container
import auth
import flask
from items import get_class_for_item
from items import supported_extentions
from items.picture import is_picture
from items import itemlist
import lang
import os
import pygal_config as config
from pylibs.multimedia import picture, video
import StringIO
import zipfile
from auth import pygal_user
from items.video import is_video


@item.route(prefix_admin + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_admin, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def admin(item_name):
    if not auth.pygal_user.may_admin():
        return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=lang.error_permission_denied)
    else:
        item_name = encode(item_name)
        admin_issue = flask.request.args.get('admin_issue')
        action = flask.request.args.get('action')
        container_uuid = flask.request.args.get('container_uuid')
        filename = flask.request.args.get('filename')
        c = get_class_for_item(item_name)
        if c:
            i = c(item_name, flask.request.args)
            if flask.request.method == 'GET':
                if admin_issue == 'staging' and action == 'thumb':
                    if container_uuid is not None and filename is not None:
                        # thumbnail picture
                        sc = staging_container(config.staging_path, None, None, None, None, None)
                        sc.load(sc.get_container_info_file_by_uuid(container_uuid))
                        if is_picture(filename):
                            i = picture.picture_edit(sc.get_container_file_path(filename))
                            i.resize(pygal_user.get_thumbnail_size())
                        elif is_video(filename):
                            i = video.video_picture_edit(sc.get_container_file_path(filename))
                            i.resize(pygal_user.get_thumbnail_size())
                            w = picture.picture_edit(os.path.join(os.path.join(os.path.dirname(__file__), '..', '..'), 'theme', 'static', 'common', 'img', 'thumbnail_movie.png'))
                            i.join(w, i.JOIN_TOP_RIGHT, 0.75)
                        else:
                            flask.abort(404)
                        fh = StringIO.StringIO()
                        i.get().save(fh, 'JPEG')
                        fh.seek(0)
                        return flask.send_file(fh, mimetype='image/jpeg')
                    flask.abort(404)
                else:
                    return app_views.make_response(app_views.RESP_TYPE_ADMIN, item_name, item=i)
            else:
                if admin_issue == 'permission':
                    user = app_views.get_form_user()
                    delete_rights = flask.request.form.get('delete-rights').split(',')
                    upload_right = flask.request.form.get('upload-right') == 'true'
                    download_right = flask.request.form.get('download-right') == 'true'
                    edit_rights = flask.request.form.get('edit-rights').split(',')
                    view_rights = flask.request.form.get('view-rights').split(',')
                    if user in [None, '']:
                        pdh = auth.public_data_handler()
                        pdh.set_rights_delete(delete_rights)
                        pdh.set_rights_upload(upload_right)
                        pdh.set_rights_download(download_right)
                        pdh.set_rights_edit(edit_rights)
                        pdh.set_rights_view(view_rights)
                        pdh.store_user()
                        info = "Public rights were changed. Check rights for safety reasons."
                    else:
                        udh = auth.user_data_handler(user)
                        udh.set_rights_delete(delete_rights)
                        udh.set_rights_upload(upload_right)
                        udh.set_rights_download(download_right)
                        udh.set_rights_edit(edit_rights)
                        udh.set_rights_view(view_rights)
                        udh.store_user()
                        info = "Rights for User '%s' changed. Check rights for safety reasons." % user
                    return app_views.make_response(app_views.RESP_TYPE_ADMIN, item_name, item=i, info=info)
                elif admin_issue == 'staging':
                    container_uuid = flask.request.form.get('container_uuid', container_uuid)
                    action = flask.request.form.get('action', action)
                    if action == 'commit':
                        target_path = flask.request.form.get('target_path')
                        if target_path != '':
                            sc = staging_container(config.staging_path, None, None, None, None, None)
                            sc.load(sc.get_container_info_file_by_uuid(container_uuid))
                            sc.move(target_path, config.database_folder, config.item_folder)
                            if sc.is_empty():
                                return flask.redirect(config.url_prefix + target_path)
                            else:
                                return app_views.make_response(app_views.RESP_TYPE_ADMIN, item_name, item=i, error='Not all elemets moved to target!')
                        else:
                            return app_views.make_response(app_views.RESP_TYPE_ADMIN, item_name, item=i, error='You need to check a folder!')
                    elif action == 'delete':
                        sc = staging_container(config.staging_path, None, None, None, None, None)
                        sc.load(sc.get_container_info_file_by_uuid(container_uuid))
                        sc.delete()
                        return app_views.make_response(app_views.RESP_TYPE_ADMIN, item_name, item=i)
    flask.abort(404)


@item.route(prefix_cachedataview + '/<itemname:item_name>')
@item.route(prefix_cachedataview, defaults=dict(item_name=u''))
def cachedataview(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        i = c(item_name, flask.request.args)
        if auth.pygal_user.may_admin():
            return app_views.make_response(app_views.RESP_TYPE_CACHEDATAVIEW, item_name, item=i)
    flask.abort(404)


@item.route(prefix_info + '/<itemname:item_name>')
@item.route(prefix_info, defaults=dict(item_name=u''))
def info(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        i = c(item_name, flask.request.args)
        if i.user_may_view():
            return app_views.make_response(app_views.RESP_TYPE_INFO, item_name, item=i)
    flask.abort(404)


@item.route(prefix_thumbnail + '/<itemname:item_name>')
def thumbnail(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        index = flask.request.args.get('index', None)
        if index is not None:
            index = int(index)
        item = c(item_name, flask.request.args)
        if item.user_may_view():
            item.create_thumbnail(index=index)
            thumbnail_item_path = item.thumbnail_item_path(index=index)
            if os.path.exists(thumbnail_item_path):
                return flask.send_file(thumbnail_item_path)
    flask.abort(404)


@item.route(prefix_userprofile + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_userprofile, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def userprofile(item_name):
    if flask.request.method == 'GET':
        return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, hint=lang.hint_resolution)
    else:
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
            if not udh.chk_password(password_current) or not password_current == sdh.get_password():
                return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, error=lang.error_password_wrong_userprofile)
            elif password1 != password2:
                return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, error=lang.error_passwords_not_equal_userprofile)
            elif password1 == u'':
                return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, item_name, error=lang.error_password_empty_userprofile)
            else:
                sdh.set_password(auth.password_salt_and_hash(password1))
                udh.set_password(auth.password_salt_and_hash(password1))
        udh.store_user()
        return flask.redirect(config.url_prefix + url_extention(item_name))


@item.route(prefix_upload + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_upload, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def upload(item_name):
    if pygal_user.may_upload():
        if flask.request.method == 'GET':
            return app_views.make_response(app_views.RESP_TYPE_UPLOAD, item_name)
        else:
            sc = staging_container(config.staging_path, flask.request.files.getlist("file[]"), supported_extentions(), pygal_user.get_session_user(), flask.request.form.get('container_name'), flask.request.environ['REMOTE_ADDR'])
            sc.save()
            if len(sc.allowed_files()) > 0:
                hint = 'Successfully uploaded the following files to Container %s:<br>* ' % sc.get(sc.KEY_UUID)
                hint += '<br>* '.join(sc.allowed_files())
            else:
                hint = None
            if len(sc.rejected_files()) > 0:
                error = 'Upload failed for the following files:<br>* '
                error += '<br>* '.join(sc.rejected_files())
            else:
                error = None
            return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=error, hint=hint)
    else:
        return app_views.make_response(app_views.RESP_TYPE_EMPTY, item_name, error=lang.error_permission_denied)


@item.route(prefix_webnail + '/<itemname:item_name>')
def webnail(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        index = flask.request.args.get('index', None)
        if index is not None:
            index = int(index)
        item = c(item_name, flask.request.args)
        if item.user_may_view():
            item.create_webnail(index=index)
            webnail_item_path = item.webnail_item_path(index=index)
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
