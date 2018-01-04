import flask
import hashlib
from helpers import decode
import json
import os
import pygal_config as config
from pylibs import fstools

basepath = os.path.abspath(os.path.dirname(__file__))


def password_salt_and_hash(password):
    return hashlib.sha512(password.encode('utf-8') + config.secret_key.encode('utf-8')).hexdigest()


def rights_uid(user):
    if user is None:
        filename = public_data_handler().data_filename(user)
    else:
        filename = user_data_handler().data_filename(user)
    if os.path.isfile(filename):
        return fstools.uid(filename)
    return 'no_user_rights_uid'


class user_data_handler(dict):
    USER_FILE_PREFIX = 'user_'
    USER_FILE_EXTENTION = 'json'
    KEY_EMAIL = 'email'
    KEY_PASSWORD = 'password'
    KEY_RIGHTS = 'rights'
    KEY_RIGHTS_DELETE = 'delete'
    KEY_RIGHTS_DOWNLOAD = 'download'
    KEY_RIGHTS_EDIT = 'edit'
    KEY_RIGHTS_VIEW = 'view'

    def __init__(self, user=None):
        dict.__init__(self)
        self._user = None
        self.load_user(user, force=True)

    def chk_password(self, password, user=None):
        return password is not None and self.get_password(user) == password

    def chk_rights_delete(self, item_path, user=None):
        try:
            return item_path in self.get_rights_delete(user)
        except TypeError:
            pass
        return False

    def chk_rights_download(self, item_path, user=None):
        return self.get_rights_download(user) is not None and self.get_rights_download(user)

    def chk_rights_edit(self, item_path, user=None):
        try:
            return item_path in self.get_rights_edit(user)
        except TypeError:
            pass
        return False

    def chk_rights_view(self, item_path, user=None):
        try:
            return item_path in self.get_rights_view(user)
        except TypeError:
            pass
        return False

    def data_filename(self, user):
        return os.path.join(basepath, self.USER_FILE_PREFIX + user + '.' + self.USER_FILE_EXTENTION)

    def get_email(self, user=None):
        self.load_user(user)
        try:
            return self[self.KEY_EMAIL]
        except KeyError:
            return None

    def get_password(self, user=None):
        self.load_user(user)
        try:
            return self[self.KEY_PASSWORD]
        except KeyError:
            return None

    def get_rights(self, user=None):
        self.load_user(user)
        try:
            return self[self.KEY_RIGHTS]
        except KeyError:
            return None

    def get_rights_delete(self, user=None):
        try:
            return self.get_rights(user)[self.KEY_RIGHTS_DELETE]
        except (TypeError, KeyError):
            return None

    def get_rights_download(self, user=None):
        try:
            return self.get_rights(user)[self.KEY_RIGHTS_DOWNLOAD]
        except (TypeError, KeyError):
            return None

    def get_rights_edit(self, user=None):
        try:
            return self.get_rights(user)[self.KEY_RIGHTS_EDIT]
        except (TypeError, KeyError):
            return None

    def get_rights_view(self, user=None):
        try:
            return self.get_rights(user)[self.KEY_RIGHTS_VIEW]
        except (TypeError, KeyError):
            return None

    def load_store_condition(self, user):
        return user is not None

    def load_user(self, user, force=False):
        if (user is not self._user or force) and self.load_store_condition(user):
            self._user = user
            try:
                with open(self.data_filename(user), 'r') as fh:
                    dict.__init__(self, json.loads(fh.read()))
            except IOError:
                self.clear()

    def set_email(self, email, user=None):
        self.load_user(user)
        self[self.KEY_EMAIL] = email

    def set_password(self, password, user=None):
        self.load_user(user)
        self[self.KEY_PASSWORD] = password

    def set_rights_delete(self, right_list, user=None):
        self.load_user(user)
        if self.KEY_RIGHTS not in self:
            self[self.KEY_RIGHTS] = {}
        self[self.KEY_RIGHTS][self.KEY_RIGHTS_DELETE] = right_list

    def set_rights_download(self, right, user=None):
        self.load_user(user)
        if self.KEY_RIGHTS not in self:
            self[self.KEY_RIGHTS] = {}
        self[self.KEY_RIGHTS][self.KEY_RIGHTS_DOWNLOAD] = right

    def set_rights_edit(self, right_list, user=None):
        self.load_user(user)
        if self.KEY_RIGHTS not in self:
            self[self.KEY_RIGHTS] = {}
        self[self.KEY_RIGHTS][self.KEY_RIGHTS_EDIT] = right_list

    def set_rights_view(self, right_list, user=None):
        self.load_user(user)
        if self.KEY_RIGHTS not in self:
            self[self.KEY_RIGHTS] = {}
        self[self.KEY_RIGHTS][self.KEY_RIGHTS_VIEW] = right_list

    def store_user(self):
        if self.load_store_condition(self._user):
            with open(self.data_filename(self._user), 'w') as fh:
                fh.write(json.dumps(self, indent=4, sort_keys=True))

    def users(self):
        rv = fstools.filelist(basepath, self.data_filename('*'), False)
        for i in range(0, len(rv)):
            entry = os.path.basename(rv[i])
            if entry.startswith(self.USER_FILE_PREFIX) and entry.endswith(self.USER_FILE_EXTENTION):
                rv[i] = decode(entry[len(self.USER_FILE_PREFIX):-len(self.USER_FILE_EXTENTION) - 1])
        return rv

    def user_exists(self, username):
        return username in self.users()


