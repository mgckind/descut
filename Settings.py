""" Settings for application"""
import os
DEBUG = True
DIRNAME = os.path.dirname(__file__)
STATIC_PATH = os.path.join(DIRNAME, 'static')
TEMPLATE_PATH = os.path.join(DIRNAME, 'templates')
COOKIE_SECRET = 'hClvdk4slveLtPze7p1g' #TO BE CHANGED
import logging
# log linked to the standard error stream
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)-8s - %(message)s',
                    datefmt='%d/%m/%Y %Hh%Mm%Ss')
# console = logging.StreamHandler(sys.stderr)
