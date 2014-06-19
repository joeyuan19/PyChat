import socket
import select
import threading
import json

def _write_log(entry):
    with open('pychat.log','a') as f:
        f.write(str(entry)+"\n")

def write_log(*args):
    msg = ''
    for arg in args:
        msg += str(arg) + ' '
    _write_log(msg)

def write_err(e,err_title="PyChatError"):
    write_log(err_title+": "+str(e)+"\n",traceback.format_exc())

def serialize(_json):
    return json.dumps(_json,separators=(":",","))


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
        while not self.isstopped() and self.isactive():
            rsockets, wsockets, errsockets = select.select([sock for sock,user in self.sockets],[],[])
            for sock in rsockets:
                if sock == self.server_socket:
                    new_conn, new_addr = sock.accept()
                    user = new_conn.recv(128)
                    _json = json.loads(user)
                    if _json["sess"] in self.cache:
                        c = self.connect_user(_user, new_conn)
                        _json = {
                            "users":[user.username for sock,user in self.sockets],
                            "name":self.name,
                            "frmt":c
                        }
                        write_log("<",_json,">")
                        new_conn.send(serialize(_json))
                    else:
                        new_conn.close()
                else:
                    try:
                        msg = sock.recv(self.RECV_SIZE)
                        self.adjust_activity(sock)
                        self.broadcast(msg)
                    except Exception as e:
                        write_err("ReceiveError:",e)
                        self.disconnect_user(sock=sock)
        self.disconnect()
    
    def adjust_activity(self,sock):
        pass

    def broadcast(self,msg):
        for sock,user in self.sockets:
            if sock != self.server_sock:
                try:
                    sock.send(msg)
                except:
                    self.disconnect_user(sock=sock)

    def connect_user(self,user,sock):
        self.sockets.append((sock,user))
        c = self.get_new_color()
        self.user_color[c] = user
        return c
        
    def disconnect_user(self,user=None,sock=None,index=None):
        if index is not None:
            try:
                self.package_and_broadcast(msg=user.name+" has left the room...")
                self.sockets[index][0].close()
                self.sockets.pop(index)
                return
            except Exception as e:
                write_err("Disconnect Exception:",e)
                return
        if user is None and sock is None:
            return
        for i,pair in enumerate(self.sockets):
            sock,user = pair
            if user == sock[1] or sock == sock[0]:
                disconnect_user(index=i)
                break

    def disconnect(self):
        for sock,user in self.sockets:
            if sock:
                sock.close()
        self.room.delete()
        self.stop()

    def isactive(self):
        return True
