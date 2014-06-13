import tornado.websocket
import tornado.web
import tornado.httpserver

import json
import random
import traceback

from chat_db import ChatUser

SESSION_CACHE = {}

def get_user(username):
    if username in SESSION_CACHE:
        return SESSION_CACHE[username
    return ChatUser.get_user(username)

def authenticate(username,password):
    user = get_user(username)
    return user is not None and user.login(password)

def random_char():
    return chr(random.choice(range(33,95)+range(96,127)))

def random_string(n):
    s = ""
    for i in range(n):
        s += random_char()
    return s

def get_new_token():
    return random_string(16)

def serialize(json_object):
    return json.dumps(json_object,separators=(",",":"))

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            req = self.request
            print req
            if authenticate(req.headers["CHAT_UNAME"],req.headers["CHAT_PWORD"]):
                user = get_user(req.headers["CHAT_UNAME"])
                token = user.session_token
                if len(token) == 0:
                    token = get_new_token()
                _json = {
                    "session_token":token
                }
                SESSION_CACHE[user.username] = user
                self.write(serialize(_json))
                print "Logged in",user.username
            else:
                self.set_status(403,"Invalid Login Information")
        except Exception as e:
            print traceback.format_exc()
            self.set_status(500,"ServerError: "+str(e))

class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Logout")

class LobbyHandler(tornado.web.RequestHandler):
    def get(self):
        req = self.request
        user = get_user(req.headers["CHAT_UNAME"])
        if user is not None and req.headers["CHAT_SESSION_TOKEN"] == user.session_token:
            _json = {
                "rooms":[],
                "users":[]
            }
            for user in ChatUser.getall()
            self.write(serialize(_json))
        else:
            self.set_status(403,"Invalid session, please login")

class JoinHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Join")

class LeaveHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Leave")

class CreateHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Create")


app = tornado.web.Application([
    (r'/login/',LoginHandler),
    (r'/logout/',LogoutHandler),
    (r'/lobby/',LobbyHandler),
    (r'/join/',JoinHandler),
    (r'/leave/',LeaveHandler),
    (r'/create/',CreateHandler),
])


if __name__ == "__main__":
    app.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
