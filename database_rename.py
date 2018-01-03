import pygal_config
from pylibs import fstools
import json
import os

for filename in fstools.filelist(pygal_config.database_folder):
    with open(filename, 'r') as fh:
        db_dict = json.loads(fh.read())

    old = filename
    new = os.path.join(pygal_config.database_folder, db_dict.get('_common_').get('rel_path').replace(os.path.sep, '_').replace(os.path.extsep, '_') + '.json')
    os.rename(old, new)
