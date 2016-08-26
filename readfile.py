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
#
import easyaccess as ea
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


def sendjob(user,folder,jobid,xs,ys):
    global clients
    filename = folder+jobid+'.csv'
    df = pd.read_csv(filename,sep=',')
    ra = df.RA.values.tolist()
    dec = df.DEC.values.tolist()
    C=ea.api.DesCoaddCuts(root_url='http://desdev2.cosmology.illinois.edu')
    C.get_token()
    C.make_cuts(ra,dec,xsize=xs,ysize=ys, wait=True)
    folder2=folder+'results/'+jobid+'/'
    links = C.job.json()['links']
    for link in links:
        temp_file = os.path.join(folder2, os.path.basename(link))
        req = requests.get(link, stream=True)
        if req.status_code == 200:
            with open(temp_file, 'wb') as temp_file:
                for chunk in req:
                    temp_file.write(chunk)
    listpngs = glob.glob(folder2+'*.png')
    print(listpngs)
    titles=[]
    Ntiles=len(listpngs)
    for i in range(Ntiles):
        title=listpngs[i].split('/')[-1][:-8]
        titles.append(title)
        listpngs[i] = listpngs[i][listpngs[i].find('/static'):]
    if os.path.exists(folder2+"list.json"):
        os.remove(folder2+"list.json")
    if Ntiles > 0:
        with open(folder2+"list.json","w") as outfile:
            json.dump([dict(name=listpngs[i],title=titles[i], size=Ntiles) for i in range(Ntiles)], outfile, indent=4)
        print('json Done!')
    

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
        clients[user].write_message(u"Job done!: %s" % jid)
        self.set_status(200)
        self.flush()
        self.finish()




class FileHandler(BaseHandler):
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
        email = self.get_argument("email")
        stype = self.get_argument("submit_type")
        print('**************')
        print(xs,ys,'sizes')
        print(stype,'type')
        print(list_only,'list_only')
        print(send_email,'send_email')
        print(email,'email')
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
        folder2=user_folder+'results/'+jobid+'/'
        os.system('mkdir -p '+folder2)
        infP=infoP(loc_user,loc_passw) 
        now = datetime.datetime.now()
        tiid = loc_user+'__'+jobid+'_{'+now.ctime()+'}'
        #run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', infP, folder2, xs,ys,jobid, list_only], task_id=tiid)
        if send_email:
            run=dtasks.sendjob.apply_async(args=[loc_user, user_folder, jobid, xs,ys], task_id=tiid,  link=dtasks.send_note.si(loc_user, jobid, email))
            #run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', infP, folder2, xs,ys,jobid, list_only], task_id=tiid, link=dtasks.send_note.si(loc_user, jobid, email))
        else:
            run=dtasks.sendjob.apply_async(args=[loc_user, user_folder, jobid, xs,ys], task_id=tiid)
            #run=dtasks.desthumb.apply_async(args=[user_folder + jobid + '.csv', infP, folder2, xs,ys,jobid, list_only], task_id=tiid)
        con = lite.connect(Settings.DBFILE)
        tup = tuple([loc_user,jobid,'PENDING',now.strftime('%Y-%m-%d %H:%M:%S'),'Coadd'])
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO Jobs VALUES(?, ?, ? , ?, ?)", tup)
        self.set_status(200)
        self.flush()
        self.finish()
