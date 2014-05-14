from django.shortcuts import render
from django.http import HttpResponse
from chat.models import Room, ChatUser

def time_now():
    import datetime
    return datetime.datetime.today().strftime("%H:%M:%S")

def write_log(*msg):
    msg = ' '.join(str(i) for i in msg)
    with open('view.log','a') as f:
        f.write(time_now() + ": " + msg +"\n")

def get_active_users(request):
    users = ChatUser.objects.all().orber_by('name')
    user_list = ""
    show_offline = False
    for user in users:
        if user.isactive():
            user_list += user.name + "is online<br>"
        elif show_offline:
            user_list += user.name + "is offline<br>"
    return HttpResponse(user_list)
    
def create_room_view(request):
    write_log('',request.POST)
    
def login_view(request):
    write_log('login',request.POST)

def destory_room_view(request)
    write_log('destroy',request.POST)


