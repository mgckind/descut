import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import Settings
import cx_Oracle
import os
import time
from version import __version__

dbConfig0 = Settings.dbConfig()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("usera")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        loc_passw = self.get_secure_cookie("userb").decode('ascii').replace('\"','')
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"','')
        newfolder = os.path.join(Settings.UPLOADS,loc_user)
        if not os.path.exists(newfolder):
            os.mkdir(newfolder)
        kwargs = {'host': dbConfig0.host, 'port': dbConfig0.port, 'service_name': 'desoper'}
        dsn = cx_Oracle.makedsn(**kwargs)
        dbh = cx_Oracle.connect(loc_user, loc_passw, dsn=dsn)
        cursor = dbh.cursor()
        cc=cursor.execute('select firstname, email from des_users where upper(username) = \'%s\'' % loc_user.upper()).fetchone()
        cursor.close()
        dbh.close()
        self.render("index.html", name=cc[0], email=cc[1], username=loc_user)

class AuthLoginHandler(BaseHandler):
    def get(self):
        try:
            errormessage = self.get_argument("error")
            print(errormessage)
        except:
            errormessage = ""
        self.render("login.html", errormessage = errormessage, version=__version__)

    def check_permission(self, password, username):
        kwargs = {'host': dbConfig0.host, 'port': dbConfig0.port, 'service_name': 'desoper'}
        dsn = cx_Oracle.makedsn(**kwargs)
        try:
            dbh = cx_Oracle.connect(username, password, dsn=dsn)
            dbh.close()
            return True,""
        except Exception as e:
            error = str(e).strip()
            return False,error


    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        auth,err = self.check_permission(password, username)
        if auth:
            self.set_current_user(username, password)
            newfolder = os.path.join(Settings.UPLOADS,username)
            if not os.path.exists(newfolder):
                os.mkdir(newfolder)
            # Add to DB for stats
            self.redirect(self.get_argument("next", u"/"))
        else:
            error_msg = u"?error=" + tornado.escape.url_escape(err)
            self.redirect(u"/login/" + error_msg)

    def set_current_user(self, user, passwd):
        if user:
            self.set_secure_cookie("usera", tornado.escape.json_encode(user), expires_days = 5)
            self.set_secure_cookie("userb", tornado.escape.json_encode(passwd), expires_days = 5)
        else:
            self.clear_cookie("usera")
            self.clear_cookie("userb")

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("usera")
        self.clear_cookie("userb")
        self.redirect(self.get_argument("next", "/"))

