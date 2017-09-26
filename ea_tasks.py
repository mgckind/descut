from celery import Celery, Task
import easyaccess as ea
import requests
from Crypto.Cipher import AES
import base64
import sqlite3 as lite
import Settings
import os
import threading
import time
import json
import glob
import MySQLdb as mydb
import yaml
#import config.mysqlconfig as ms

app = Celery('ea_tasks')
app.config_from_object('config.celeryconfig')


def get_filesize(filename):
    size = os.path.getsize(filename)
    size = size * 1. / 1024.
    if size > 1024. * 1024:
        size = '%.2f GB' % (1. * size / 1024. / 1024)
    elif size > 1024.:
        size = '%.2f MB' % (1. * size / 1024.)
    else:
        size = '%.2f KB' % (size)
    return size


class CustomTask(Task):

    abstract = None

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        url = 'http://localhost:8080/pusher/pusher/'
        # data = {'username': retval['user'], 'result': retval['data'], 'status': retval['status'],
        #         'kind': retval['kind']}
        #con = lite.connect(Settings.DBFILE)
        with open('config/mysqlconfig.yaml', 'r') as cfile:
            conf = yaml.load(cfile)['mysql']
        con = mydb.connect(**conf)
        #con = mydb.connect(host=ms.host, port=ms.port, user=ms.user, passwd=ms.passwd, db=ms.db)
        file_list = json.dumps(retval['files'])
        size_list = json.dumps(retval['sizes'])
        if retval['status'] == 'ok':
            temp_status = 'SUCCESS'
        else:
            temp_status = 'FAIL'
        q0 = "UPDATE Jobs SET status='{0}' where job = '{1}'".format(temp_status, task_id)
        q1 = "UPDATE Jobs SET files='{0}' where job = '{1}'".format(file_list, task_id)
        q2 = "UPDATE Jobs SET sizes='{0}' where job = '{1}'".format(size_list, task_id)
        #with con:
        cur = con.cursor()
        cur.execute(q0)
        if retval['files'] is not None:
            cur.execute(q1)
            cur.execute(q2)
        con.commit()
        con.close()
        requests.post(url, data=retval)


@app.task(base=CustomTask)
def run_query(query, filename, db, username, lp, jid, timeout=None):
    """
    Run a query

    Parameters
    ----------
    query : str
    filename : str
        None if not output filename
    db : database
    username : username
    lp : encypted password
    jid: Job (Task) id
    timeout: int, optional
        Timeout in seconds

    Returns
    -------
    dict
        response dictionary with following keys:
        - user    : username
        - elapsed : time in seconds
        - status  : 'ok'/'error'
        - data    : json array of data or message
        - kind    : 'query' (any no select statement) / 'select' (select statement)
        - jobid   : Job id
        - files   : list of created files
        - sizes   : list of  sizes of created filenames

    """
    response = {}
    response['user'] = username
    response['elapsed'] = 0
    response['jobid'] = jid
    response['files'] = None
    response['sizes'] = None
    user_folder = os.path.join(Settings.WORKDIR, username)+'/'
    if filename is not None:
        if not os.path.exists(os.path.join(user_folder, jid)):
            os.mkdir(os.path.join(user_folder, jid))
    jsonfile = os.path.join(user_folder, jid+'.json')
    cipher = AES.new(Settings.SKEY, AES.MODE_ECB)
    dlp = cipher.decrypt(base64.b64decode(lp)).strip()
    try:
        connection = ea.connect(db, user=username, passwd=dlp.decode())
        cursor = connection.cursor()
    except Exception as e:
            response['status'] = 'error'
            response['data'] = str(e).strip()
            response['kind'] = 'query'
            with open(jsonfile, 'w') as fp:
                json.dump(response, fp)
            return response
    if timeout is not None:
        tt = threading.Timer(timeout, connection.con.cancel)
        tt.start()
    t1 = time.time()
    if query.lower().lstrip().startswith('select'):
        response['kind'] = 'select'
        try:
            if filename is not None:
                outfile = os.path.join(user_folder, jid, filename)
                connection.query_and_save(query, outfile)
                if timeout is not None:
                    tt.cancel()
                t2 = time.time()
                job_folder = os.path.join(user_folder, jid)+'/'
                files = glob.glob(job_folder+'*')
                response['files'] = [os.path.basename(i) for i in files]
                response['sizes'] = [get_filesize(i) for i in files]
                data = 'File {0} written'.format(outfile)
                response['kind'] = 'query'
            else:
                df = connection.query_to_pandas(query)
                if timeout is not None:
                    tt.cancel()
                data = df.to_json(orient='records')
                t2 = time.time()
            response['status'] = 'ok'
            response['data'] = data
        except Exception as e:
            if timeout is not None:
                tt.cancel()
            t2 = time.time()
            response['status'] = 'error'
            response['data'] = str(e).strip()
            response['kind'] = 'query'
    else:
        response['kind'] = 'query'
        try:
            df = cursor.execute(query)
            connection.con.commit()
            if timeout is not None:
                tt.cancel()
            t2 = time.time()
            response['status'] = 'ok'
            response['data'] = 'Done!'
        except Exception as e:
            if timeout is not None:
                tt.cancel()
            t2 = time.time()
            response['status'] = 'error'
            response['data'] = str(e).strip()

    response['elapsed'] = t2 - t1
    with open(jsonfile, 'w') as fp:
        json.dump(response, fp)
    cursor.close()
    connection.close()
    return response
