import socket
import select
import random
import threading
import traceback
import datetime
import json

def _write_log(entry):
    with open('room.log','a') as f:
        f.write(time_now()+" " +str(entry)+"\n")

def write_log(*args):
    msg = ''
    for arg in args:
        msg += str(arg) + ' '
    _write_log(msg)

def write_err(err_name="PyChatError"):
    write_log(str(err_name)+":\n",traceback.format_exc())

def serialize(_json):
    return json.dumps(_json,separators=(",",":"))

def deserialize(_json):
    return json.loads(_json)

def time_now():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

class RoomManager(threading.Thread):
    CONNECT_LIMIT = 10
    RECV_SIZE = 4096
    COLORS = [
        (0,i) for i in range(1,8)
    ] + [
        (1,i) for i in [0,3,4,6]
    ] + [
        (2,i) for i in [0,3,4,6]
    ] + [
        (3,i) for i in range(0,8) if i != 3
    ] + [
        (4,i) for i in range(0,8) if i != 4 or i != 6
    ] + [
        (5,i) for i in range(0,8) if i != 5 or i != 7
    ] + [
        (6,i) for i in range(0,8) if i != 6 or i != 4
    ] + [
        (7,i) for i in range(0,8) if i != 7 or i != 5
    ]
    name = ""
    def __init__(self,cache,*args,**kwargs):
        self.cache = cache
        self._stop = threading.Event()
        self.host = 'localhost'
        # set up sever socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost',0))
        self.server_socket.listen(self.CONNECT_LIMIT)
        # Initiate Socket List
        self.sockets = [(self.server_socket,None)]
        self.web_sockets = []
        self.msg_queue = []
        self.user_color = {}
        super(RoomManager,self).__init__(*args,**kwargs)
        self.setDaemon(True)
        self.start()

    def activity(self):
        self.last_active = timezone.now()

    def get_new_color(self):
        return random.choice([c for c in self.COLORS if c not in self.user_color])
    
    def get_user_color(self,user):
        for color,user in self.user_color.iteritems():
            if user == user:
                return color

    def addr(self):
        return self.server_socket.getsockname()
    
    def stop(self):
        self._stop.set()
    
    def isstopped(self):
        return self._stop.isSet()

    def run(self):
        write_log("create room")
        try:
            while not self.isstopped() and self.isactive():
                rsockets, wsockets, errsockets = select.select([sock for sock,user in self.sockets],[],[])
                for sock in rsockets:
                    if sock == self.server_socket:
                        new_conn, new_addr = sock.accept()
                        new_user = new_conn.recv(128)
                        _json = deserialize(new_user)
                        if _json["name"] in self.cache and self.cache[_json["name"]].session_token == _json["sess"]:
                            c = self.connect_user(self.cache[_json["name"]], new_conn)
                            new_conn.send(serialize({
                                "users":[(user.username,frmt) for frmt,user in self.user_color.iteritems()],
                                "name":self.name,
                                "frmt":c
                            }))
                            self.broadcast(serialize(
                                {
                                    "verb":"join",
                                    "name":_json["name"],
                                    "frmt":c,
                                }
                            ))
                        else:
                            write_log("new conn refused",_json)
                            new_conn.close()
                    else:
                        try:
                            msg = sock.recv(self.RECV_SIZE)
                            self.adjust_activity(sock)
                            self.broadcast(msg)
                        except Exception as e:
                            write_err("ReceiveError")
                            self.disconnect_user(sock=sock)
        except:
            write_log("ServerCloseError",traceback.format_exc())
        write_log("closing room")
        self.disconnect()
    
    def adjust_activity(self,sock):
        pass

    def broadcast(self,msg):
        for sock,user in self.sockets:
            if sock != self.server_socket:
                try:
                    sock.send(msg)
                except:
                    self.disconnect_user(sock=sock)

    def connect_web_user(self,user,websock):
        self.web_sockets.append((websock,user))
        c = self.get_new_color()
        self.user_color[c] = user

    def connect_user(self,user,sock):
        self.sockets.append((sock,user))
        c = self.get_new_color()
        self.user_color[c] = user
        return c
        
    def disconnect_user(self,user=None,sock=None,index=None,username=None):
        if self.server_socket == sock:
            write_log("Tried to disconnect the server sock")
            return
        if index is not None:
            try:
                self.sockets[index][0].close()
                self.sockets.pop(index)
                return
            except Exception as e:
                write_err("Disconnect Exception")
                return
        if user is None and sock is None:
            return
        for i,pair in enumerate(self.sockets):
            _sock,_user = pair
            if (_user is not None and _user == user) or (_sock is not None and _sock == sock):
                self.disconnect_user(index=i)
                break

    def disconnect(self):
        for sock,user in self.sockets:
            if sock:
                sock.close()
        self.stop()

    def isactive(self):
        return True
