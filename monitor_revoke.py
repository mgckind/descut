from celery import Celery
import Settings
import sqlite3 as lite

def my_monitor(app):
    state = app.events.State()


    def update_revoked_tasks(event):
        state.event(event)
        # task name is sent only with -received event, and state
        # will keep track of this for us.
        task = state.tasks.get(event['uuid'])
        jobid = task.uuid
        jobid2=jobid[jobid.find('__')+2:jobid.find('{')-1]
        con = lite.connect(Settings.DBFILE)
        q0 = "UPDATE Jobs SET status='{0}' where job = '{1}'".format('REVOKE', jobid2)
        with con:
            cur = con.cursor()
            cur.execute(q0)
            con.commit()

        print('TASK REVOKED: %s[%s] %s' % (
            task.name, task.uuid, task.info(),))
        

    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={
                'task-revoked' : update_revoked_tasks,
                '*': state.event,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)

if __name__ == '__main__':
    app = Celery('dtasks')
    app.config_from_object('celeryconfig')
    my_monitor(app)
