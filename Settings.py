""" Settings for application"""
import os
import random
import string
import logging

DEBUG = True
DIRNAME = os.path.dirname(__file__)
STATIC_PATH = os.path.join(DIRNAME, 'static')
TEMPLATE_PATH = os.path.join(DIRNAME, 'templates')
UPLOADS = os.path.join(STATIC_PATH,"workdir/")

# TODO: DO WE NEED TO CHANGE WORKER IN THIS CASE?
WORKERS = os.path.join(DIRNAME, 'workdir/')
# FF=open('ranC.tck','r')
# COOKIE_SECRET = SKEY = FF.readlines()[0]
# FF.close()
MAX_OBJECTS = 100 #TO BE CHANGED
TOKEN_TTL = 3600
# DBFILE = os.path.join(STATIC_PATH,"uploads/admin/users.db")
ROOT_URL = 'http://descut.cosmology.illinois.edu'
import logging
# log linked to the standard error stream
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)-8s - %(message)s',
                    datefmt='%d/%m/%Y %Hh%Mm%Ss')
# console = logging.StreamHandler(sys.stderr)
class dbConfig(object):
    def __init__(self):
        self.host = 'desdb.ncsa.illinois.edu'
        self.port = '1521'


LOG_PATH = os.path.join(DIRNAME, 'logs')
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
WORKDIR = os.path.join(STATIC_PATH, "workdir/")
DBFILE = os.path.join(STATIC_PATH, "workdir/admin/users.db")
DBFILE2 = os.path.join(STATIC_PATH, "workdir/admin/users.sql")
LOGFILE = os.path.join(LOG_PATH, "access.log")
LOG_GENERALFILE = os.path.join(LOG_PATH, "general.log")
LOG_APPFILE = os.path.join(LOG_PATH, "app.log")
# TODO: read from file since there will be a race conition between pods
with open('config/ranC.tk', 'r') as fi:
    COOKIE_SECRET = fi.readline().strip()
    SKEY = fi.readline().strip()

access_log = logging.getLogger('tornado.access')
# app_log = logging.getLogger('tornado.application')
access_log.setLevel(logging.DEBUG)
# general_log.setLevel(logging.DEBUG)
# app_log.setLevel(logging.DEBUG)
handler_access = logging.FileHandler(LOGFILE)
# handler_general = logging.FileHandler(LOG_GENERALFILE)
# handler_app = logging.FileHandler(LOG_APPFILE)
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)-8s - %(message)s',
                              datefmt='%d/%m/%Y %Hh%Mm%Ss')
# handler_general.setFormatter(formatter)
handler_access.setFormatter(formatter)
# handler_app.setFormatter(formatter)
access_log.addHandler(handler_access)
