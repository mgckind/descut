""" Settings for application"""
import os
DEBUG = True
DIRNAME = os.path.dirname(__file__)
STATIC_PATH = os.path.join(DIRNAME, 'static')
TEMPLATE_PATH = os.path.join(DIRNAME, 'templates')
UPLOADS = os.path.join(STATIC_PATH,"uploads/")
WORKERS = os.path.join(DIRNAME, 'workers')
COOKIE_SECRET = 'hClvdk4slveLtPze7p1g' #TO BE CHANGED
MAX_OBJECTS = 100 #TO BE CHANGED
DBFILE = os.path.join(STATIC_PATH,"uploads/admin/users.db")
import logging
# log linked to the standard error stream
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)-8s - %(message)s',
                    datefmt='%d/%m/%Y %Hh%Mm%Ss')
# console = logging.StreamHandler(sys.stderr)
class dbConfig(object):
    def __init__(self):
        self.host = 'leovip148.ncsa.uiuc.edu'
        self.port = '1521'
