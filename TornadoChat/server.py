import tornado.websocket
import tornado.web
import tornado.httpserver

import json

def get_user(username):
    users = [
        {
            'username':'joe',
            'password':'password',
            'session_token':'',
        },
    ]
    user = [user for user in users if user['username'] == username]
    if len(user) > 0:
        return user[0]
    else:
        return None


def authenticate(username,password):
    user = get_user(username)
    return user is not None and user['password'] == password

def get_new_token():
    return "a"*16

def jsonify(json_object):
    return json.dumps(json_object,separators=(",",":"))

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        req = self.request
        if authenticate(req.headers["CHAT_UNAME"],req.headers["CHAT_PWORD"]):
            user = get_user(req.headers["CHAT_UNAME"])
            token = user['session_token']
            if len(token) > 0:
                token = get_new_token() 
            _json = {
                "session_token":token
            }
            self.write(jsonify(_json))
        else:
            self.set_status(403,"Invalid Login Information")
    
class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Logout")

class LobbyHandler(tornado.web.RequestHandler):
    def get(self):
        req = self.request
        user = get_user(req.headers["CHAT_UNAME"])
        if user is not None and len(user['session_token']) == 16 and req.headers["CHAT_SESSION_TOKEN"] == user['session_token']:
            self.write("Lobby")
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
