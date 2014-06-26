import tornado.ioloop
from tornado.httpclient import HTTPClient, HTTPRequest, HTTPError

from display import ChatDisplayManager

import traceback
import getpass
import json
import time
import sys


class InvalidLoginError(Exception):
    pass

class RoomCreationError(Exception):
    pass

class LobbyError(Exception):
    pass

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
        response = self.fetch(req)
        print
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
        return self._loggedin
    
    def logout(self):
        req = self.request('logout',
            headers={
                "CHAT_UNAME":self.username,
                "CHAT_SESSION_TOKEN":self.session_token
            }
        )
        return self.fetch(req,handle_request)
    
    def get_lobby(self):
        req = self.request('lobby',
            headers={
                "CHAT_UNAME":self.username,
                "CHAT_SESSION_TOKEN":self.session_token
            }
        )
        return self.get_lobby_cb(self.fetch(req))

    def get_lobby_cb(self,response):
        if response.error:
            raise LobbyError("Failed to fetch Lobby <"+str(response.code)+" "+str(response.error)+" >")
        else:
            return response
    def join(self,room_id):
        res = self.join_room(room_id)
        if res.error:
            raise RoomCreationError(" Server returned <"+str(res.code)+" "+res.error+">")
        else:
            manager = ChatDisplayManager(self.session_token,self.username)
            _json = json.loads(res.body)
            manager.run_chat_room((_json["addr"]["host"],int(_json["addr"]["port"])))

    
    def join_room(self,room_id):
        req = self.request(
            'join',
            headers={
                "CHAT_UNAME":self.username,
                "CHAT_SESSION_TOKEN":self.session_token,
                "CHAT_ROOM_ID":str(room_id)})
        return self.fetch(req)
    
    def leave_room(self):
        req = self.request('leave',headers={"CHAT_UNAME":self.username,"CHAT_PWORD":self.pword})
        return self.fetch(req,handle_request)
    
    def create(self):
        res = self.create_room()
        if res.error:
            raise RoomCreationError(" Server returned <"+str(res.code)+" "+res.error+">")
        else:
            manager = ChatDisplayManager(self.session_token,self.username)
            _json = json.loads(res.body)
            manager.run_chat_room((_json["addr"]["host"],int(_json["addr"]["port"])))
    
    def create_room(self):
        req = self.request('create',headers={
            "CHAT_UNAME":self.username,
            "CHAT_SESSION_TOKEN":self.session_token})
        return self.fetch(req)

def pad(s,n,ch=" ",left=True):
    if left:
        return s+ch*(n-len(s))
    else:
        return ch*(n-len(s))+s

def get_pad_length(li):
    mx = 0
    for it in li:
        mx = max(mx,len(it))
    return mx


try:
    client = None
    client = ChatClient()
    try_count = 0
    while True:
        try:
            if client.login():
                break
        except:
            print
        try_count += 1
        if try_count == 3:
            print "Three failed login attempts."
            sys.exit()
    SHOW_OFFLINE = False
    while True:
        lobby = client.get_lobby()
        _json = json.loads(lobby.body)
        print "\n\n\nLobby\n"
        print "Enter 'help' for help"
        print
        # Display Rooms
        options = []
        if len(_json["rooms"]) > 0:
            print "Active Rooms:"
            for room in _json["rooms"]:
                print "<"+str(len(options))+">",
                print "Join Room",room["room_id"]
                options.append("room:"+str(room["room_id"]))
        else:
            print "No active rooms"
        
        print "<"+str(len(options))+">",
        print "Create new room"
        options.append("create")
        print

        if len(_json["users"]) > 0:
            print "User list:"
        else:
            pad_space = get_pad_length([user["username"] for user in _json["users"] if SHOW_OFFLINE or user["status"] != "offline"])
            for user in _json["users"]:
                print "<"+str(len(options))+">",
                print pad(user["username"],pad_space),user["status"]
                options.append("user:"+room["username"])
                
        # Show offline
        print "<"+str(len(options))+">",
        print "Show Offline"
        options.append("toggle_offline")
        print
        
        # logout
        print "<"+str(len(options))+">",
        print "Logout"
        options.append("logout")
        print

        choice = raw_input("Choose option or press enter to continue:\n>>> ").strip()
        if len(choice) == 0:
            continue
        try:
            choice = int(choice)
        except:
            print "Invalid choice"
            continue
        
        action = options[choice]
        if action == "logout":
            client.logout()
        elif action == "toggle_offline":
            SHOW_OFFLINE = not SHOW_OFFLINE
        elif action == "create":
            client.create()
        elif action.startswith("user:"):
            pass # create a new room, notify user of desire to chat
        elif action.startswith("room:"):
            client.join(int(action[action.find(":")+1:]))

except HTTPError as e:
    print "HTTPError:",e
except Exception as e:
    print "Error:",e
    print traceback.format_exc()
finally:
    if client:
        client.close()

















