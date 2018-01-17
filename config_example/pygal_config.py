import os
import urllib

DEBUG = False
ip_to_serve_from = '127.0.0.1'
# create this e.g. by the following command: binascii.hexlify(os.urandom(24))
secret_key = 'This should be a real secret string including all kinds of characters'
admin_group = []
multimedia_only = True
#
thumbnail_size_list = [137, 175, 225]
thumbnail_size_default = 1
webnail_size_list = [450, 1100, 1750]
webnail_size_default = 1
# e.g.
# url_prefix = urllib.quote('/test')
url_prefix = urllib.quote('')
basepath = os.path.abspath(os.path.dirname(__file__))
trash_path = os.path.join(basepath, 'data', 'trash')
temp_path = os.path.join(basepath, 'data', 'tmp')
staging_path = os.path.join(basepath, 'data', 'staging')
item_path = os.path.join(basepath, 'data', 'items')
database_path = os.path.join(basepath, 'data', 'database')
cache_path = os.path.join(basepath, 'data', 'cache')
