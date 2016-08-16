import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import Settings
import pandas as pd
import numpy as np
import os, uuid
import json
import sqlite3 as lite
import sys
import datetime as dt
from celery.result import AsyncResult


def humantime(s):
    if s < 60:
        return "%d seconds ago" % s
    else:
        mins = s/60
        secs = s % 60
        if mins < 60:
            return "%d minutes and %d seconds ago" % (mins, secs)
        else:
            hours = mins/60
            mins  = mins % 60
            if hours < 24:
                return "%d hours and %d minutes ago" % (hours,mins)
            else:
                days = hours/24
                hours = hours % 24
                return "%d days and %d hours ago" % (days, hours)

def job_s(entry):
    return entry['job'][entry['job'].index('__')+2:entry['job'].index('_{')]

def dt_t(entry):
    t = dt.datetime.strptime(entry['time'], '%a %b %d %H:%M:%S %Y')
    return t.strftime('%Y-%m-%d %H:%M:%S')

def tup(entry,i, user):
    return (i,user,job_s(entry),entry['status'],dt_t(entry))

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("usera")

class ApiHandler(BaseHandler):

    @tornado.web.authenticated
    def delete(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        user_folder = os.path.join(Settings.UPLOADS,loc_user)
        response = { k: self.get_argument(k) for k in self.request.arguments }
        Nd=len(response)
        con = lite.connect(Settings.DBFILE)
        with con:
            cur = con.cursor()
            for j in range(Nd):
                jid=response[str(j)]
                q = "DELETE from Jobs where job = '%s' and user = '%s'" % (jid, loc_user)
                print(q)
                cc = cur.execute(q)
                folder = os.path.join(user_folder,'results/' + jid)
                os.system('rm -rf ' + folder)
                os.system('rm -f ' + os.path.join(user_folder,jid+'.csv'))
        self.set_status(200)
        self.flush()
        self.finish()

    @tornado.web.authenticated
    def get(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        response = { k: self.get_argument(k) for k in self.request.arguments }
        con = lite.connect(Settings.DBFILE)
        with con:
            cur = con.cursor()
            cc = cur.execute("SELECT * from Jobs where user = '%s' order by datetime(time) DESC " % loc_user).fetchall()
        cc = list(cc)
        jjob=[]
        jstatus=[]
        jtime=[]
        jelapsed=[]

        for i in range(len(cc)):
            dd = dt.datetime.strptime(cc[i][3],'%Y-%m-%d %H:%M:%S')
            ctime = dd.strftime('%a %b %d %H:%M:%S %Y')
            jjob.append(cc[i][0]+'__'+cc[i][1]+'_{'+ctime+'}')
            jstatus.append(cc[i][2])
            jtime.append(ctime)
            jelapsed.append(humantime((dt.datetime.now()-dd).total_seconds()))
        out_dict=[dict(job=jjob[i],status=jstatus[i], time=jtime[i], elapsed=jelapsed[i]) for i in range(len(jjob))]
        temp = json.dumps(out_dict, indent=4)
            #with open('static/jobs2.json',"w") as outfile:
        self.write(temp)
            #self.set_status(200)
            #self.flush()
            #self.finish()

class LogHandler(BaseHandler):
    @tornado.web.authenticated

    def get(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        jobid = self.get_argument("jobid")
        res = AsyncResult(jobid)
        if res is not None:
            try:
                temp = json.dumps(res.result.replace('\n','</br>'))
            except:
                temp = 'Running'
        else:
            temp = json.dumps('Running')
        self.write(temp)


