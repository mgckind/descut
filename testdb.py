import sqlite3 as lite
import json
import sys
import datetime as dt

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

def tup(entry,i, user='mcarras2'):
    return (i,user,job_s(entry),entry['status'],dt_t(entry))

with open('static/jobs.json','r') as F:
    J =json.load(F)

bigJ=[]
for i in range(len(J)):
    bigJ.append(tup(J[i],i))

bigJ=tuple(bigJ)

con = lite.connect('test.db')

# write
with con:
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS Jobs")
    cur.execute("CREATE TABLE Jobs(id integer primary key, user text, job text, status text, time datetime)")
    cur.executemany("INSERT INTO Jobs VALUES(?, ?, ?, ? , ?)", bigJ)

#read
    with con:
        cur = con.cursor()
        cc = cur.execute("SELECT * from Jobs where time > datetime('2016-07-20')").fetchall()

    cc = list(cc)

    jjob=[]
    jstatus=[]
    jtime=[]
    jelapsed=[]

    for i in range(len(cc)):
        dd = dt.datetime.strptime(cc[i][4],'%Y-%m-%d %H:%M:%S')
        ctime = dd.strftime('%a %b %d %H:%M:%S %Y')
        jjob.append(cc[i][1]+'__'+cc[i][2]+'_{'+ctime+'}')
        jstatus.append(cc[i][3])
        jtime.append(ctime)
        jelapsed.append((dt.datetime.now()-dd).total_seconds())

    out_dict=[dict(job=jjob[i],status=jstatus[i], time=jtime[i], elapsed=humantime(jelapsed[i])) for i in range(len(jjob))]
    with open('static/jobs2.json',"w") as outfile:
        json.dump(out_dict, outfile, indent=4)


