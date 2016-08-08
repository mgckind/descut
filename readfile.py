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
import datetime
import stat
import sqlite3 as lite
import sys
import datetime as dt

def dt_t(entry):
    t = dt.datetime.strptime(entry['time'], '%a %b %d %H:%M:%S %Y')
    return t.strftime('%Y-%m-%d %H:%M:%S')


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
        stype = self.get_argument("submit_type")
        print(xs,ys,'sizes')
        print(stype,'type')
        jobid=str(uuid.uuid4())
        if stype=="manual":
            values = self.get_argument("values")
            print(values)
        if stype=="csvfile":
            fileinfo = self.request.files["csvfile"][0]
            print(fileinfo['filename'])
            fname = fileinfo['filename']
            print(fileinfo['content_type'])
            print(fileinfo['body'])
        #xtn = os.path.splitext(fname)[1]
        #cname = str(uuid.uuid4()) + extn
        con = lite.connect('test.db')
        tup = tuple(['mcarras2',jobid,'SUCCESS',dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO Jobs VALUES(?, ?, ? , ?)", tup)
        self.set_status(200)
        self.flush()
        self.finish()
