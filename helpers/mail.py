import auth
from email.mime.text import MIMEText
import logging
import pygal_config as config
from pylibs import report
from subprocess import Popen, PIPE
import flask

logger = logging.getLogger('pygal.items')


def to_adr_admins():
    return '; '.join([auth.user_data_handler(user).get_email() for user in config.admin_group])


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
        return flask.request.url[:-len(flask.request.path)]
