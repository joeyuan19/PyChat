from django.db import models
import random

GOOD_COLOR_PAIRS = [
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

def random_char():
    r = random.choice(range(33,95)+range(96,127))
    return chr(r)

def random_string(n):
    s = ""
    for i in range(n):
        s += random_char()
    return s


class RoomManager(threading.Thread):
    def __init__(self,name,receive_channel,send_channel,*args,**kwargs):
        super(RoomThread,self).__init__(*args,**kwargs)
        self._stop = threading.Event()
        self.room = Room()
        self.req_queue = []
        self.receive_channel = receive_channel
        self.send_channel = send_channel
    
    def stop(self):
        self._stop.set()
    
    def isstopped(self):
        return self._stop.isSet()
    
    def run(self):
        while not isstopped():
            req = self.next_req()
            if req is not None:
                self.process(req)
        room.disconnect()
    
    def next_req(self):
        if len(self.req_queue) > 0:
            return self.req_queue.pop(0)
        else:
            return None
    
    def process(self,req):
        if req["type"] == "msg":
            room.post_message(req["msg"])
        elif req["type"] == "join":
            room.join_user(req["user"])
        elif req["type"] == "leave":
            room.leave_user(req["user"])

    def add(self,req):
        self.req_queue.append(req)

NEXT_ROOM_ID = 0

class Room(models.Model):
    room_id = models.IntegerField()
    
    def __init__(self,name,*args,**kwargs):
        super(Room, self).__init__(*args,**kwargs)
        self.users = {}
        self.name = name
        self.room_id = NEXT_ROOM_ID
        self.thread = RoomManager(self.name,NEXT_ROOM_ID,5000+NEXT_ROOM_ID,5000+NEXT_ROOM_ID+1)
        self.thread.start()
    
    def delete(self,*args,**kwargs):
        self.thread.stop()
    
    def join_user(self,user):
        users.append(user)

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

    def checkpword(self,check):
        if len(check) != self.pword_freq:
            return False
        idx = 0
        for i in range(0,len(self.password),self.pword_freq+1):
            if check[idx] != self.password[i]:
                return False
            idx += 1
        return True

