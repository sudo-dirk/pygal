from app.items import item
import app_views
import auth
import flask
import items
import lang
import os
from prefixes import prefix_add_tag
from prefixes import prefix_admin
from prefixes import prefix_delete
from prefixes import prefix_download
from prefixes import prefix_info
from prefixes import prefix_slideshow
from prefixes import prefix_thumbnail
from prefixes import prefix_upload
from prefixes import prefix_userprofile
from prefixes import prefix_webnail
from prefixes import prefix_raw
import pygal_config as config
from pylibs.multimedia import picture, video
import StringIO
import time
import zipfile
from auth import pygal_user
from items.video import is_video
import uuid
import helpers

@item.route(prefix_admin + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_admin, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def admin(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        if not i.user_may_admin():
            return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error=lang.error_permission_denied)
        else:
            if flask.request.method == 'GET':
                action = flask.request.args.get(helpers.STR_ARG_ADMIN_ACTION)
                admin_issue = flask.request.args.get(helpers.STR_ARG_ADMIN_ISSUE, helpers.STR_ARG_ADMIN_ISSUE_PERMISSION)
                container_uuid = flask.request.args.get(helpers.STR_ARG_ADMIN_CONTAINER)
                name = flask.request.args.get(helpers.STR_ARG_ADMIN_NAME)
                # STAGING THUMB
                if admin_issue == helpers.STR_ARG_ADMIN_ISSUE_STAGING and action == helpers.STR_ARG_ADMIN_ACTION_THUMB:
                    if container_uuid is not None and name is not None:
                        # thumbnail picture
                        sc = items.staging_container(config.staging_path, container_uuid, None, None)
                        if items.picture.is_picture(name):
                            i = picture.picture_edit(sc.get_container_file_path(name))
                            i.resize(pygal_user.get_thumbnail_size())
                        elif is_video(name):
                            i = video.video_picture_edit(sc.get_container_file_path(name))
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
                # FOLDER PAGE
                elif admin_issue == helpers.STR_ARG_ADMIN_ISSUE_FOLDERS:
                    return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, hint='Mark the folder you want to delete or where you want to create a subfolder.')
                # ALL OTHER ADMIN PAGES
                else:
                    return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc)
            else:
                action = flask.request.form.get(helpers.STR_ARG_ADMIN_ACTION)
                admin_issue = flask.request.form.get(helpers.STR_ARG_ADMIN_ISSUE, helpers.STR_ARG_ADMIN_ISSUE_PERMISSION)
                container_uuid = flask.request.form.get(helpers.STR_ARG_ADMIN_CONTAINER)
                name = flask.request.form.get(helpers.STR_ARG_ADMIN_NAME)
                target = flask.request.form.get(helpers.STR_ARG_ADMIN_TARGET)
                if admin_issue == helpers.STR_ARG_ADMIN_ISSUE_PERMISSION:
                    user = app_views.get_form_user()
                    # TODO: Add args to helpers, upload and download for public not working
                    delete_rights = flask.request.form.get('delete-rights').split(',')
                    upload_right = flask.request.form.get('upload-right') == 'true'
                    download_right = flask.request.form.get('download-right') == 'true'
                    edit_rights = flask.request.form.get('edit-rights').split(',')
                    view_rights = flask.request.form.get('view-rights').split(',')
                    if user == '':
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
                    return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, info=info)
                elif admin_issue == helpers.STR_ARG_ADMIN_ISSUE_STAGING:
                    if action == helpers.STR_ARG_ADMIN_ACTION_COMMIT:
                        if target != '':
                            sc = items.staging_container(config.staging_path, container_uuid, None, None)
                            sc.move(helpers.encode(target), config.database_path, config.item_path)
                            if sc.is_empty():
                                return flask.redirect(config.url_prefix + target)
                            else:
                                return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, error='Not all elemets moved to target!')
                        else:
                            return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, error='You need to check a folder!')
                    elif action == helpers.STR_ARG_ADMIN_ACTION_DELETE:
                        sc = items.staging_container(config.staging_path, container_uuid, None, None)
                        sc.delete()
                        return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc, info='Staging-Container %s deleted' % sc.get(sc.KEY_CONTAINERNAME))
                elif admin_issue == helpers.STR_ARG_ADMIN_ISSUE_FOLDERS:
                    if action == helpers.STR_ARG_ADMIN_ACTION_CREATE:
                        target = os.path.join(target, name)
                        try:
                            os.mkdir(os.path.join(config.item_path, helpers.encode(target)))
                        except OSError:
                            return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, error='Folder %s can not be created. The parent folder has possibly insufficient rights' % target, hint='Mark the folder you want to delete or where you want to create a subfolder.')
                        return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, info='Folder %s succesfully created.' % target, hint='Mark the folder you want to delete or where you want to create a subfolder.')
                    elif action == helpers.STR_ARG_ADMIN_ACTION_DELETE:
                        try:
                            os.rmdir(os.path.join(config.item_path, helpers.encode(target)))
                        except OSError:
                            return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, error='Folder %s can not be deleted. The folder is possibly not empty' % target, hint='Mark the folder you want to delete or where you want to create a subfolder.')
                        return app_views.make_response(app_views.RESP_TYPE_ADMIN, i, tmc, info='Folder %s succesfully deleted.' % target, hint='Mark the folder you want to delete or where you want to create a subfolder.')
    flask.abort(404)


