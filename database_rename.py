'''
Created on 08.02.2018

@author: dirk
'''

from helpers import encode
import json
import os
from pygal_config import database_path as db_path
from pygal_config import item_path
from pygal_config import temp_path as trash_path
from pylibs import fstools


if __name__ == '__main__':
    for db_file in fstools.filelist(db_path, '*.json'):
        with open(db_file, 'r') as fh:
            db = json.load(fh)
        new_db_file = encode(os.path.join(db_path, db['_rel_path_'] + '.json'))
        trash_db_file = encode(os.path.join(trash_path, db['_rel_path_'] + '.json'))
        item_file = encode(os.path.join(item_path, db['_rel_path_']))
        if not os.path.exists(item_file):
            fstools.mkdir(os.path.dirname(trash_db_file))
            os.rename(db_file, trash_db_file)
        elif db_file != new_db_file:
            fstools.mkdir(os.path.dirname(new_db_file))
            os.rename(db_file, new_db_file)
