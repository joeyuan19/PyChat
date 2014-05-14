from django.db import models
from django.utils import timezone

import random
import re
import time
import datetime


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
# To Do:
#    [ ] Make it work
#    [ ] Possible Improvement: make a listener thread and a broadcast thread
#    [ ] HTTP connection and sercurity
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def date_now():
    return timezone.now().strftime("%m/%d/%Y")

def time_now():
    return timezone.now().strftime("%H:%M:%S")

def write_err(*args):
    msg = ""
    for arg in args:
        msg += str(arg) + " "
    msg = msg[:-1]
    with open("err.log","a") as f:
        f.write(date_now() + " " + time_now() + "#" + msg + "\n") 

def write_log(*args):
    msg = ""
    for arg in args:
        msg += str(arg) + " "
    msg = msg[:-1]
    with open("chat_app.log","a") as f:

# Constants

def random_char():
    r = random.choice(range(33,95)+range(96,127))
    return chr(r)

def random_string(n):
    s = ""
    for i in range(n):
        s += random_char()
    return s

def parse_msgs(block):
    exp = r'<msg>.*?</msg>'
    m = re.findall(exp, block, re.S)
    return [parse_msg(i) for i in m]

def parse_msg(msg):
    exp = r'<body>(.*?)</body><date>(.*?)</date><c>(\d+/\d+)</c>'
    m = re.search(exp, msg, re.S)
    return [m.group(i) for i in range(4)]
    

class Message(object):
    def __init__(self,msg):
        self.body,self.date,self.user,self.part = parse_msg(msg)

class RoomManager(threading.Thread):
    CONNECT_LIMIT = 10
    CONNECT_ATTEMPTS = 3
    RECV_SIZE = 2048
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
    def __init__(self,*args,**kwargs):
        super(RoomThread,self).__init__(*args,**kwargs)
        self._stop = threading.Event()
        self.room = Room()
        self.host = 'localhost'
        # set up sever socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.listen(self.CONNECT_LIMIT)
        # Initiate Socket List
        self.sockets = []
        self.msg_queue = []
        self.last_active = datetime.datetime.today()
        self.user_color = {}

    def get_new_color(self):
        return random.choice([c for c in self.COLORS if c not in self.user_color])
        
    def get_receive_port(self):
        return self.receive_port
    
    def get_send_port(self):
        return self.send_port
    
    def stop(self):
        self._stop.set()
    
    def isstopped(self):
        return self._stop.isSet()

    def run(self):
        while not self.isstopped():
            rsockets, wsockets, errsockets = select.select([sock[0] for sock in self.sockets],[],[])
            for sock in rsockets:
                if sock == self.server_socket:
                    new_conn, new_addr = sock.accept()
                    user = new_conn.recv(128)
                    if not user:
                        self.connect_user(user,new_sock)
                    else:
                        new_conn.close()
                else:
                    try:
                        msg = sock.recv(self.RECV_SIZE)
                        self.broadcast(msg)
                    else:
                        self.disconnect_user(sock=sock)
        self.disconnect()
    
    def broadcast(self,*msgs):
        msg = ""
        for _msg in msgs:
            msg += str(_msg) + " "
        msg = msg[:-1]
    
    def _broadcast(self,msg):
        count = len(msg)/RECV_LIMIT + 1
        i = 1
        while len(msg) > self.RECV_LIMIT:
            


    def next_req(self):
        if len(self.req_queue) > 0:
            return self.req_queue.pop(0)
        else:
            return None

    def connect_user(self,u_name,sock):
        user = Users.objects.get(name=u_name)
        if user.count() == 0:
            sock.close()
        else:
            user = user[0]
            if user.isactive():
                self.sockets.append((sock,user))
                self.user_color[get_new_color] = user
                self.broadcast(user,"has entered the room...")
            else:
                sock.close()
        
    def get_users(self):
        return ', '.join(i[1].name for i in self.

    def disconnect_user_by_socket(self,sock):
        disconnect_user(sock=sock)
            
    def disconnect_user_by_user(self,user):
        disconnect_user(user=user)

    def disconnect_user(self,user=None,sock=None,index=None):
        if index is not None:
            try:
                self.broadcast(user.name,"has left the room...")
                self.sockets[index][0].close()
                self.sockets.pop(index)
                return
            except:
                pass
        if user is None and sock is None:
            return
        for i, sock in enumerate(self.sockets):
            if user == sock[1] or sock == sock[0]:
                disconnect_user(index=i)
                break

    def add_req(self,req):
        self.req_queue.append(req)

    def disconnect(self):
        for sock in self.sockets:
            if sock:
                sock.close()

    def isactive(self):
        return len(self.sockets) > 0


class Room(models.Model):
    room_id = models.IntegerField()
    
    def __init__(self,name,*args,**kwargs):
        super(Room, self).__init__(*args,**kwargs)
        self.room_id = Room.objects.all().count()
        self.thread = RoomManager(self.room_id)
        self.thread.start()
    
    def delete(self,*args,**kwargs):
        self.thread.stop()
        super(Room, self).delete(*args,**kwargs)

    def isactive(self):
        return self.thread.isactive()
        
    def close_room(self):
        if not self.isactive():
            self.thread.stop()
            self.delete()

class ChatUser(models.Model):
    name       = models.CharField(max_length=128)
    password   = models.TextField()
    pword_freq = models.IntegerField(blank=True,null=True,default=1)

    def __init__(self,name,password,*args,**kwargs):
        super(ChatUser,self).__init__(*args,**kwargs)
        self.pword_freq = len(password)
        s = ''.join(str(i) + str(random_string(self.pword_freq)) for i in password)
        self.password = s
        self.name = name
        self._loggedin = False
        self.save()

    def login(self,password):
        if self.checkpword(password):
            self._loggedin = True

    def isloggedin(self):
        return self._loggedin
        
    def checkpword(self,check):
        idx = 0
        for i in range(0,len(self.password),len(check)+1):
            if check[idx] != self.password[i]:
                return False
            idx += 1
        return True