@item.route(prefix_info + '/<itemname:item_name>')
@item.route(prefix_info, defaults=dict(item_name=u''))
def info(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        if i.user_may_view():
            return app_views.make_response(app_views.RESP_TYPE_INFO, i, tmc)
    flask.abort(404)


@item.route(prefix_thumbnail + '/<itemname:item_name>')
def thumbnail(item_name):
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        index = flask.request.args.get(helpers.STR_ARG_THUMB_INDEX, None)
        if index is not None:
            index = int(index)
        else:
            index = config.thumbnail_size_default
        if i.user_may_view():
            i.create_thumbnail(index)
            thumbnail_item_path = i.citem_filename(config.thumbnail_size_list[index])
            # send thumbnail, if exists
            if os.path.exists(thumbnail_item_path):
                return flask.send_file(thumbnail_item_path)
    flask.abort(404)


@item.route(prefix_userprofile + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_userprofile, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def userprofile(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        if flask.request.method == 'GET':
            return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, i, tmc)
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
                    return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, i, tmc, error=lang.error_password_wrong_userprofile)
                elif password1 != password2:
                    return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, i, tmc, error=lang.error_passwords_not_equal_userprofile)
                elif password1 == u'':
                    return app_views.make_response(app_views.RESP_TYPE_USERPROFILE, i, tmc, error=lang.error_password_empty_userprofile)
                else:
                    sdh.set_password(auth.password_salt_and_hash(password1))
                    udh.set_password(auth.password_salt_and_hash(password1))
            udh.store_user()
            return flask.redirect(config.url_prefix + helpers.url_extention(item_name))
    flask.abort(404)


@item.route(prefix_upload + '/<itemname:item_name>', methods=['GET', 'POST'])
@item.route(prefix_upload, defaults=dict(item_name=u''), methods=['GET', 'POST'])
def upload(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        if i.user_may_upload():
            if flask.request.method == 'GET':
                return app_views.make_response(app_views.RESP_TYPE_UPLOAD, i, tmc)
            else:
                db = items.database.database_handler(None, None)
                db.add_data(db.KEY_UPLOAD_USERNAME, pygal_user.get_session_user())
                db.add_data(db.KEY_UPLOAD_TIMESTAMP, time.time())
                db.add_data(db.KEY_UPLOAD_SRC_IP, flask.request.environ['REMOTE_ADDR'])
                if config.multimedia_only:
                    sc = items.staging_container(config.staging_path, None, flask.request.form.get('container_name'), items.supported_extentions())
                else:
                    sc = items.staging_container(config.staging_path, None, flask.request.form.get('container_name'), None)
                failed_files = []
                for f in flask.request.files.getlist("file[]"):
                    f.filename = helpers.encode(f.filename)
                    success = sc.append_file_upload(f, db)
                    if not success:
                        failed_files.append(f.filename)
                if len(failed_files) == 0:
                    hint = 'Successfully uploaded all files to Container %s.' % sc.get(sc.KEY_UUID)
                    error = None
                else:
                    hint = None
                    error = 'Upload failed for the following files:<br>'
                    for filename in failed_files:
                        error += ' * %s<br>' % filename
                return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc, error=error, hint=hint)
        else:
            return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error=lang.error_permission_denied)
    flask.abort(404)



@item.route(prefix_webnail + '/<itemname:item_name>')
def webnail(item_name):
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        index = flask.request.args.get(helpers.STR_ARG_WEB_INDEX, None)
        if index is not None:
            index = int(index)
        else:
            index = config.webnail_size_default
        if i.user_may_view():
            i.create_webnail(index)
            webnail_item_path = i.citem_filename(config.webnail_size_list[index])
            if os.path.exists(webnail_item_path):
                return flask.send_file(webnail_item_path)
    flask.abort(404)


