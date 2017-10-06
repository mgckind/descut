import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
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
import dtasks
import MySQLdb as mydb
#import config.mysqlconfig as ms
import yaml
#
#import easyaccess as ea
from multiprocessing import Pool
import requests

clients={}

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        clients[loc_user]=self
        print('%s connected' % loc_user)

    def on_message(self, message):
        pass
        #self.write_message(u"Your message was: " + message)

    def on_close(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        print('%s disconnected' % loc_user)


def notify(user,jobid):
    global clients
    clients[user].write_message(u"Job done!:" + jobid)



    con = lite.connect(Settings.DBFILE)
    q="UPDATE Jobs SET status='SUCCESS' where job = '%s'" % jobid
    print(q)
    with con:
        cur = con.cursor()
        cur.execute(q)
    clients[user].write_message(u"Job done!:" + jobid)
    print('Done!')



def dt_t(entry):
    t = dt.datetime.strptime(entry['time'], '%a %b %d %H:%M:%S %Y')
    return t.strftime('%Y-%m-%d %H:%M:%S')


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("usera")

class infoP(object):
    def __init__(self, uu, pp):
        self._uu=uu
        self._pp=pp

class RefreshHandler(BaseHandler):
    def get(self):
        global clients
        user = self.get_argument("user")
        jid = self.get_argument("jid")
        print('Refresh!')
        message = {'user': user, 'jid' : jid, 'type': 'refresh'}
        clients[user].write_message(json.dumps(message))
        self.set_status(200)
        self.flush()
        self.finish()



class FileHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def post(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        loc_passw = self.get_secure_cookie("userb").decode('ascii').replace('\"','')
        user_folder = os.path.join(Settings.WORKDIR,loc_user)+'/'
        xs = float(self.get_argument("xsize"))
        ys = float(self.get_argument("ysize"))
        list_only = self.get_argument("list_only") == 'true'
        send_email = self.get_argument("send_email") == 'true'
        email = self.get_argument("email")
        stype = self.get_argument("submit_type")
        tag = self.get_argument("tag")
        # comment = self.get_argument("comment")
        print('**************')
        print(xs,ys,'sizes')
        print(stype,'type')
        print(list_only,'list_only')
        print(send_email,'send_email')
        print(email,'email')
        print(tag,'Tag')
        # print(comment,'comment')
        jobid = str(uuid.uuid4())
        if xs == 0.0 : xs=''
        if ys == 0.0 : ys=''
        if stype=="manual":
            values = self.get_argument("values")
            print(values)
            filename = user_folder+jobid+'.csv'
            F=open(filename,'w')
            F.write("RA,DEC\n")
            F.write(values)
            F.close()
        if stype=="csvfile":
            fileinfo = self.request.files["csvfile"][0]
            fname = fileinfo['filename']
            extn = os.path.splitext(fname)[1]
            print(fname)
            print(fileinfo['content_type'])
            filename = user_folder+jobid+extn
            with open(filename,'w') as F:
                F.write(fileinfo['body'].decode('ascii'))
        print('**************')
        folder2=user_folder+'results/'+jobid+'/'
        os.system('mkdir -p '+folder2)
        infP=infoP(loc_user,loc_passw)
        now = datetime.datetime.now()
        tiid = loc_user+'__'+jobid+'_{'+now.ctime()+'}'
        #run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', infP, folder2, xs,ys,jobid, list_only], task_id=tiid)
        if send_email:
            run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', loc_user, loc_passw,folder2, xs,ys,jobid, list_only, tag], task_id=tiid, link=dtasks.send_note.si(loc_user, jobid, email))
        else:
            run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', loc_user, loc_passw, folder2, xs,ys,jobid, list_only, tag], task_id=tiid)
        # con = lite.connect(Settings.DBFILE)

        with open('config/mysqlconfig.yaml', 'r') as cfile:
            conf = yaml.load(cfile)['mysql']
        con = mydb.connect(**conf)

        tup = tuple([loc_user,jobid,'PENDING',now.strftime('%Y-%m-%d %H:%M:%S'),'DES', '', '', ''])
        with con:
            cur = con.cursor()

            cur.execute("INSERT INTO Jobs VALUES(?, ?, ?, ?, ?, ?, ?, ?)", tup)
        self.set_status(200)
        self.flush()
        self.finish()

class FileHandlerS(BaseHandler):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def post(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        loc_passw = self.get_secure_cookie("userb").decode('ascii').replace('\"','')
        user_folder = os.path.join(Settings.UPLOADS,loc_user)+'/'
        xs = float(self.get_argument("xsize"))
        ys = float(self.get_argument("ysize"))
        list_only = self.get_argument("list_only") == 'true'
        send_email = self.get_argument("send_email") == 'true'
        noBlacklist = self.get_argument('noBlacklist') == 'true'
        bands = self.get_argument('bands')
        email = self.get_argument("email")
        # comment = self.get_argument("comment")
        stype = self.get_argument("submit_type")
        if xs == 0.0 : xs=''
        if ys == 0.0 : ys=''
        print('**************')
        print(xs,ys,'sizes')
        print(stype,'type')
        print(list_only,'list_only')
        print(send_email,'send_email')
        print(email,'email')
        # print(comment,'comment')
        print(bands, 'bands')
        print(noBlacklist, 'noBlacklist')
        jobid = str(uuid.uuid4())
        if stype=="manual":
            values = self.get_argument("values")
            print(values)
            filename = user_folder+jobid+'.csv'
            F=open(filename,'w')
            F.write("RA,DEC\n")
            F.write(values)
            F.close()
        if stype=="csvfile":
            fileinfo = self.request.files["csvfile"][0]
            fname = fileinfo['filename']
            extn = os.path.splitext(fname)[1]
            print(fname)
            print(fileinfo['content_type'])
            filename = user_folder+jobid+extn
            with open(filename,'w') as F:
                F.write(fileinfo['body'].decode('ascii'))
        print('**************')
        job_dir=user_folder+'results/'+jobid+'/'
        os.system('mkdir -p '+job_dir)
        infP=infoP(loc_user,loc_passw)
        now = datetime.datetime.now()
        tiid = loc_user+'__'+jobid+'_{'+now.strftime('%a %b %d %H:%M:%S %Y')+'}'

        if send_email:
            print('Sending email to %s' % email)
            run=dtasks.mkcut.apply_async(args=[filename, loc_user, loc_passw, job_dir, xs, ys, bands, jobid, noBlacklist, tiid, list_only], \
                task_id=tiid, link=dtasks.send_note.si(loc_user, tiid, toemail))
        else:
            print('Not sending email')
            run=dtasks.mkcut.apply_async(args=[filename, loc_user, loc_passw, job_dir, xs, ys, bands, jobid, noBlacklist, tiid, list_only], \
                task_id=tiid)
        con = lite.connect(Settings.DBFILE)
        tup = tuple([loc_user,jobid,'PENDING',now.strftime('%Y-%m-%d %H:%M:%S'),'DES','', '', ''])
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO Jobs VALUES(?, ?, ? ,?, ?, ?, ?, ?)", tup)
        self.set_status(200)
        self.flush()
        self.finish()
