""" Main application for public release"""
from version import __version__
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.log
import Settings
from tornado.options import define, options
import api
import pusher
import queries
import os
import login
import readfile
import sqlite3 as lite
import dtasks
import download
import yaml
import MySQLdb as mydb
import backup

define("port", default=8999, help="run on the given port", type=int)

def create_db(delete=False):
    dirname = os.path.dirname(Settings.DBFILE)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open('config/mysqlconfig.yaml', 'r') as cfile:
        conf = yaml.load(cfile)['mysql']
    conf.pop('db', None)
    con = mydb.connect(**conf)
    try:
        con.select_db('des')
    except:
        backup.restore()
        con.commit()
        con.select_db('des')
    cur = con.cursor()
    if delete:
        cur.execute("DROP TABLE IF EXISTS Jobs")
    cur.execute("CREATE TABLE IF NOT EXISTS  \
        Jobs(user text, job text, status text, time datetime, type text, query mediumtext, files text, sizes text)")
    con.commit()
    con.close()
#
# def create_db(delete=False):
#     dirname = os.path.dirname(Settings.DBFILE)
#     if not os.path.exists(dirname):
#         os.mkdir(dirname)
#     con = lite.connect(Settings.DBFILE)
#     with con:
#         cur = con.cursor()
#         if delete:
#             cur.execute("DROP TABLE IF EXISTS Jobs")
#         cur.execute("CREATE TABLE IF NOT EXISTS  \
#         Jobs(user text, job text, status text, time datetime, type text, query mediumtext, files text, sizes text)")



class Application(tornado.web.Application):
    """
    The tornado application  class
    """
    def __init__(self):
        handlers = [
            (r"/", login.MainHandler),
            (r"/footprint", login.FootHandler),
            (r"/login/", login.AuthLoginHandler),
            (r"/logout/", login.AuthLogoutHandler),            
            (r"/api/?", api.ApiHandler),
            (r"/api/canceljob/?", api.CancelJobHandler),
            (r"/api/log/?", api.LogHandler),
            (r"/api/token/?", api.TokenHandler),            
            (r"/api/jobs/?", api.JobHandler),
            (r"/api/mongo/?", api.MongoHandler),
            # (r"/api/shared/?", api.ShareHandler),
            # (r"/api/sharejob/?", api.ShareJobHandler),
            # (r"/api/addcomment/?", api.AddCommentHandler),
            (r"/api/refresh/?", readfile.RefreshHandler),
            (r'/websocket', readfile.WebSocketHandler),
            (r"/readfile/coadd/", readfile.FileHandler),
            (r"/readfile/single/", readfile.FileHandlerS),
            (r"/download/object/", download.DownloadObjectHandler),
            (r"/download/single/", download.DownloadHandler),
            # (r"/api/myjobs/", api.MyJobsHandler),
            (r"/api/myresponse/", api.MyResponseHandler),
            (r"/api/mytables/", api.MyTablesHandler),
            (r"/api/desctables/", api.DescTablesHandler),
            (r"/api/alltables/", api.AllTablesHandler),
            (r'/pusher/websocket/', pusher.WebSocketHandler),
            (r'/pusher/pusher/', pusher.PusherHandler),
            (r"/queries/query/", queries.QueryHandler),

            ]
        settings = {
            "template_path":Settings.TEMPLATE_PATH,
            "static_path":Settings.STATIC_PATH,
            "debug":Settings.DEBUG,
            "cookie_secret": Settings.COOKIE_SECRET,
            "login_url": "/login/",
            "static_url_prefix": "/static/",
        }
        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    """
    The main function
    """
    if not os.path.exists(Settings.UPLOADS):
        os.mkdir(Settings.UPLOADS)
    if not os.path.exists(Settings.WORKDIR):
        os.mkdir(Settings.WORKDIR)
    if not os.path.exists(Settings.WORKERS):
        os.mkdir(Settings.WORKERS)
    create_db()
    tornado.options.parse_command_line()
    if options.port == 443:
        http_server = tornado.httpserver.HTTPServer(Application(), ssl_options={"certfile": "/des/etc/cks/descut_cert.cer", "keyfile": "/des/etc/cks/descut.key",})
    else:
        http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
