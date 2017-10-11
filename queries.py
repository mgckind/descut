import tornado.web
import pusher
import json
import ea_tasks
import uuid
import os
import sqlite3 as lite
import Settings
import base64
from Crypto.Cipher import AES
import datetime
import requests
import MySQLdb as mydb
#import config.mysqlconfig as ms
import yaml

def after_return(retval):
    url = 'http://localhost:8999/pusher/pusher/'
    data = {'username': retval['user'], 'result': retval['data'], 'status': retval['status']}
    requests.post(url, data=data)
    return


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("usera")

class QueryHandler(BaseHandler):
    """Main query handler."""
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self):
        """Post function."""
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"', '')
        loc_passw = self.get_secure_cookie("userb").decode('ascii').replace('\"', '')
        db = self.get_secure_cookie("userdb").decode('ascii').replace('\"', '')
        cipher = AES.new(Settings.SKEY, AES.MODE_ECB)
        lp = base64.b64encode(cipher.encrypt(loc_passw.rjust(32)))
        response = {'status': 'error'}
        response['user'] = loc_user
        response['elapsed'] = 0
        user_folder = os.path.join(Settings.WORKDIR, loc_user)+'/'
        jobid = str(uuid.uuid4())
        response['jobid'] = jobid
        jsonfile = os.path.join(user_folder, jobid+'.json')
        # Get Arguments
        query = self.get_argument("query", "")
        original_query = query
        query_kind = self.get_argument("querykind", "")
        filename = self.get_argument("filename", "")
        if query == "":
            print('No query string')
            return
        query = query.replace(';', '')
        lines = query.split('\n')
        newquery = ''
        for line in lines:
            line = line.lstrip()
            if line.startswith('--'):
                continue
            newquery += ' ' + line.split('--')[0]
        query = newquery
        print(query)
        print('*******')
        print("query kind: ", query_kind)
        file_error = False
        if filename == "nofile":
            filename = None
        elif filename == "":
            file_error = True
        elif not filename.endswith('.csv') and not filename.endswith('.fits'):
            file_error = True
        print("filename: ", filename)
        if file_error:
            response['data'] = 'ERROR: File format allowed : .csv and .fits'
            response['kind'] = 'query'
            with open(jsonfile, 'w') as fp:
                json.dump(response, fp)
            self.flush()
            self.write(response)
            self.finish()
            return
        if query_kind == "submit":
            now = datetime.datetime.now()
            with open('config/mysqlconfig.yaml', 'r') as cfile:
                conf = yaml.load(cfile)['mysql']
            con = mydb.connect(**conf)
            #con = mydb.connect(host=ms.host, port=ms.port, user=ms.user, passwd=ms.passwd, db=ms.db)
            #con = lite.connect(Settings.DBFILE)
            tup = tuple([loc_user, jobid, 'PENDING', now.strftime('%Y-%m-%d %H:%M:%S'), 'EASY',
                         original_query, '', ''])

            print("==> tup: ", tup)
            cur = con.cursor()
            try:
                cur.execute("SELECT * from Jobs where user = '%s' order "
                                 "by time DESC limit 1" % loc_user)
                cc = cur.fetchone()
                #last = datetime.datetime.strptime(cc[3], '%Y-%m-%d %H:%M:%S')
                last = cc[3]
            except:
                last = now - datetime.timedelta(seconds=60)
            if (now-last).total_seconds() < 30:
                print(cc[4] == query)
                print(cc[4], query)
                response['data'] = 'ERROR: You submitted the same query less than 30s ago'
                response['kind'] = 'query'
                self.flush()
                self.write(response)
                self.finish()
                return

            # cur.execute("INSERT INTO Jobs VALUES(?, ?, ?, ?, ?, ?, ?, ?)", tup)
            cur.execute("INSERT INTO Jobs VALUES{0}".format(tup))

            cur.execute("SELECT * from Jobs where user = '{0}'".format(loc_user))
            cc = cur.fetchall()
            # print("==> ", list(cc))
            con.commit()
            try:
                run = ea_tasks.run_query.apply_async(args=[query, filename, db,
                                                     loc_user, lp.decode(), jobid], task_id=jobid)
            except:
                pass
            response['data'] = 'Job {0} submitted'.format(jobid)
            response['status'] = 'ok'
            response['kind'] = 'query'
            pusher.SendMessage('refreshJobs')
            con.close()
            with open(jsonfile, 'w') as fp:
                json.dump(response, fp)
        elif query_kind == "quick":
            run = ea_tasks.run_query(query, filename, db, loc_user, lp.decode(), jobid, timeout=20)
            response = run
        else:
            return
        self.flush()
        self.write(response)
        self.finish()
