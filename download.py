import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import pandas as pd
import os, uuid
import Settings
import time
import glob
import json
import subprocess

class BaseHandler(tornado.web.RequestHandler): 
    def get_current_user(self):
        return self.get_secure_cookie("usera").decode('utf-8')

class DownloadHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        pngName = self.get_argument("pngName")
        path = self.get_argument("path")
        # print('+-+-+-+-',pngName)
        # print('+-+-+-+-',path)
        fits_name = pngName.replace('.png','.fits')
        # user_folder=os.path.join(Settings.UPLOADS,self.current_user.replace('\"','')) + '/'
        username = self.current_user.replace('\"', '')
        app_dir = os.path.dirname(__file__)
        archiveFolder =  os.path.join(app_dir, 'static/uploads', username, 'results/tar/')
        
        tarName = pngName.replace('.png', '.tar.gz')
        filegz = path.replace('.png', '.tar.gz')
        if os.path.exists(archiveFolder+tarName):
            self.set_status(200)
            self.flush()
        else:
            os.chdir(app_dir+os.path.split(path)[0]+'/')
            print (os.getcwd())
            subprocess.check_call("tar -zcf {} {} {}".format(archiveFolder+tarName, pngName, fits_name), shell=True) 
            os.chdir(app_dir)
            
            self.set_status(200)
            self.flush()
        self.finish()

class DownloadObjectHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        path = self.get_argument("path")
        jobid_short = self.get_argument("jobid")[:6]
        username = self.current_user.replace('\"', '')
        app_dir = os.path.dirname(__file__)
        archiveFolder =  os.path.join(app_dir, 'static/uploads', username, 'results/tar/')
        tarName = jobid_short+'_'+os.path.split(path)[1]+'.tar.gz'

        if os.path.exists(archiveFolder+tarName):
            self.set_status(200)
            self.flush()
        else:
            os.chdir(app_dir+os.path.split(path)[0])
            subprocess.check_call("tar -zcf {} {}".format(archiveFolder+tarName, os.path.split(path)[1]+'/'), shell=True) 
            os.chdir(os.path.dirname(__file__))
            
            self.set_status(200)
            self.flush()
        self.finish()