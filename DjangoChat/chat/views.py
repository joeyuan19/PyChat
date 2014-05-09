from django.shortcuts import render

# Create your views here.

import threading
from chat.models import Room, ChatUser

NEXT_ROOM_ID = 0



def time_now():
    import datetime
    return datetime.datetime.today().strftime("%H:%M:%S")

def write_log(*msg):
    msg = ' '.join(str(i) for i in msg)
    with open('view.log','a') as f:
        f.write(time_now() + ": " + msg +"\n")

def create_room_view(request):
    
    
def login_view(request):
    write_log('login',request.POST)

def destory_room_view(request)
    write_log('destroy',request.POST)


