import subprocess
from celery import Celery
from celery import Task
import time
import tornado.web
import tornado.websocket
import smtplib
import urllib
import glob
import os, io
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import Settings
import sqlite3 as lite
#
#import easyaccess as ea
import requests
import pandas as pd
import readfile
import api
from cutout_cmd import mongo_util as mu

celery = Celery('dtasks')
celery.config_from_object('celeryconfig')



@celery.task
def desthumb(inputs, infoP, outputs,xs,ys, siid, listonly):
    com =  "makeDESthumbs  %s --user %s --password %s --MP --outdir=%s" % (inputs, infoP._uu, infoP._pp, outputs)
    if xs != "": com += ' --xsize %s ' % xs
    if ys != "": com += ' --ysize %s ' % ys
    com += " --logfile %s" % (outputs + 'log.log')
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
        os.system("tar -zcf results/"+siid+"/"+siid+".tar.gz results/"+siid+"/") 
        os.chdir(os.path.dirname(__file__))
        if os.path.exists(mypath+"list.json"): os.remove(mypath+"list.json")
        with open(mypath+"list.json","w") as outfile:
            json.dump([dict(name=pngfiles[i],title=titles[i], size=Ntiles) for i in range(len(pngfiles))], outfile, indent=4)

    # writing files for wget
    allfiles = glob.glob(mypath+'*.*')
    Fall = open(mypath+'list_all.txt','w')
    prefix=Settings.ROOT_URL+'/static'
    for ff in allfiles:
        if (ff.find(siid+'.tar.gz')==-1 & ff.find('list.json')==-1): Fall.write(prefix+ff.split('static')[-1]+'\n')
    Fall.close()
    con = lite.connect(Settings.DBFILE)
    q="UPDATE Jobs SET status='SUCCESS' where job = '%s'" % siid
    with con:
        cur = con.cursor()
        cur.execute(q)
    try:
        a=requests.get(Settings.ROOT_URL+'/api/refresh/?user=%s&jid=%s' % (infoP._uu,siid))
        #readfile.notify(infoP._uu,siid)
    except:
        pass
    return oo.decode('ascii')

@celery.task
def mkcut(filename, infoP, outdir, xs, ys, bands, jobid, noBlacklist, tiid, listOnly):
    #different dir path
    loc_user = infoP._uu
    loc_passw = infoP._pp
    user_folder = Settings.UPLOADS+loc_user+"/"  
    outdir =  os.path.join(user_folder+'results', jobid)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if bands == "all":
        bands = "g r i z Y"
    else:
        bands = bands.replace(',', ' ')
    
    cmd = script_dir+"/cutout_cmd/mkdescut.py {} --username {} --password {} " \
      "--bands {} --outdir {} --listOnly {} --noBlacklist {}".format(filename, loc_user, loc_passw, \
        bands, outdir, listOnly, noBlacklist)
    if xs != "": cmd += ' --xsize %s ' % xs
    if ys != "": cmd += ' --ysize %s ' % ys
    
    oo = subprocess.check_call(cmd, shell=True)
    
    #generate archives for each job
    job_tar = jobid+'.tar.gz'
    os.chdir(user_folder+'results/')
    try:
        subprocess.check_call("tar -zcf {} {}".format(os.path.join(outdir,job_tar), jobid+'/'),shell=True)
    except:
        print ('not making the tars')
    
    #create all file list
    prefix = Settings.ROOT_URL+'/static/uploads/'+loc_user+'/results/'+jobid+'/'
    os.chdir(outdir)
    all_files = glob.glob('thumbs*/DESJ*')
    
    with open('list_all.txt', 'w') as list_output:
        for file in all_files:
            list_output.write(prefix+file+'\n')
    
    os.chdir(script_dir)
    
    # update job status in sqlite 
    conS = lite.connect(Settings.DBFILE)
    qS="UPDATE Jobs SET status='SUCCESS' where job = '%s'" % jobid
    with conS:
        curS = conS.cursor()
        curS.execute(qS)
    # a=requests.get('http://descut.cosmology.illinois.edu:8888/api/refresh/?user=%s&jid=%s' % (infoP._uu,siid))
    # a=requests.get('http://localhost:8888/api/refresh?user=%s&jid=%s' % (infoP._uu,jobid))
    
    # call error taks if error.log is not zero byte
    err_file = outdir+'/error.log'
    try: 
        if os.path.getsize(err_file) > 0:
            print ('init error task')
            celery.send_task('dtasks.error', [err_file])
    except:
        pass
    
    try:
        a=requests.get(Settings.ROOT_URL+'/api/refresh/?user=%s&jid=%s' % (loc_user,jobid))
    except:
        pass
    return oo
        
@celery.task
def send_note(user, jobid, toemail):
    print('Task was completed')
    print('I will notify %s to its email address :  %s' % (user, toemail))
    fromemail = 'devnull@ncsa.illinois.edu'
    s = smtplib.SMTP('smtp.ncsa.illinois.edu')
    link = Settings.ROOT_URL 
    #link2 = urllib.quote(link.encode('utf8'),safe="%/:=&?~#+!$,;'@()*[]")
    #jobid2=jobid[jobid.find('__')+2:jobid.find('{')-1]



    html = """\
    <html>
    <head></head>
    <body>
         <b> Please do not reply to this email</b> <br><br>
        <p>The job %s was completed, <br> 
        the results can be retrieved from this <a href="%s">link</a> under My Jobs Tab.
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
def getList(df_pos, options, bands, noBlacklist):

    frames = []
    mu.select_collection(noBlacklist)
    final_out = io.StringIO()

    if bands == "all":
        bands = ['g', 'r', 'i', 'z', 'Y']
    else:
        bands = bands.split(',')

    for i in range(len(df_pos)):
        frame = mu.query_to_pandas(df_pos['RA'][i],df_pos['DEC'][i], bands)
        frames.append(frame)
    
    df_result = pd.concat(frames)

    #check for options
    if 'ccdnum' in options:
        ccdnum = options['ccdnum']
        df_result = df_result[df_result['CCDNUM'].isin(ccdnum)]

    if 'expnum' in options:
            expnum = options['expnum']
            df_result = df_result[df_result['EXPNUM'].isin(expnum)]

    if 'nite' in options:
        nite = options['nite']
        df_result = df_result[df_result['NITE'].isin(nite)]
    
    df_result.to_json(final_out, orient='records')
    return_value = final_out.getvalue()
    final_out.close()

    return return_value

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
    
    allfiles = glob.glob(folder2+'*.*')
    Fall = open(folder2+'list_all.txt','w')
    prefix='http://desdev2.cosmology.illinois.edu/static'
    for ff in allfiles:
        if (ff.find(siid+'.tar.gz')==-1 & ff.find('list.json')==-1): Fall.write(prefix+ff.split('static')[-1]+'\n')
    Fall.close()
    

    con = lite.connect(Settings.DBFILE)
    q="UPDATE Jobs SET status='SUCCESS' where job = '%s'" % jobid
    print(q)
    with con:
        cur = con.cursor()
        cur.execute(q)
    print('Done!')
    a=requests.get('http://localhost:8999/api/refresh/?user=%s&jid=%s' % (user,jobid))
    return jobid + '\n' + testtext
