import flask
import hashlib
import json
import os
import pygal_config as config
from pylibs import fstools

user_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'users.json')
user_permission_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'users_%s.json')


class pygal_auth(object):
    def users(self):
        try:
            with open(user_file, 'r') as fh:
                users = json.loads(fh.read())
        except IOError:
            users = dict()
            self.store_users(users)
        return users

    def store_users(self, users):
        with open(user_file, 'w') as fh:
            fh.write(json.dumps(users, indent=4, sort_keys=True))

    def get_session_user(self):
        return flask.session.get('username')

    def get_session_password(self):
        return flask.session.get('password')

    def set_session_user(self, username):
        if username is None:
            flask.session.pop('username', None)
        else:
            flask.session.permanent = True
            flask.session['username'] = username

    def set_session_password(self, password):
        if password is None:
            flask.session.pop('password', None)
        else:
            flask.session.permanent = True
            flask.session['password'] = password

    def user_url(self, url_extention=''):
        from app import prefix_userprofile
        return config.url_prefix + prefix_userprofile + url_extention

    def get_rights_uid(self):
        filename = user_permission_file % self.get_session_user()
        if os.path.isfile(filename):
            return fstools.uid(filename)
        return 'no_rights_uid'

    def get_perms_dict(self):
        try:
            return json.loads(open(user_permission_file % self.get_session_user(), 'r').read())
        except IOError:
            return {}

    def chk_perms(self, perm_name, item):
        from app import decode
        permission_obj = self.get_perms_dict().get(perm_name, None)
        if permission_obj is not None:
            for entry in permission_obj:
                if decode(item._rel_path).startswith(entry):
                    return True
        return False

    def may_view(self, item):
        if self.may_admin() or len(item._rel_path) == 0:
            return True
        return self.chk_perms('view', item)

    def may_delete(self, item):
        if self.may_admin():
            return True
        return self.chk_perms('delete', item)

    def may_download(self, item):
        if self.may_admin():
            return True
        return self.get_perms_dict().get('download', False) and item.user_may_view()

    def may_admin(self):
        return self.chk_login() and self.get_session_user() in config.admin_group

    def is_a_user_logged_in(self):
        return self.chk_login()

    def user_exists(self, username):
        return username in self.users()

    def password_correct(self, username, password):
        return password is not None and password == self.users().get(username, {}).get('password', None)

    def chk_login(self):
        return self.user_exists(self.get_session_user()) and self.password_correct(self.get_session_user(), self.get_session_password())

    def login(self, username, password, url_extention):
        if self.password_correct(username, password):
            resp = flask.make_response(flask.redirect(config.url_prefix + url_extention))
            self.set_session_user(username)
            self.set_session_password(password)
            return resp
        else:
            return self.logout(url_extention)

    def logout(self, url_extention):
            resp = flask.make_response(flask.redirect(config.url_prefix + url_extention))
            self.set_session_user(None)
            self.set_session_password(None)
            return resp

    def password_salt_and_hash(self, password):
        return hashlib.sha512(password.encode('utf-8') + config.secret_key.encode('utf-8')).hexdigest()

    def login_by_form(self, fdata, url_extention):
        fusername = fdata.get('login_username')
        fpassword = self.password_salt_and_hash(fdata.get('login_password'))
        return self.login(fusername, fpassword, url_extention)

    def create_user_by_form(self, fdata, url_extention):
        fusername = fdata.get('register_username')
        fpassword1 = self.password_salt_and_hash(fdata.get('register_password1'))
        fpassword2 = self.password_salt_and_hash(fdata.get('register_password2'))
        femail = fdata.get('register_email')
        if not self.user_exists(fusername) and fpassword1 == fpassword2:
            users = self.users()
            users[fusername] = {'password': fpassword1, 'email': femail}
            self.store_users(users)
            return self.login(fusername, fpassword1, url_extention)
        from app import prefix_lostpass
        return flask.redirect(config.url_prefix + prefix_lostpass + url_extention)

pygal_user = pygal_auth()
