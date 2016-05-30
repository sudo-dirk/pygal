from app.items import item
from app import collector
from app import prefix_add_tag
from app import prefix_delete
from app import prefix_download
from app import prefix_edit
from app import prefix_info
from app import prefix_thumbnail
from app import prefix_webnail
from app import prefix_raw
from app import url_extention
from app import encode
from auth import pygal_user
import flask
from items import get_class_for_item
from items import itemlist
import lang
import os
from pygal_config import url_prefix
import StringIO
import zipfile


@item.route(prefix_thumbnail + '/<itemname:item_name>')
def thumbnail(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args, prefix=prefix_thumbnail)
        if item.user_may_view():
            item.create_thumbnail()
            thumbnail_item_path = item.thumbnail_item_path()
            if os.path.exists(thumbnail_item_path):
                return flask.send_file(thumbnail_item_path)
    flask.abort(404)


@item.route(prefix_webnail + '/<itemname:item_name>')
def webnail(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args, prefix=prefix_webnail)
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
        item = c(item_name, flask.request.args, prefix=prefix_raw)
        if item.user_may_download():
            raw_path = item.raw_path()
            if os.path.isfile(raw_path):
                return flask.send_file(raw_path)
        flask.abort(404)
    else:
        # TODO: implement answer
        return '!!! not yet implemented !!!'


@item.route(prefix_download + '/<itemname:item_name>')
def download(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args, prefix=prefix_download)
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
    else:
        # TODO: implement answer
        return '!!! not yet implemented !!!'


@item.route(prefix_edit + '/<itemname:item_name>')
@item.route(prefix_info + '/<itemname:item_name>')
@item.route(prefix_info, defaults=dict(item_name=u''))
def info(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args, prefix=prefix_info)
        inp = collector(title='Info: %s' % item.name(), url_prefix=url_prefix, url_extention=url_extention(item_name), this=item, pygal_user=pygal_user, lang=lang)
        rv = flask.render_template('header.html', input=inp)
        if item.exists():
            if item.user_may_view():
                rv += flask.render_template('info.html', input=inp)
            else:
                rv += lang.permission_denied
        rv += flask.render_template('footer.html', input=inp)
        return rv
    flask.abort(404)


@item.route(prefix_add_tag + '/<itemname:item_name>', methods=['GET', 'POST'])
def add_tag(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        tag_id = flask.request.args.get('tag_id')
        item = c(item_name)
        if item.exists() and type(item) is not itemlist:
            # TODO: Right management for tagging
            inp = collector(title='Add Tag: %s' % (item.name()), url_prefix=url_prefix, url_extention=url_extention(item_name), this=item, pygal_user=pygal_user, lang=lang, tag_id=tag_id)
            rv = flask.render_template('header.html', input=inp)
            rv += flask.render_template('add_tag.html', input=inp)
            rv += flask.render_template('footer.html', input=inp)
            return rv
    flask.abort(404)


@item.route(prefix_delete + '/<itemname:item_name>', methods=['GET', 'POST'])
def delete(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args, prefix=prefix_delete)
        if item.exists() and type(item) is not itemlist:
            inp = collector(title='Delete: %s' % (item.name()), url_prefix=url_prefix, url_extention=url_extention(item_name), this=item, pygal_user=pygal_user, lang=lang)
            rv = flask.render_template('header.html', input=inp)
            if item.user_may_delete():
                if flask.request.method == 'GET':
                    rv += flask.render_template('delete.html', input=inp)
                elif flask.request.method == 'POST' and flask.request.form.get('delete_submit') == '1':
                        item.delete()
                        return flask.redirect(item.parent_url())
                else:
                    flask.abort(500)
            else:
                rv += lang.permission_denied
            rv += flask.render_template('footer.html', input=inp)
            return rv
    flask.abort(404)


@item.route('/<itemname:item_name>', methods=['GET', 'POST'])
def item(item_name):
    item_name = encode(item_name)
    c = get_class_for_item(item_name)
    if c:
        item = c(item_name, flask.request.args)
        if flask.request.method == 'POST' and flask.request.form.get('tag_submit') == '1':
            # TODO: Right management for tagging
            tag_id = flask.request.form.get('tag_id', None)
            action = flask.request.form.get('action')
            if action == 'Submit Tag':       # EDIT/ ADD
                x1 = int(flask.request.form.get('x1'))
                x2 = int(flask.request.form.get('x2'))
                y1 = int(flask.request.form.get('y1'))
                y2 = int(flask.request.form.get('y2'))
                tag_text = flask.request.form.get('tag_text')
                item.add_tag_wn_x1y1x2y2(x1, y1, x2, y2, tag_text, tag_id)
            elif action == 'Delete Tag':     # DELETE
                item.delete_tag(tag_id)
        inp = collector(title=item.name(), url_prefix=url_prefix, url_extention=url_extention(item_name), this=item, pygal_user=pygal_user, lang=lang)
        rv = flask.render_template('header.html', input=inp)
        if item.user_may_view():
            if item.exists():
                if item.user_may_view() or type(item) is itemlist:
                    rv += flask.render_template(item.template(), input=inp)
                else:
                    rv += lang.permission_denied
        rv += flask.render_template('footer.html', input=inp)
        return rv
    flask.abort(404)
