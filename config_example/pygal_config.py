import os
import urllib

DEBUG = False
ip_to_serve_from = '127.0.0.1'
secret_key = 'This should be a real secret string including all kinds of characters'
admin_group = []
#
thumbnail_size_list = [137, 175, 225]
thumbnail_size_default = 1
webnail_size_list = [450, 1100, 1750]
webnail_size_default = 1
# e.g.
# url_prefix = urllib.quote('/test')
url_prefix = urllib.quote('')
basepath = os.path.abspath(os.path.dirname(__file__))
trash_path = 'data/trash'
item_folder = 'data/items'
database_folder = 'data/database'
citem_folder = os.path.join(basepath, 'data/cache/citems')
iprop_folder = os.path.join(basepath, 'data/cache/iprops')
