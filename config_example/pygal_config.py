import os

DEBUG = True
ip_to_serve_from = '127.0.0.1'
secret_key = 'This should be a real secret string including all kinds of characters'
admin_group = []
thumbnail_size = 150
webnail_size = 1300
# e.g.
# url_prefix = '/test'
url_prefix = ''
basepath = os.path.abspath(os.path.dirname(__file__))
trash_path = 'data/trash'
item_folder = 'data/items'
database_folder = 'data/database'
citem_folder = os.path.join(basepath, 'data/cache/citems')
iprop_folder = os.path.join(basepath, 'data/cache/iprops')
