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
import dtasks
import datetime
import requests
import readfile



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
        arguments = { k.lower(): self.get_argument(k) for k in self.request.arguments }
        response = {'status' : 'error'}
        if 'token' in arguments:
            ttl = tokens.ttl(arguments['token'])
            if ttl is None:
                response['message'] = 'Token does not exist or it expired'
                self.set_status(404)
            else:
                response['status'] = 'ok'
                response['message'] = 'Token is valid for %s' % humantime(round(ttl))
                self.set_status(200)
        else:
            response['message'] = 'no token argument found!'
            self.set_status(400)
        self.write(response)
        self.flush()
        self.finish()
    
    @tornado.web.asynchronous
    def post(self):
        arguments = { k.lower(): self.get_argument(k) for k in self.request.arguments}
        response = {'status' : 'error'}
        if 'username' in arguments:
            if 'password' not in arguments:
                response['message'] = 'Need password'
                self.set_status(400)
            else:
                user = arguments['username']
                passwd = arguments['password']
                check,msg = check_permission(passwd, user)
                if check:
                    response['status'] = 'ok'
                    newfolder = os.path.join(Settings.UPLOADS,user)
                    if not os.path.exists(newfolder):
                        os.mkdir(newfolder)
                else:
                    self.set_status(403)
                    response['message'] = msg
        else:
            response['message'] = 'Need username'
            self.set_status(400)
        
        if response['status'] == 'ok':
            response['message'] = 'Token created, expiration time: %s' % humantime(Settings.TOKEN_TTL)
            #temp = binascii.hexlify(os.urandom(64))
            temp = hashlib.sha1(os.urandom(64)).hexdigest()
            tokens[temp] = [user,passwd]
            response['token'] = temp 
            self.set_status(200)
        self.write(response)
        self.flush()
        self.finish()
       


class JobHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        arguments = { k.lower(): self.get_argument(k) for k in self.request.arguments }
        response = {'status' : 'error'}
        if 'token' in arguments:
            auths = tokens.get(arguments['token'])
            if auths is None:
                response['message'] = 'Token does not exist or it expired. Please create a new one'
                self.set_status(403)
            else:
                user = auths[0]
                passwd = auths[1]
                response['status'] = 'ok'
                user_folder = os.path.join(Settings.UPLOADS,user) + '/'
        else:
            self.set_status(400)
            response['message'] = 'Need a token to generate a request'

        if response['status'] == 'ok':
            try:
                ra = [float(i) for i in arguments['ra'].replace('[','').replace(']','').split(',')]
                dec = [float(i) for i in arguments['dec'].replace('[','').replace(']','').split(',')]
                stype = "manual"
                if len(ra) != len(dec):
                    self.set_status(400)
                    response['status']='error'
                    response['message'] = 'RA and DEC arrays must have same dimensions'
            except:
                self.set_status(400)
                response['status']='error'
                response['message'] = 'RA and DEC arrays must have same dimensions'

        if response['status'] == 'ok':
            try:
                jtype = arguments['job_type'].lower()
                if jtype not in ('coadd','single'): raise
            except:
                self.set_status(400)
                response['status']='error'
                response['message'] = "Need to specify job_type, either 'coadd' or 'single'"

        if response['status'] == 'ok':
            try:
                fileinfo = self.request.files["csvfile"][0]
                stype = 'csvfile'
            except:
                pass
        
        if response['status'] == 'ok':
            xs = np.ones(len(ra))
            ys = np.ones(len(ra))
            if 'xsize' in arguments:
                xs_read = [float(i) for i in arguments['xsize'].replace('[','').replace(']','').split(',')]
                if len(xs_read) == 1 : xs=xs*xs_read
                if len(xs) >= len(xs_read): xs[0:len(xs_read)] = xs_read
                else: xs = xs_read[0:len(xs)]
            if 'ysize' in arguments:
                ys_read = [float(i) for i in arguments['ysize'].replace('[','').replace(']','').split(',')]
                if len(ys_read) == 1 : ys=ys*ys_read
                if len(ys) >= len(ys_read): ys[0:len(ys_read)] = ys_read
                else: xy = xy_read[0:len(xy)]

            if 'list_only' in arguments:
                list_only = arguments["list_only"] == 'true'
            if 'email' in arguments:
                send_email = True
                email = arguments['email']
            else:
                send_email = False
            jobid = str(uuid.uuid4())
            if stype=="manual":
                filename = user_folder + jobid + '.csv'
                df = pd.DataFrame(np.array([ra,dec,xs,ys]).T,columns=['RA','DEC','XSIZE','YSIZE'])
                df.to_csv(filename,sep=',',index=False)
                del df
            if stype=="csvfile":
                fname = fileinfo['filename']
                extn = os.path.splitext(fname)[1]
                filename = user_folder+jobid+extn
                with open(filename,'w') as F:
                    F.write(fileinfo['body'].decode('ascii'))
            folder2 = user_folder+'results/'+jobid+'/'
            os.system('mkdir -p '+folder2)
            infP = infoP(user,passwd) 
            now = datetime.datetime.now()
            tiid = user+'__'+jobid+'_{'+now.ctime()+'}'
            #SUBMIT JOB, ADD TO SQLITE
            if send_email:
                xs=1.0
                ys=1.0
                run=dtasks.sendjob.apply_async(args=[user, user_folder, jobid, xs,ys], task_id=tiid,  link=dtasks.send_note.si(user, jobid, email))
                #run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', infP, folder2, xs,ys,jobid, list_only], task_id=tiid, link=dtasks.send_note.si(loc_user, jobid, email))
            else:
                xs=1.0
                ys=1.0
                run=dtasks.sendjob.apply_async(args=[user, user_folder, jobid, xs,ys], task_id=tiid)
                #run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', infP, folder2, xs,ys,jobid, list_only], task_id=tiid)
            con = lite.connect(Settings.DBFILE)
            tup = tuple([user,jobid,'PENDING',now.strftime('%Y-%m-%d %H:%M:%S'),'Coadd'])
            with con:
                cur = con.cursor()
                cur.execute("INSERT INTO Jobs VALUES(?, ?, ? , ?, ?)", tup)
            response['message'] = 'Job %s submitted.' % (jobid)
            response['job'] = jobid
            readfile.notify(user,jobid)
            self.set_status(200)
        
        self.write(response)
        self.flush()
        self.finish()


    @tornado.web.asynchronous
    def get(self):
        arguments = { k.lower(): self.get_argument(k) for k in self.request.arguments }
        response = {'status' : 'error'}
        if 'token' in arguments:
            auths = tokens.get(arguments['token'])
            if auths is None:
                response['message'] = 'Token does not exist or it expired. Please create a new one'
                self.set_status(403)
            else:
                user = auths[0]
                passwd = auths[1]
                response['status'] = 'ok'
                user_folder = os.path.join(Settings.UPLOADS,user) + '/'
        else:
            self.set_status(400)
            response['message'] = 'Need a token to generate a request'

        if response['status'] == 'ok':
            if 'list_jobs' in arguments:
                con = lite.connect(Settings.DBFILE)
                with con:
                    cur = con.cursor()
                    cc = cur.execute("SELECT job from Jobs where user = '%s' order by datetime(time) DESC  " % user).fetchall()
                response['message'] = 'List of jobs returned'
                response['list_jobs'] = [j[0] for j in cc]
                self.set_status(200)
                self.write(response)
                self.flush()
                self.finish()




        if response['status'] == 'ok':
            if 'jobid' in arguments:
                jobid = arguments['jobid']
            else:
                response['status'] = 'error'
                self.set_status(400)
                response['message'] = 'No jobid argument in request'

        if response['status'] == 'ok':
            con = lite.connect(Settings.DBFILE)
            with con:
                cur = con.cursor()
                cc = cur.execute("SELECT status from Jobs where user = '%s' and job = '%s'" % (user, jobid)).fetchall()
            try:
                status = cc[0][0]
                response['message'] = 'Job %s is %s' % (jobid, status)
                response['job_status'] = status
                if status  == 'SUCCESS':
                    list_file = user_folder + 'results/'+jobid+'/list_all.txt'
                    with open(list_file) as f:
                        links = f.read().splitlines()
                    response['links'] = links
                self.set_status(200)
            except:
                response['status'] = 'error'
                self.set_status(400)
                respose['message'] = 'Job Id does not exists'
        self.write(response)
        self.flush()
        self.finish()


    @tornado.web.asynchronous
    def delete(self):
        arguments = { k.lower(): self.get_argument(k) for k in self.request.arguments }
        response = {'status' : 'error'}
        if 'token' in arguments:
            auths = tokens.get(arguments['token'])
            if auths is None:
                response['message'] = 'Token does not exist or it expired. Please create a new one'
                self.set_status(403)
            else:
                user = auths[0]
                passwd = auths[1]
                response['status'] = 'ok'
                user_folder = os.path.join(Settings.UPLOADS,user) + '/'
        else:
            response['status'] = 'error'
            self.set_status(400)
            response['message'] = 'Need a token to generate a request'

        if response['status'] == 'ok':
            if 'jobid' in arguments:
                jobid = arguments['jobid']
            else:
                self.set_status(400)
                response['message'] = 'No jobid argument in request'

        if response['status'] == 'ok':
            con = lite.connect(Settings.DBFILE)
            with con:
                cur = con.cursor()
                cc = cur.execute("SELECT status from Jobs where user = '%s' and job = '%s'" % (user, jobid)).fetchall()
            try:
                status = cc[0][0]
                with con:
                    cur = con.cursor()
                    cc = cur.execute("DELETE from Jobs where user = '%s' and job = '%s'" % (user, jobid))
                response['message'] = 'Job %s was deleted' % (jobid)
                folder = os.path.join(user_folder,'results/' + jobid)
                os.system('rm -rf ' + folder)
                os.system('rm -f ' + os.path.join(user_folder,jobid+'.csv'))
                self.set_status(200)
                readfile.notify(user,jobid)
            except:
                response['status'] = 'error'
                self.set_status(400)
                response['message'] = 'Job Id does not exists'
        
        self.write(response)
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
