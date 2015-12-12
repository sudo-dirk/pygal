import os
import sys

basepath = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basepath)

#import site
#site.addsitedir(os.path.join(basepath, 'venv', 'lib', 'python2.7', 'site-packages'))

from pygal import app as application

