import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import pandas as pd
import os, uuid
import Settings
import time
import glob
import json
import dtasks
import datetime
import stat


class BaseHandler(tornado.web.RequestHandler): 
    def get_current_user(self):
        return self.get_secure_cookie("user")

class infoP(object):
    def __init__(self, uu, pp):
        self._uu=uu
        self._pp=pp

class FileHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        xs = self.get_argument("xsize")
        ys = self.get_argument("ysize")
        fileinfo = self.request.files["csvfile"][0]
        print(fileinfo['filename'])
        fname = fileinfo['filename']
        print(fileinfo['content_type'])
        print(fileinfo['body'])
        #xtn = os.path.splitext(fname)[1]
        #cname = str(uuid.uuid4()) + extn

        self.set_status(200)
        self.flush()
        self.finish()