class public_data_handler(user_data_handler):
    def data_filename(self, user):
        return os.path.join(basepath, 'public.json')

    def load_store_condition(self, user):
        return True


class session_data_handler(object):
    KEY_PASSWORD = 'password'
    KEY_THUMBNAIL_SIZE_INDEX = 'thumbnail_size_index'
    KEY_USERNAME = 'username'
    KEY_WEBNAIL_SIZE_INDEX = 'webnail_size_index'

    def get_password(self):
        return flask.session.get(self.KEY_PASSWORD)

    def get_thumbnail_index(self):
        return flask.session.get(self.KEY_THUMBNAIL_SIZE_INDEX)

    def get_webnail_index(self):
        return flask.session.get(self.KEY_WEBNAIL_SIZE_INDEX)

    def get_user(self):
        return flask.session.get(self.KEY_USERNAME)

    def set_password(self, password):
        if password is None:
            flask.session.pop(self.KEY_PASSWORD, None)
        else:
            flask.session.permanent = True
            flask.session[self.KEY_PASSWORD] = password

    def set_thumbnail_size_index(self, index):
        if index is None:
            flask.session.pop(self.KEY_THUMBNAIL_SIZE_INDEX, None)
        else:
            flask.session.permanent = True
            flask.session[self.KEY_THUMBNAIL_SIZE_INDEX] = index

    def set_webnail_size_index(self, index):
        if index is None:
            flask.session.pop(self.KEY_WEBNAIL_SIZE_INDEX, None)
        else:
            flask.session.permanent = True
            flask.session[self.KEY_WEBNAIL_SIZE_INDEX] = index

    def set_user(self, username):
        if username is None:
            flask.session.pop(self.KEY_USERNAME, None)
        else:
            flask.session.permanent = True
            flask.session[self.KEY_USERNAME] = username

    def chk_login(self):
        username = self.get_user()
        password = self.get_password()
        user_exists = username in user_data_handler().users()
        return user_exists and user_data_handler(username).chk_password(password)


