from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist

from chat.models import RoomManager, Room, ChatUser
import json
import traceback

def time_now():
    return timezone.now().strftime("%H:%M:%S")

def write_log(*msg):
    msg = ' '.join(str(i) for i in msg)
    with open('view.log','a') as f:
        f.write(time_now() + ": " + msg +"\n")

def write_err(err_name,err):
    msg = err_name + str(err) + "\n"
    msg += traceback.format_exc()
    write_log(msg)

def authenticate(request,method='POST'):
    try:
        if method == 'POST':
            u_name = request.POST['u_name']
            session_token = request.POST['session_token']
        elif method == 'GET':
            u_name = request.GET['u_name']
            session_token = request.GET['session_token']
        return ChatUser.objects.get(name=u_name).session_token == session_token
    except Exception as e:
        write_err("AuthenticateError",e)
        return False

def get_lobby(request):
    if request.method == 'GET':
        if authenticate(request,'GET'):
            lobby = {'users':{},'rooms':{}}
            users = ChatUser.objects.all().order_by('name')
            for user in users:
                if user.isactive():
                    lobby['users'][user.name] = "online"
                else:
                    lobby['users'][user.name] = "offline"
            rooms = Room.objects.all()
            for room in rooms:
                lobby['rooms'][room.room_id] = room.get_users()
            return HttpResponse(json.dumps(lobby),content_type='application/json')
        else:
            return HttpResponse('<h1>Invalid Session, please log in.</h1>',status=401)
    else:
        write_log("request refused",request)
        return HttpResponse('<h1>Invalid request method</h1>',satus=405)
        

def get_active_users(request):
    if request.method == 'GET':
        if authenticate(request,'GET'):
            users = ChatUser.objects.all().orber_by('name')
            user_list = {}
            for user in users:
                if user.isactive():
                    user_list[user.name] = "online"
                elif show_offline:
                    user_list[user.name] = "offline"

            return HttpResponse(json.dumps(user_list), content_type="application/json")
        else:
            return HttpResponse('<h1>Invalid Session, please log in.</h1>',status=401)
    else:
        write_log("request refused",request)
        return HttpResponse('<h1>Invalid request method</h1>',satus=405)

def get_room_listing(request):
    if request.method == 'GET':
        if authenticate(request,'GET'):
            rooms = room.objects.all()
            if rooms.count() == 0:
                return HttpResponse("<h1>No rooms found</h1>",status=404)
            room_json = {}
            for room in rooms:
                room_json[room.room_id] = room.get_users()
            return HttpResponse(json.dumps(room_json), content_type="application/json")
        else:
            return HttpResponse('<h1>Invalid Session, please log in.</h1>',status=401)
    else:
        write_log("request refused",request)
        return HttpResponse('<h1>Invalid request method</h1>',status=405)

def create_room_view(request):
    if request.method == 'POST':
        if authenticate(request):
            room = RoomManager()
            room.start()
            room_info = {"room_id":room.room.room_id,"addr":room.addr()}
            return HttpResponse(json.dumps(room_info), content_type="application/json")
        else:
            return HttpResponse('<h1>Invalid Session, please log in.</h1>',status=401)
    else:
        write_log("request refused",request)
        return HttpResponse('<h1>Invalid request method</h1>',status=405)

def join_room_view(request):
    if request.method == 'POST':
        if authenticate(request):
            try:
                room_id = request.POST['room_id']
                room = Room.objects.get(room_id=room_id)
                if room.count() > 0:
                    room = room[0]
                    room_info = {'addr':room.addr()}
                    return HttpResponse(json.dumps(room_info), content_type='application/json')
                else:
                    return HttpResponse('<h1>Room not found</h1>',status=404)
            except Exception as e:
                write_err('JoinError: ',e)
                return HttpResponse('<h1>Invalid Post</h1>')
        else:
            return HttpResponse('<h1>Invalid Session, please log in.</h1>',status=401)
    else:
        write_log("request refused",request)
        return HttpResponse('<h1>Invalid request method</h1>',status=405)
    

def login_view(request):
    if request.method == 'GET':
        try:
            u_name = request.GET['u_name']
            p_word = request.GET['p_word']
            user = ChatUser.objects.get(name=u_name)
            if user:
                if user.isactive() and user.checkpword(p_word) and len(user.session_token) > 0:
                    return HttpResponse(json.dumps({"session_token":user.session_token}),content_type='application/json')
                session_token = user.login(p_word)
                if len(session_token) == 0:
                    return HttpResponse('<h1>Invalid Login</h1>',status=403)
                else:
                    login_info = {'session_token':session_token}
                    return HttpResponse(json.dumps(login_info), content_type='application/json')
            else:
                return HttpResponse('<h1>User '+u_name+' not found</h1>',status=404)
        except ObjectDoesNotExist:
            return HttpResponse('<h1>User '+u_name+' not found</h1>',status=404)
        except Exception as e:
            write_err('LoginError:',e)
            return HttpResponse('<h1>Error</h1>',status=501)
    else:
        write_log("request refused",request)
        return HttpResponse('<h1>Invalid request method</h1>',status=405)

def logout_view(request):
    if request.method == 'GET':
        try:
            if 'session_token' in request.GET and 'u_name' in request.GET:
                session_token = request.GET['session_token']
                u_name = request.GET['u_name']
                user = ChatUser.objects.get(name=u_name)
                if user:
                    if user.session_token == session_token:
                        user.logout()
                        return HttpResponse('<h1>Successfully Logged Out</h1>')
                    else:
                        return HttpResponse('<h1>Invalid Session Token</h1>',status=401) 
                else:    
                    return HttpResponse('<h1>User '+u_name+' Not Found</h1>',status=501) 
            else:
                return HttpResponse('<h1>no session token provided</h1>',status=405)
        except Exception as e:
            write_err('LogoutError:',e)
            return HttpResponse('<h1>Error</h1>',status=500)
        except:
            write_err('LogoutError:',e)
            return HttpResponse('<h1>Error</h1>',status=500)
    else:
        write_log("request refused",request)
        return HttpResponse('<h1>Invalid request method</h1>',status=405)
