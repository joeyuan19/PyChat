import tornado.websocket
import tornado.web
import tornado.httpserver

import json
import random
import traceback

from db import ChatUser
from room import RoomManager

class Cache(dict):
    def __init__(self):
        self.rooms = {}

    def get_user(self,username):
        if username in self:
            return self[username]
        return ChatUser.get_user(username)

    def add_room(self,room):
        self.rooms[len(self.rooms)] = room

    def get_room(self,room_id):
        if isinstance(room_id,basestring):
            room_id = int(room_id)
        if room_id in self.rooms:
            return self.rooms[room_id]
        else:
            return None

    def get_active_rooms(self):
        return [(i,j) for i,j in self.rooms.iteritems()]

SESSION_CACHE = Cache()

def get_user(username):
    if username in SESSION_CACHE:
        return SESSION_CACHE[username]
    return ChatUser.get_user(username)

def login(username,password):
    user = get_user(username)
    return user is not None and user.login(password)

def authenticate(request):
    try:
        username = request.headers["CHAT_UNAME"]
        token = request.headers["CHAT_SESSION_TOKEN"]
        user = get_user(username)
        return user is not None and token == user.session_token
    except:
        return False

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
            if login(req.headers["CHAT_UNAME"],req.headers["CHAT_PWORD"]):
                user = get_user(req.headers["CHAT_UNAME"])
                token = user.session_token
                if len(token) == 0:
                    token = get_new_token()
                    user.session_token = token
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
        if authenticate(self.request):
            _json = {
                "rooms":[],
                "users":[]
            }
            for user in ChatUser.getall():
                _json["users"].append({
                    "username":user.username,
                    "status":user.username in SESSION_CACHE
                })
            for room_id,room in SESSION_CACHE.get_active_rooms():
                _json["rooms"].append({
                    "room_id":room_id
                })
            self.write(serialize(_json))
        else:
            self.set_status(403,"Invalid session, please login")

class JoinHandler(tornado.web.RequestHandler):
    def get(self):
        if authenticate(self.request):
            req = self.request
            try:
                room = SESSION_CACHE.get_room(req.headers["CHAT_ROOM_ID"])
                if room is not None:
                    _addr = room.addr()
                    _json = {"addr":{"host":_addr[0],"port":_addr[1]}}
                    self.write(serialize(_json))
                    print "User",req.headers["CHAT_UNAME"],"joined a room"
                else:
                    self.set_status(400,"Room "+req.headers["CHAT_ROOM_ID"]+" Not found")
            except Exception as e:
                print traceback.format_exc()
                self.set_status(500,"Invalid session, please login")
        else:
            self.set_status(403,"Invalid session, please login")


class LeaveHandler(tornado.web.RequestHandler):
    def get(self):
        if authenticate(self.request):
            req = self.request
            try:
                room = SESSION_CACHE.get_room(req.headers["CHAT_ROOM_ID"])
                if room is not None:
                    if room.user_in_room(req.headers["CHAT_UNAME"]):
                        pass
                    else:
                        self.set_status(403,"User: "+req.headers["CHAT_UNAME"]+" not in room "+req.headers["CHAT_ROOM_ID"])
                else:
                    self.set_status(400,"Room "+req.headers["CHAT_ROOM_ID"]+" Not found")
            except Exception as e:
                print traceback.format_exc()
                self.set_status(500,"Invalid session, please login")
        else:
            self.set_status(403,"Invalid session, please login")

        
class CreateHandler(tornado.web.RequestHandler):
    def get(self):
        if authenticate(self.request):
            room = RoomManager(SESSION_CACHE)
            while not room.is_alive():
                pass
            _addr = room.addr()
            _json = {"addr":{"host":_addr[0],"port":_addr[1]}}
            self.write(serialize(_json))
            SESSION_CACHE.add_room(room)
            print "User",self.request.headers["CHAT_UNAME"],"created a room"
        else:
            self.set_status(403,"Invalid session, please login")
            
        


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
    print "Server started..."
    tornado.ioloop.IOLoop.instance().start()