@item.route(prefix_raw + '/<itemname:item_name>')
def raw(item_name):
    item_name = helpers.encode(item_name)
    item = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if item is not None:
        if item.user_may_download():
            raw_path = item.raw_path()
            if os.path.isfile(raw_path):
                return flask.send_file(raw_path)
    flask.abort(404)


@item.route(prefix_download + '/<itemname:item_name>')
@item.route(prefix_download, defaults=dict(item_name=u''))
def download(item_name):
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        if i.user_may_download():
            raw_path = i.raw_path()
            if os.path.isfile(raw_path):
                return flask.send_file(raw_path, as_attachment=True)
            elif os.path.isdir(raw_path):
                def add_to_archive(arc, i):
                    for entry in i.get_itemlist():
                        if os.path.isfile(entry.raw_path()):
                            arc.write(entry.raw_path(), entry._rel_path)
                        else:
                            add_to_archive(arc, entry)
                temp_file = os.path.join(config.temp_path, str(uuid.uuid4()) + '.zip')
                with open(temp_file, 'w') as fh:
                    with zipfile.ZipFile(fh, mode='w', compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
                        add_to_archive(zf, i)

                @flask.after_this_request
                def remove_file(response):
                    os.remove(temp_file)
                    return response
                return flask.send_file(temp_file, mimetype='application/zip', as_attachment=True, attachment_filename='%s.zip' % helpers.encode(i.name()))
    flask.abort(404)


@item.route(prefix_add_tag + '/<itemname:item_name>', methods=['GET', 'POST'])
def add_tag(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        if i.exists() and not i.is_itemlist():
            if i.user_may_edit():
                if flask.request.method == 'GET':
                    return app_views.make_response(app_views.RESP_TYPE_ADD_TAG, i, tmc)
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
                            i.add_tag_wn(tag_text, tag_id)
                        else:
                            i.add_tag_wn_x1y1x2y2(x1, y1, x2, y2, tag_text, tag_id)
                        info = lang.info_tag_added % (tag_text)
                    elif action == 'Delete Tag':     # DELETE
                        tag_text = i.get_tag_text(tag_id)
                        i.delete_tag(tag_id)
                        info = lang.info_tag_deleted % (tag_text)
                    return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc, info=info)
            else:
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error=lang.error_permission_denied)
    flask.abort(404)


@item.route(prefix_delete + '/<itemname:item_name>', methods=['GET', 'POST'])
def delete(item_name):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, False, config.database_path, config.cache_path, None)
    if i is not None:
        if i.exists() and not i.is_itemlist():
            if i.user_may_delete():
                if flask.request.method == 'GET':
                    return app_views.make_response(app_views.RESP_TYPE_DELETE, i, tmc)
                elif flask.request.method == 'POST' and flask.request.form.get('delete_submit') == '1':
                    n = 0
                    sc = items.staging_container(config.staging_path, os.path.basename(i.raw_path()), i.name(), None)
                    while not sc.is_empty():
                        n += 1
                        sc = items.staging_container(config.staging_path, os.path.basename(i.raw_path()) + '-%d' % n, i.name() + '-%d' % n, None)
                    sc.append_file_delete(i.raw_path(), i.get_database_content())
                    i.delete()
                    return app_views.make_response(app_views.RESP_TYPE_ITEM, i.parent(), tmc, info=lang.info_item_deleted % i.name(True))
            else:
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error=lang.error_permission_denied)
    flask.abort(404)


@item.route(prefix_slideshow + '/<itemname:item_name>', methods=['GET', 'POST'])
def slideshow(item_name):
    return item_view(item_name, slideshow=True)


@item.route('/<itemname:item_name>', methods=['GET', 'POST'])
def item_view(item_name, slideshow=False):
    tmc = helpers.time_measurement()
    item_name = helpers.encode(item_name)
    i = items.get_item_by_path(item_name, config.item_path, slideshow, config.database_path, config.cache_path, None)
    if i is not None:
        if i.exists() and i.user_may_view():
            return app_views.make_response(app_views.RESP_TYPE_ITEM, i, tmc)
        else:
            if i.is_a_searchresult():
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, info=lang.info_empty_search)
            else:
                return app_views.make_response(app_views.RESP_TYPE_EMPTY, i, tmc, error=lang.error_permission_denied)
    flask.abort(404)
