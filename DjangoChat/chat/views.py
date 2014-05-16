from django.shortcuts import render
from djano.utils import timezone
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from chat.models import RoomManger, Room, ChatUser
import json


def time_now():
    return timezone.now().strftime("%H:%M:%S")

def write_log(*msg):
    msg = ' '.join(str(i) for i in msg)
    with open('view.log','a') as f:
        f.write(time_now() + ": " + msg +"\n")

def authenticate(u_name,session_token):
    return ChatUser.objects.get(name=U_name)[0].session_token == session_token

def get_active_users(request):
    if request.method == 'GET':
        if request.post['session_token'] and authenticate(request.post['session_token']):
            users = ChatUser.objects.all().orber_by('name')
            user_list = {}
            for user in users:
                if user.isactive():
                    user_list[user.name] = "online"
                elif show_offline:
                    user_list[user.name] = "offline"
            return HttpResponse(json.dumps(user_list), content_type="application/json")
        else:
            return HttpResponseForbidden('<h1>Invalid session token, please log in.</h1>')
    else:
        return HttpResponseNotFound('<h1>Invalid request method</h1>')

def get_room_listing(request):
    if request.method == 'GET':
        if request.POST['session_token'] and authenticate(request.POST['session_token']):
            rooms = room.objects.all()
            room_json = {}
            for room in rooms:
                room_json[room.room_id] = room.get_users()
            return HttpResponse(json.dumps(room_json), content_type="application/json")
        else:
            return HttpResponseForbidden('<h1>Invalid session token, please log in.</h1>')
    else:
        return HttpResponseNotFound('<h1>Invalid request method</h1>')

def create_room_view(request):
    if request.method == 'POST':
        if request.POST['session_token'] and authenticate(request.POST['session_token']):
            room = RoomManager()
            room.start()
            room_info = {"room_id":room.room.room_id,"addr",room.add()}
            return HttpResonse(json.dumps(room_info), content_type="application/json")
        else:
            return HttpResponseForbidden('<h1>Invalid Session token, please log in.</h1>')
    else:
        return HttpResponseNotFound('<h1>Invalid request method</h1>')

def join_room_view(request):
    if request.method == 'POST':
        if request.POST['session_token'] and authenticate(request.POST['session_token']):
            try:
                room_id = request.POST['room_id']
                room = Room.objects.get(room_id=room_id)
                if room.count() > 0:
                    room = room[0]
                    room_info = {'addr':room.addr()}
                    return HttpResponse(json.dumps(room_info), content_type='application/json')
                else:
                    return HttpResponseNotFound('<h1>Room not found</h1>')
            except Exception as e:
                write_log('join error: ',e)
                return HttpResponse('<h1>Invalid Post</h1>')
                
        else:
            return HttpResponseForbidden('<h1>Invalid Session token, please log in.</h1>')
    else:
        return HttpResponseNotFound('<h1>Invalid request method</h1>')
    

def login_view(request):
    if request.method == 'POST':
        try:
            u_name = request.POST['u_name']
            p_word = request.POST['p_word']
            user = ChatUser.objects.get(name=u_name)
            if user.count() > 0:
                user = user[0]
                user
        except Exception as e:
            write_log('LoginError:',e)
    else:
        return HttpResponseNotFound('<h1>Invalid request method</h1>')
    
