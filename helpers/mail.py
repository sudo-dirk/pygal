import auth
from email.mime.text import MIMEText
import helpers
import pygal_config as config
from pylibs import report
from subprocess import Popen, PIPE
import flask
from prefixes import prefix_token
from prefixes import prefix_admin 

import logging
logger = logging.getLogger('app logger')


def to_adr_admins():
    return ', '.join([auth.user_data_handler(user).get_email() for user in config.admin_group])


class mail(report.logit):
    LOG_PREFIX = 'mail:'

    def __init__(self):
        try:
            self.sendmail_cmd = config.sendmail_cmd
        except AttributeError:
            self.sendmail_cmd = None
        try:
            self.from_adr = config.from_adr
        except AttributeError:
            self.from_adr = None

    def send(self, to_adr, content):
        msg = MIMEText(content.message)
        msg["From"] = self.from_adr
        msg["To"] = to_adr
        msg["Subject"] = content.subject
        if self.sendmail_cmd is not None and config.DEBUG:
            p = Popen([self.sendmail_cmd, "-t", "-oi"], stdin=PIPE)
            p.communicate(msg.as_string())
        else:
            self.logit_info(logger, msg.as_string())


class content_new_user():
    def __init__(self, username):
        udh = auth.user_data_handler(username)
        self.subject = 'New Account created (%s at %s)' % (username, self.base_url())
        self.message = """A user created an account.

Details:
--------
- Page:  %s
- User:  %s
- Email: %s

Edit the permission setting to grant access.

Have a nice day,

your pygal""" % (self.base_url(), username, udh.get_email())

    def base_url(self):
        return flask.request.url_root[:-1] + config.url_prefix


class content_pw_recovery(content_new_user):
    def __init__(self, token):
        self.subject = 'Password Recovery at %s' % self.base_url()
        self.message = """A password recovery had been triggered. If you did not trigger the recovery, use the password token or ignore it and it will be invalid in %.1f hours or

follow you token url %s to set your password.


Have a nice day,

your pygal""" % (config.token_valid_time / 3600., self.base_url() + prefix_token + '/' + token.get(token.KEY_TOKEN))


class content_account_creation(content_new_user):
    def __init__(self, token):
        self.subject = 'E-Mail-Confirmation for User-Account-Creation at %s' % self.base_url()
        self.message = """A User-Account-Creation had been requested. If you did not request the user account, ignore that email or

follow you token url %s to activate the account.


Have a nice day,

your pygal""" % (self.base_url() + prefix_token + '/' + token.get(token.KEY_TOKEN))


class content_email_confirmation(content_new_user):
    def __init__(self, token):
        self.subject = 'E-Mail-Confirmation for addresschange at %s' % self.base_url()
        self.message = """An E-Mail-Confirmation is needed to change the stored E-Mail-Address. If you did not trigger the address change, ignore that email or

follow you token url %s to change your E-Mailaddress.


Have a nice day,

your pygal""" % (self.base_url() + prefix_token + '/' + token.get(token.KEY_TOKEN))


class content_upload(content_new_user):
    def __init__(self):
        self.subject = 'Data had been uploaded at %s' % self.base_url()
        self.message = """A User uploaded new items. Go to the staging area %s to commit items to your gallery.


Have a nice day,

your pygal""" % (self.base_url() + prefix_admin + helpers.strargs({helpers.STR_ARG_ADMIN_ISSUE: helpers.STR_ARG_ADMIN_ISSUE_STAGING}))
