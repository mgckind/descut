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
import login
import readfile

define("port", default=8000, help="run on the given port", type=int)

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
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    #http_server = tornado.httpserver.HTTPServer(Application(), ssl_options={"certfile": "/etc/httpd/ssl/des.crt", "keyfile": "/etc/httpd/ssl/des.key",})
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
