import tornado.websocket
import tornado.web
import tornado.httpserver

import json

def authenticate(username,password):
    users = dict([('joe','password'),('adrian','password')])
    if username not in users:
        return False
    return users[username] == password

def get_new_token():
    return "a"*16

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        req = self.request
        if authenticate(req.headers["CHAT_UNAME"],req.headers["CHAT_PWORD"]):
            _json = {"session_token":get_new_token()}
            self.write(json.dumps(_json,separators=(",",":")))
        else:
            self.status_code(403,"Invalid Login Information")
    
class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Logout")

class LobbyHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Lobby")

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
