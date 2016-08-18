import subprocess
from celery import Celery
import time
import tornado.web
import tornado.websocket
import smtplib
import urllib
import glob
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import Settings
import sqlite3 as lite
#
import easyaccess as ea
import requests
import pandas as pd

celery = Celery('dtasks')
celery.config_from_object('celeryconfig')

#class CallbackTask(Task):
#    def on_success(self, retval, task_id, args, kwargs):
#        pass
#
#    def on_failure(self, exc, task_id, args, kwargs, einfo):
#        pass


testtext="""
# Will run:
# makeDESthumbs 
# --verb False
# --password antares8533
# --bands all
# --user mcarras2
# --ysize None
# --inputList /root/DES/desth/app/static/uploads/mcarras2/016fdfc0-d0b3-4b91-82f9-caf6b3bb2a0f.csv
# --prefix DES
# --tag Y1A1_COADD
# --MP True
# --xsize None
# --colorset ['i', 'r', 'g']
# --coaddtable	None
# --outdir /root/DES/desth/app/static/uploads/mcarras2/results/016fdfc0-d0b3-4b91-82f9-caf6b3bb2a0f/
# ----------------------------------------------------
# Doing: DES0144-4831 [1/2]
# -----------------------------------------------------
# ----------------------------------------------------
# Doing: DES0002+0001 [2/2]
# -----------------------------------------------------

*** Grand Total time:0m 3.31s ***
"""


@celery.task
def desthumb(inputs, infoP, outputs,xs,ys, siid, listonly):
    com =  "makeDESthumbs  %s --user %s --password %s --MP --outdir=%s" % (inputs, infoP._uu, infoP._pp, outputs)
    if xs != "": com += ' --xsize %s ' % xs
    if ys != "": com += ' --ysize %s ' % ys
    oo = subprocess.check_output([com],shell=True)
    mypath = Settings.UPLOADS+infoP._uu+'/results/'+siid+'/'
    user_folder = Settings.UPLOADS+infoP._uu+"/"

    if listonly:
        if os.path.exists(mypath+"list.json"): os.remove(mypath+"list.json")
        with open(mypath+"list.json","w") as outfile:
            json.dump('', outfile, indent=4)
    else:
        tiffiles=glob.glob(mypath+'*.tif')
        titles=[]
        pngfiles=[]
        Ntiles = len(tiffiles)
        for f in tiffiles:
            title=f.split('/')[-1][:-4]
            os.system("convert %s %s.png" % (f,f))
            titles.append(title)
            pngfiles.append(mypath+title+'.tif.png')
        
        for ij in range(Ntiles):
            pngfiles[ij] = pngfiles[ij][pngfiles[ij].find('/static'):]       
        os.chdir(user_folder)
        os.system("tar -zcf results/"+siid+"/all.tar.gz results/"+siid+"/") 
        os.chdir(os.path.dirname(__file__))
        if os.path.exists(mypath+"list.json"): os.remove(mypath+"list.json")
        with open(mypath+"list.json","w") as outfile:
            json.dump([dict(name=pngfiles[i],title=titles[i], size=Ntiles) for i in range(len(pngfiles))], outfile, indent=4)


    # writing files for wget
    allfiles = glob.glob(mypath+'*.*')
    Fall = open(mypath+'list_all.txt','w')
    prefix='http://desdev2.cosmology.illinois.edu/static'
    for ff in allfiles:
        if (ff.find('all.tar.gz')==-1 & ff.find('list.json')==-1): Fall.write(prefix+ff.split('static')[-1]+'\n')
    Fall.close()
    con = lite.connect(Settings.DBFILE)
    q="UPDATE Jobs SET status='SUCCESS' where job = '%s'" % siid
    with con:
        cur = con.cursor()
        cur.execute(q)
    #clients[infoP._uu].write_message(u"Job done!:" + siid)
    return oo

@celery.task
def send_note(user, jobid, toemail):
    print('Task was completed')
    print('I will notify %s to its email address :  %s' % (user, toemail))
    fromemail = 'devnull@ncsa.illinois.edu'
    s = smtplib.SMTP('smtp.ncsa.illinois.edu')
    link = "http://desdev2.cosmology.illinois.edu/results/%s" % jobid
    #link2 = urllib.quote(link.encode('utf8'),safe="%/:=&?~#+!$,;'@()*[]")
    #jobid2=jobid[jobid.find('__')+2:jobid.find('{')-1]



    html = """\
    <html>
    <head></head>
    <body>
         <b> Please do not reply to this email</b> <br><br>
        <p>The job %s was completed, <br> 
        the results can be retrieved from this <a href="%s">link</a> .
        </p><br>
        <p> DESDM Thumbs generator</p><br>
        <p> PS: This is the full link to the results: <br>
        %s </p>
    </body>
    </html>
    """ % (jobid, link, link)


    MP1 = MIMEText(html, 'html')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Job %s is completed' % jobid
    #msg['From'] = fromemail
    msg['From'] = formataddr((str(Header('DESDM Thumbs', 'utf-8')), fromemail))
    msg['To'] = toemail

    msg.attach(MP1)


    s.sendmail(fromemail, toemail, msg.as_string())
    s.quit()
    return "Email Sent to %s" % toemail


@celery.task
def sendjob(user,folder,jobid,xs,ys):
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
    #clients[user].write_message(u"Job done!:" + jobid)
    print('Done!')
    return jobid + '\n' + testtext
