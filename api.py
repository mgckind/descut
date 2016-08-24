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
from celery.task.control import revoke
from expiringdict import ExpiringDict
import binascii
import hashlib
import cx_Oracle



dbConfig0 = Settings.dbConfig()
tokens = ExpiringDict(max_len=300, max_age_seconds=Settings.TOKEN_TTL)


def humantime(s):
    if s < 60:
        return "%d seconds" % s
    else:
        mins = s/60
        secs = s % 60
        if mins < 60:
            return "%d minutes and %d seconds" % (mins, secs)
        else:
            hours = mins/60
            mins  = mins % 60
            if hours < 24:
                return "%d hours and %d minutes" % (hours,mins)
            else:
                days = hours/24
                hours = hours % 24
                return "%d days and %d hours" % (days, hours)

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



class infoP(object):
    def __init__(self, uu, pp):
        self._uu=uu
        self._pp=pp

def check_permission(password, username, database='desoper'):
    kwargs = {'host': dbConfig0.host, 'port': dbConfig0.port, 'service_name': database}
    dsn = cx_Oracle.makedsn(**kwargs)
    try:
        dbh = cx_Oracle.connect(username, password, dsn=dsn)
        dbh.close()
        return True,""
    except Exception as e:
        error = str(e).strip()
        return False,error


class TokenHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        response = { k: self.get_argument(k) for k in self.request.arguments }
        response2 = {'status':'error', 'message':''}
        response3={}
        for k in response.keys():
            response2[k.lower()]=response[k]
        if 'token' in response2:
            ttl = tokens.ttl(response2['token'])
            if ttl is None:
                response2['status']='error'
                response2['message']='Token does not exist or it expired'
                print('sssss')
                self.set_status(404)
            else:
                response2['status'] = 'ok'
                response2['message'] = 'Token is valid for %s' % humantime(round(ttl))
                self.set_status(200)
            self.write(response2)
            self.flush()
            self.finish()
            return
                
        if 'username' in response2:
            if 'password' not in response2:
                response2['message'] = 'Need password'
            else:
                user = response2['username']
                passwd = response2['password']
                check,msg = check_permission(passwd, user)
                if check:
                    response2['status']='ok'
                    newfolder = os.path.join(Settings.UPLOADS,user)
                    user_folder = newfolder + '/'
                    if not os.path.exists(newfolder):
                        os.mkdir(newfolder)
                else:
                    response2['message']=msg
        else:
            response2['message'] = 'Need username'
        
        if response2['status'] == 'ok':
            response2['message'] = 'Token created, expiration time: %s' % humantime(Settings.TOKEN_TTL)
            #temp = binascii.hexlify(os.urandom(64))
            temp = hashlib.sha1(os.urandom(64)).hexdigest()
            tokens[temp] = [user,passwd]
            response3['token']=temp 
        response3['status']=response2['status']
        response3['message']=response2['message']
        self.write(response3)
        self.set_status(200)
        self.flush()
        self.finish()
       







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
        jtype=[]

        for i in range(len(cc)):
            dd = dt.datetime.strptime(cc[i][3],'%Y-%m-%d %H:%M:%S')
            ctime = dd.strftime('%a %b %d %H:%M:%S %Y')
            jjob.append(cc[i][0]+'__'+cc[i][1]+'_{'+ctime+'}')
            jstatus.append(cc[i][2])
            jtime.append(ctime)
            jtype.append(cc[i][4])
            jelapsed.append(humantime((dt.datetime.now()-dd).total_seconds())+" ago")
        out_dict=[dict(job=jjob[i],status=jstatus[i], time=jtime[i], elapsed=jelapsed[i], jtypes=jtype[i]) for i in range(len(jjob))]
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

class CancelJobHandler(BaseHandler):

    @tornado.web.authenticated
    def delete(self):
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        jobid = self.get_argument("jobid")
        jobid2=jobid[jobid.find('__')+2:jobid.find('{')-1]
        revoke(jobid, terminate=True)
        con = lite.connect(Settings.DBFILE)
        with con:
            cur = con.cursor()
            q = "UPDATE Jobs SET status='REVOKED' where job = '%s'" % jobid2
            cc = cur.execute(q)
        self.set_status(200)
        self.flush()
        self.finish()
