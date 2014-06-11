import tornado.ioloop
from tornado.httpclient import HTTPClient, HTTPRequest, HTTPError

import traceback
import getpass
import json
import time


class InvalidLoginError(Exception):
    pass

def res_handler(response):
    print "response"
    if response.error:
        print "Error:",response.error
    else:
        print 'called'
        print response.body

class ChatClient(object):
    def __init__(self,server="127.0.0.1:8000"):
        self.http_client = HTTPClient()
        self.server = server
        self._loggedin = False
        self.session_token = ""
        self.username = ""
        
    def close(self):
        self.http_client.close()
    
    def loggedin(self):
        return self._loggedin
    
    def server_url(self):
        return "http://"+self.server
    
    def request(self,
            relative_url,
            chat_username="",
            chat_password="",
            chat_room_id="",
            *args,**kwargs):
        if "headers" in kwargs:
            if "CHAT_SESSION_TOKEN" in kwargs["headers"]:
                pass
            else:
                kwargs["headers"]["CHAT_SESSION_TOKEN"] = self.session_token
        else:
            kwargs["headers"] = {"CHAT_SESSION_TOKEN":self.session_token}
        if not relative_url.startswith('/'):
            relative_url = '/' + relative_url
        if not relative_url.endswith('/'):
            relative_url = relative_url + '/'
        return HTTPRequest(self.server_url()+relative_url,*args,**kwargs)
    
    def fetch(self,request):
        return self.http_client.fetch(request)
    
    def login(self):
        self.username = raw_input("Username: ")
        password = getpass.getpass()
        req = self.request('login',
            headers={
                "CHAT_UNAME":self.username,
                "CHAT_PWORD":password
            }
        )
        print "logging in...",
        self.login_cb(self.fetch(req))
    
    def login_cb(self,response):
        try:
            if response.error:
                print "LoginError:",response.code,response.error
            else:
                _json = json.loads(response.body)
                self.session_token = _json["session_token"]
                if len(self.session_token) == 16:
                    self._loggedin = True
                else:
                    self._loggedin = False
        except Exception as e:
            print e
            print traceback.format_exc()
            self._loggedin = False
        finally:
            print "Logged in:",len(self.session_token)==16,"Token:",self.session_token

    def logout(self):
        req = self.request('logout',headers={"CHAT_UNAME":self.username,"CHAT_PWORD":self.pword})
        return self.fetch(req,handle_request)
    
    def get_lobby(self):
        req = self.request('lobby',headers={"CHAT_UNAME":self.username,"CHAT_SESSION_TOKEN":self.session_token})
        self.get_lobby_cb(self.fetch(req))

    def get_lobby_cb(self,response):
        if response.error:
            print "Error fetching lobby: <"+str(response.code)+">",response.reason
        else:
            print response.body
            
    def join_room(self):
        req = self.request('join',headers={"CHAT_UNAME":self.username,"CHAT_PWORD":self.pword})
        return self.fetch(req,handle_request)
    
    def leave_room(self):
        req = self.request('leave',headers={"CHAT_UNAME":self.username,"CHAT_PWORD":self.pword})
        return self.fetch(req,handle_request)
    
    def create_room(self):
        req = self.request('create',headers={"CHAT_UNAME":self.username,"CHAT_PWORD":self.pword})
        return self.fetch(req,handle_request)


try:
    client = None
    client = ChatClient()
    client.login()
except HTTPError as e:
    print "HTTPError:",e
except Exception as e:
    print "Error:",e
    print traceback.format_exc()
finally:
    if client:
        client.close()
