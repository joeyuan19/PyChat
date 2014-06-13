from django.db import models
from django.utils import timezone

import re
import time
import random
import select
import socket
import datetime
import threading


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
# To Do:
#    [ ] Make it work
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
        f.write(date_now() + " " + time_now() + "# " + msg + "\n") 

def write_log(*args):
    msg = ""
    for arg in args:
        msg += str(arg) + " "
    msg = msg[:-1]
    with open("chat_app.log","a") as f:
        f.write(date_now() + " " + time_now() + "# " + msg + "\n") 

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
    exp = r'<m>.*?</m>'
    m = re.findall(exp, block, re.S)
    return [parse_msg(i) for i in m]

def parse_msg(msg):
    exp = r'<b>(.*)</b><d>(.*?)</d><u>(.*?)</u><f>(.*?)</f><c>(\d+/\d+)</c>'
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
        print "create"
        self._stop = threading.Event()
        self.host = 'localhost'
        # set up sever socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.server_socket.bind(('localhost',0))
        self.server_socket.listen(self.CONNECT_LIMIT)
        # Initiate Socket List
        self.sockets = [(self.server_socket,None)]
        self.msg_queue = []
        self.user_color = {}
        self.mark_as_empty = None
        self.room = Room.create()
        self.room.save()
        super(RoomManager,self).__init__(*args,**kwargs)
        self.setDaemon(True)
        self.start()
        print "Thread started"
        for _t in threading.enumerate():
            print "thread",_t
            print "ident",_t.ident
            print "name",_t.name

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
        self.room.set_thread(self)
        while not self.isstopped() and self.isactive():
            rsockets, wsockets, errsockets = select.select([sock for sock,user in self.sockets],[],[])
            for sock in rsockets:
                if sock == self.server_socket:
                    new_conn, new_addr = sock.accept()
                    user = new_conn.recv(64)
                    if not user:
                        self.connect_user(user, new_conn)
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

    def package_and_broadcast(self,msg="",u_name="",formatting=""):
        msg = "<m><b>"+str(msg)+"</b><u>"+str(u_name)+"</u><d>"+full_date()+"</d><f>"+str(formatting)+"</f><c>1/1</c></m>"
        self.broadcast(msg)
    
    def broadcast(self,msg):
        for sock,user in self.sockets:
            if sock != self.server_sock:
                try:
                    sock.send(msg)
                except:
                    self.disconnect_user(sock=sock)

    def connect_user(self,u_name,sock):
        user = Users.objects.get(name=u_name)
        if user.count() == 0:
            sock.close()
        else:
            user = user[0]
            if user.isactive():
                self.sockets.append((sock,user))
                self.user_color[self.get_new_color()] = user
                self.package_and_broadcast(msg=user.name+" has entered the room...")
            else:
                sock.close()
        
    def get_users(self):
        return ', '.join(user.name for sock,user in self.sockets if sock != self.server_socket)

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
#        if self.mark_as_empty is None:
#            if len(self.sockets) <= 1:
#                self.mark_as_empty = timezone.now()
#        else:
#            return timezone.now() - self.mark_as_empty >= 

class Room(models.Model):
    room_id = models.IntegerField(default=0,null=True,blank=True)
    thread_name = models.CharField(max_length=64,null=True,blank=True)
    thread_ident = models.IntegerField(default=-1)
    thread_addr_server = models.CharField(max_length=128,default="")
    thread_addr_port = models.IntegerField(default=0)
    
    @classmethod
    def create(cls,*args,**kwargs):
        room = cls(*args,**kwargs)
        room.room_id = Room.objects.all().count()
        return room
    
    def set_thread(self,thread):
        self.thread_name = thread.name
        self.thread_ident = thread.ident
        addr = thread.server_socket.getsockname()
        self.thread_addr_server = addr[0]
        self.thread_addr_port = addr[1]
        self.save()
    
    def get_id(self):
        return self.room_id
    
    def get_name(self):
        return self.thread_name
    
    def delete(self,*args,**kwargs):
        self.thread.stop()
        super(Room, self).delete(*args,**kwargs)
    
    def addr(self):
        return self.thread().addr()

    def isactive(self):
        return True
    
    def user_list(self):
        return self.get_users()

    def thread(self):
        _thread = None
        for thread in threading.enumerate():
            if thread.ident == self.thread_ident:
                _thread = thread
                break
        return _thread
    
    def delete(self,*args,**kwargs):
        self.close_room()
        super(Room, self).delete(*args,**kwargs)

    def get_users(self):
        _thread = self.thread()
        if _thread is None:
            return ''
        return _thread.get_users()
    
    def close_room(self):
        self.thread().stop()
        self.delete()

class ChatUser(models.Model):
    name = models.CharField(max_length=64)
    password = models.TextField(default="",blank=True,null=True)
    pword_freq = models.IntegerField(default=0)
    session_token = models.CharField(max_length=16,default="")
    loggedin = models.BooleanField(default=False)
    
    @classmethod
    def create(cls,*args,**kwargs):
        if len(str(kwargs['name'])) == 0 or len(str(kwargs['password'])) == 0: return
        password = kwargs['password']
        name = kwargs['name']
        new_user = cls(*args,**kwargs)
        new_user.name = name
        new_user.pword_freq = len(password)
        new_user.password = ''.join(str(i) + str(random_string(new_user.pword_freq)) for i in password)
        new_user.loggedin = False
        new_user.session_token = ''
        return new_user

    def login(self,password):
        if self.checkpword(password):
            self.loggedin = True
            self.session_token = random_string(16)
            self.last_seen = timezone.now()
            self.save()
            return self.session_token
        else:
            return ''

    def logout(self):
        if self.loggedin:
            self.loggedin = False
            self.session_token = ''
            self.save()
            return True
        else:
            return False
    
    def isactive(self):
        return self.loggedin
    
    def checkpword(self,check):
        if self.pword_freq > 0 and len(check) != self.pword_freq:
            return False
        idx = 0
        for i in range(0,len(self.password),len(check)+1):
            if check[idx] != self.password[i]:
                return False
            idx += 1
        return True

    def clear_read_notifications(self):
        for msg in self.notification_set.all():
            if not msg.unread():
                msg.delete()

