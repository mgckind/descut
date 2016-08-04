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

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        loc_passw = self.get_secure_cookie("pass").replace('\"','')
        loc_user = self.get_secure_cookie("user").replace('\"','')
        self.render("index.html")

class AuthLoginHandler(BaseHandler):
    def get(self):
        try:
            errormessage = self.get_argument("error")
            print(errormessage)
        except:
            errormessage = ""
        self.render("login.html", errormessage = errormessage)

    def check_permission(self, password, username):
        if username=='admin' and password=='admin':
            return True, ""
        else:
            return False, 'Wrong credentials'


    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        auth,err = self.check_permission(password, username)
        if auth:
            self.set_current_user(username, password)
            # Add to DB
            self.redirect(self.get_argument("next", u"/"))
        else:
            error_msg = u"?error=" + tornado.escape.url_escape(err)
            self.redirect(u"/login/" + error_msg)

    def set_current_user(self, user, passwd):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user), expires_days = 5)
            self.set_secure_cookie("pass", tornado.escape.json_encode(passwd), expires_days = 5)
        else:
            self.clear_cookie("user")
            self.clear_cookie("pass")

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("pass")
        self.redirect(self.get_argument("next", "/"))

