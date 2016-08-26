""" Main application for public release"""
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
import os
import login
import readfile
import sqlite3 as lite
import dtasks

define("port", default=443, help="run on the given port", type=int)

def create_db(delete=False):
    dirname = os.path.dirname(Settings.DBFILE)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    con = lite.connect(Settings.DBFILE)
    with con:
        cur = con.cursor()
        if delete:
            cur.execute("DROP TABLE IF EXISTS Jobs")
        cur.execute("CREATE TABLE IF NOT EXISTS  Jobs(user text, job text, status text, time datetime, type text)")



class Application(tornado.web.Application):
    """
    The tornado application  class
    """
    def __init__(self):
        handlers = [
            (r"/", login.MainHandler),
            (r"/login/", login.AuthLoginHandler),
            (r"/logout/", login.AuthLogoutHandler),            
            (r"/api/?", api.ApiHandler),
            (r"/api/canceljob/?", api.CancelJobHandler),
            (r"/api/log/?", api.LogHandler),
            (r"/api/token/?", api.TokenHandler),            
            (r"/api/jobs/?", api.JobHandler),            
            (r"/api/refresh/?", readfile.RefreshHandler),
            (r'/websocket', readfile.WebSocketHandler),
            (r"/readfile/", readfile.FileHandler),
            ]
        settings = {
            "template_path":Settings.TEMPLATE_PATH,
            "static_path":Settings.STATIC_PATH,
            "debug":Settings.DEBUG,
            "cookie_secret": Settings.COOKIE_SECRET,
            "login_url": "/login/",            
        }
        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    """
    The main function
    """
    if not os.path.exists(Settings.UPLOADS):
        os.mkdir(Settings.UPLOADS)
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