class pygal_auth(object):
    def _admin_right_list_(self, user, perm_name):
        class admin_folder_list(list):
            def __init__(self):
                list.__init__(self)

            def append(self, rel_path, selected=False):
                o = dict()
                o['id'] = rel_path
                o['text'] = os.path.basename(rel_path)
                o['state'] = {"selected": selected}
                o['children'] = admin_folder_list()
                try:
                    list.append(self.object_to_append(o), o)
                except TypeError:
                    list.append(self, o)

            def object_to_append(self, o):
                rv = None
                for item in self:
                    rv = item['children'].object_to_append(o)
                    if rv is not None:
                        return rv
                    if os.path.dirname(o['id']) == item['id']:
                        return item['children']
                return rv
        folder_list = fstools.dirlist(config.item_folder, True)
        folder_list.sort()

        if user is None:
            udh = public_data_handler()
        else:
            udh = user_data_handler(user)
        al = admin_folder_list()
        for i in range(0, len(folder_list)):
            rel_path = decode(folder_list[i][len(config.item_folder) + 1:])
            try:
                selected = rel_path in udh.get_rights().get(perm_name)
            except (AttributeError, TypeError):
                selected = False
            al.append(rel_path, selected)
        return al

    def admin_view_right_list(self, user):
        return json.dumps(self._admin_right_list_(user, 'view'), indent=4, sort_keys=True)

    def admin_edit_right_list(self, user):
        return json.dumps(self._admin_right_list_(user, 'edit'), indent=4, sort_keys=True)

    def admin_delete_right_list(self, user):
        return json.dumps(self._admin_right_list_(user, 'delete'), indent=4, sort_keys=True)

    def admin_download_right(self, user):
        try:
            if user is None:
                udh = public_data_handler()
            else:
                udh = user_data_handler(user)
            return udh.get_rights().get(udh.KEY_RIGHTS_DOWNLOAD)
        except (AttributeError, TypeError):
            return False

    def chk_login(self):
        return session_data_handler().chk_login()

    def get_my_email(self):
        return user_data_handler(self.get_session_user()).get_email()

    def get_session_user(self):
        return session_data_handler().get_user()

    def get_thumbnail_size(self):
        thumbnail_size_index = session_data_handler().get_thumbnail_index()
        if thumbnail_size_index is None:
            thumbnail_size_index = config.thumbnail_size_default
        return config.thumbnail_size_list[thumbnail_size_index]

    def get_webnail_size(self):
        webnail_size_index = session_data_handler().get_webnail_index()
        if webnail_size_index is None:
            webnail_size_index = config.webnail_size_default
        return config.webnail_size_list[webnail_size_index]

    def users(self):
        return user_data_handler().users()

    def user_url(self, url_extention=''):  # TODO: move this method to a more sensefull place
        # TODO: reduce late impoerts
        from app import prefix_userprofile
        return config.url_prefix + prefix_userprofile + url_extention

    def may_view(self, item):
        if len(item._rel_path) == 0:
            return True
        if not item.is_itemlist():
            path = decode(os.path.dirname(item._rel_path))
        else:
            path = decode(item._rel_path)
        user = self.get_session_user()
        if user is None:
            return public_data_handler().chk_rights_view(path)
        else:
            return user_data_handler(user).chk_rights_view(path)

    def may_delete(self, item):
        if not item.is_itemlist():
            path = decode(os.path.dirname(item._rel_path))
        else:
            path = decode(item._rel_path)
        user = self.get_session_user()
        if user is None:
            return public_data_handler().chk_rights_delete(path)
        else:
            return user_data_handler(user).chk_rights_delete(path)

    def may_download(self, item):
        if not item.is_itemlist():
            path = decode(os.path.dirname(item._rel_path))
        else:
            path = decode(item._rel_path)
        user = self.get_session_user()
        if user is None:
            return public_data_handler().chk_rights_download(path)
        else:
            return user_data_handler(user).chk_rights_download(path)

    def may_edit(self, item):
        if not item.is_itemlist():
            path = decode(os.path.dirname(item._rel_path))
        else:
            path = decode(item._rel_path)
        user = self.get_session_user()
        if user is None:
            return public_data_handler().chk_rights_edit(path)
        else:
            return user_data_handler(user).chk_rights_edit(path)

    def may_admin(self):
        sdh = session_data_handler()
        return sdh.chk_login() and sdh.get_user() in config.admin_group


pygal_user = pygal_auth()
