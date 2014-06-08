import curses
import threading
import time
import random
import datetime
import getpass
import requests
import sys
import traceback
import re

# Debug functions

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

# Text Parsers

def parse_entry_to_fit(entry,width):
    remaining = entry
    split = []
    while len(remaining) > width:
        index = remaining[:width].rfind(' ')
        if index < 0:
            index = width
        split.append(remaining[:index].lstrip())
        remaining = remaining[index:]
    if len(remaining) > 0:
        split.append(remaining.lstrip())
    return split

# Get the dimensions of the window

def get_window_dims(window):
    return window.getmaxyx()

def getwindowyx(window=None):
    if window is None:
        return 0,0
    else:
        return get_window_dims(window)

# Functions to handle printing to the screen

def color_safe_addstr(window,y,x,s,c=None):
    if COLORS and c is not None:
        window.addstr(y,x,s,c)
    else:
        window.addstr(y,x,s)

def display_chat_log(window, log):
    h,w = getwindowyx(window)
    row = 0
    for entry in log[-h:]:
        # print the header and first line
        user_name = entry[0]
        if user_name == USER_NAME:
            color_safe_(window,row,0,user_name,get_curses_color(USER_COLOR_INDEX))
        else:
            color_safe_(window,row,0,user_name,curses.color_pair(2))
        header = " (" + entry[1] + ")" + ": "
        index = entry[2][:w-len(header)].rfind(" ")
        if index < 0 or len(entry[2][:w-len(header)]) < w:
            index = w - len(header)
        color_safe_(window,row,len(user_name),header + entry[2][:index])
        row += 1
        if row >= h:
            return
        for line in parse_entry_to_fit(entry[2][index:].strip(),w):
            color_safe_(window,row,0,line)
            row += 1
            if row >= h:
                return

def display_chat_msg(window,msg):
    h,w = getwindowyx(window)
    row = 1
    entry = ""
    for entry in parse_entry_to_fit(msg,w)[-h:]:
        color_safe_(window,row,0,entry)
        row += 1
        if row >= h-1:
            break
    if len(entry) >= w:
        x = 0
        y = row + 1
    elif row >= h-1:
        x = 0
        y = h - 1
    elif len(msg) == 0:
        x = 0
        y = 1
    else:
        x = len(entry)
        y = row
    curses.setsyx(y, x)

def display_div(window):
    h,w = getwindowyx(window)
    div = DIV_CHAR*(w/len(DIV_CHAR)) + DIV_CHAR[:w%len(DIV_CHAR)]
    color_safe_(window,0,0,div)

def get_mode_str(mde):
    if mde == MODE_INSERT:
        return "[Entry Field]"
    else:
        return "[Conversation Field]"

def get_shorthand_mode(mde):
    if mde == "Insert":
        return "[I]"
    else:
        return "[N]"

def fill_middle(msg,trailer,width):
    if len(msg + trailer) < width:
        return msg + " "*(width - len(msg + trailer)-1) + trailer
    return msg + trailer

def users_in_room():
    return "Connected to: " + ", ".join(i for i in USERS)

def disply_status(window,y,x,m,f=None):
    color_safe_addstr(window,y,x,m,f)
    
def display_status_msg(window,msg_info):
    h,w = getwindowyx(window)
    msg = msg_info[0] + " " + users_in_room()
    idx = msg_info[1]
    mde = get_mode_str(msg_info[2])
    
    const_info = " " + mde + " " + datetime.datetime.now().strftime("%H:%M:%S")
    eff_w = w - len(const_info) - 1
    if len(msg) > eff_w:
        idx = (idx +1)%len(msg)
        msg = (msg + "      " + msg + "      ")[idx:idx+eff_w-3] + "..."
    else:
        idx = -1
    msg = fill_middle(msg,const_info,w)
    write_log(msg)
    global status_msg
    status_msg = msg
    return idx

class StatusThread(threading.Thread):
    def __init__(self,window,status_msg,*args,**kwargs):
        super(StatusThread,self).__init__(*args,**kwargs)
        self.last_index = 0
        self.window = window
        self._stop = threading.Event()
        self.status_msg = status_msg
        self.mode = MODE_INSERT

    def run(self):
        while not self.isstopped():
            self.display()
            time.sleep(0.9)
            
    def display(self):
        self.last_index = display_status_msg(self.window,(self.status_msg,self.last_index,self.mode))
    
    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

class MessageThread(threading.Thread):
    RECV_SIZE = 2048
    def __init__(self,server_addr,client_addr,window,message_history=[],*args,**kwargs):
        super(MessageThread, self).__init__(*args,**kwargs)
        self.window = window
        self._stop = threading.Event()
        self.message_history = message_history
        self.partial_messages = []
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.connect(server_addr)
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.connect(client_addr)
        self.sockets = [self.server_socket, self.client_socket]
    
    def run(self):
        while not self.isstopped():
            r_sock,w_sock,e_sock = select.select(self.sockets,[],[])
            for sock in r_sock:
                if sock == self.server_socket:
                    try:
                        msg = sock.recv(2048)
                        self.process(msg)
                    except Exception as e:
                        write_log("ServerReadError:",e)
                        self.stop()
                        break
                else:
                    try:
                        msg = sock.recv(2048)
                        self.package_and_send(msg)
                    except Exception as e:
                        write_log("ClientReadError:",e)
                        self.stop()
                        break
        self.disconnect()
    
    def _process_partial_message(self,msg):
        pass

    def display(self):
        display_chat_log(self.window,self.message_history)

    def disconnect(self):
        self.server_socket.close()
        self.client_socket.close()

    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

    def process(self,msg):
        pass

    def package_and_send(self,msg):
        pass 

def get_user_action(window):
    ch = window.getch()
    if ch == 10:
        action = "send"
    elif ch == 127:
        action = "delr"
    elif ch > 256 or ch < 0:
        action = "pass"
    else:
        action = "type"
    return action,ch

def curses_init():
    window = curses.initscr()
    window.nodelay(1)
    window.keypad(1)
    curses.noecho()
    curses.cbreak()
    init_colors()
    return window

def init_colors():
    global COLORS
    COLORS = curses.can_change_color()
    if COLORS:
        curses.start_color()
        global USER_COLOR_INDEX
        USER_COLOR_INDEX = random.randint(1,6)

def get_color(idx):
    if idx == 0:
        return curses.COLOR_WHITE
    elif idx == 1:
        return curses.COLOR_YELLOW
    elif idx == 2:
        return curses.COLOR_CYAN
    elif idx == 3:
        return curses.COLOR_GREEN
    elif idx == 4:
        return curses.COLOR_BLUE
    elif idx == 5:
        return curses.COLOR_MAGENTA
    elif idx == 6:
        return curses.COLOR_RED
    elif idx == 7:
        return curses.COLOR_BLACK

def get_curses_color(idx):
    global COLORS
    if not COLORS:
        return -1
    return curses.color_pair(idx)

def split_window(window,ratio=0.75):
    height,width = getwindowyx(window)
    larger = int(round(ratio*height))
    log = window.derwin(larger,width,0,0)
    chat = window.derwin(height-larger-1,width,larger,0)
    status = window.derwin(height-1,0)
    return log, chat, status

# URL HANDLING

def urlopen(url,method='GET',params=None,timeout=2.0):
    res = None
    if params is not None:
        res = requests.request(method,url,data=params,params=params,timeout=timeout)
    else:
        res = requests.request(method,url,timeout=timeout)
    return res

def login(u_name,p_word,server='127.0.0.1:8000'):
    # GET http://127.0.0.1:8000/login/?u_name=<username>&p_word=<password>
    return urlopen(
        "http://"+server+"/login/",
        method='GET',
        params={"u_name":u_name,"p_word":p_word}
    )

def get_room_list(u_name,session_token,server='127.0.0.1:8000'):
    # GET http://<server>/room_list/?u_name=<username>&session_token=<session token>
    return urlopen(
        "http://"+server+"/room_list/",
        method='GET',
        params={"u_name":u_name,"session_token":sesion_token}
    )

def get_user_list(u_name,session_token,server='127.0.0.1:8000'):
    # GET http://<server>/user_list/?u_name=<username>&session_token=<session token>
    return urlopen(
        "http://"+server+"/user_list/",
        method='GET',
        params={"u_name":u_name,"session_token":session_token}
    )

def get_lobby(u_name,session_token,server='127.0.0.1:8000'):
    # GET http://<server>/lobby/?u_name=<username>&session_token=<session token>
    return urlopen(
        "http://"+server+"/lobby/",
        method='GET',
        params={"u_name":u_name,"session_token":session_token}
    )

def create(u_name,session_token,server='127.0.0.1:8000'):
    # POST http://<server>/create_room/?u_name=<username>&session_token=<session token>
    return urlopen(
        "http://"+server+"/room_create/",
        method='POST',
        params={"u_name":u_name,"session_token":session_token}
    )

def join(u_name,session_token,room_id,server='127.0.0.1:8000'):
    # POST http://<server>/join/?u_name=<username>&room_id=<room id>&session_token=<session token>
    return urlopen(
        "http://"+server+"/join/",
        method='POST',
        params={"u_name":u_name,"session_token":session_token,"room_id":room_id}
    )
    
def logout(u_name,session_token,server='127.0.0.1:8000'):
    # POST http://<server>/logout/?u_name=<username>&session_token=<session token>
    return urlopen(
        "http://"+server+"/logout/",
        method='GET',
        params={"u_name":u_name,"session_token":session_token}
    )

def strip_headers(msg):
    matches = re.findall(r'<h1>(.*?)</h1>',msg)
    if len(matches) == 0:
        return msg
    else:
        return matches[0]
    

SESSION_TOKEN = ''
status_thread = None
message_thread = None
COLORS = False
USER_COLOR_INDEX = 1
DIV_CHAR = "*^"
USER_NAME = "Joe"
USERS = [USER_NAME]
COLOR_PAIRS = [
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

status_msg = ""
chat_msg = ""
chat_log = []

LAST_COLOR_INDEX = -1

# Style info

MODE_INSERT = 0
SESSION_TOKEN = ''
USER_NAME = ''
CONNECTION_SPEED = 2.0


print "\n\n\nWelcome to PyChat!"
code = -1
attempt = 0
while True:
    print "Please login:"
    u_name = raw_input("Username: ")
    p_word = getpass.getpass()

    res = None
    try:
        res = login(u_name,p_word)
        code = res.status_code
    except Exception as e:
        write_err(e)
    
    if code == 200:
        print "Welcome " + u_name + "!"
        _json = res.json()
        SESSION_TOKEN = _json['session_token']
        USER_NAME = u_name
        break
    else:
        print "Error",code,strip_headers(res.text)
        attempt += 1

    if attempt == 3:
        print "Three failed attempts in a row, exiting..."
        sys.exit()


SHOW_OFFLINE = False


try:
    while True:
        res = get_lobby(USER_NAME,SESSION_TOKEN)
        code = res.status_code
        options = {}

        out = ''
        if code != 200:
            out = "Error " + str(code) + ": " + strip_headers(res.text)
            print out
            sys.exit()
        else:
            _json = res.json()
            out += "Rooms:\n"
            for room_id,occ in _json["rooms"].iteritems():
                out += "<"+str(len(option))+" > Room"+str(room_id)+":"+occ+"\n"
                options[len(options)] = "room:" + str(room_id)
            out += "\n"
            out += "Users\n"
            for username,status in _json["users"].iteritems():
                if status == 'online':
                    out += "<"+str(len(options))+"> "+username+" " + status + "\n"
                    options[len(options)] = "user:" + username
                elif SHOW_OFFLINE and status == 'offline':
                    out += "<"+str(len(options))+"> "+username+" "+status+"\n"
                    options[len(options)] = username
            out += "\n\n"
            if SHOW_OFFLINE:
                out += "<"+str(len(options))+"> Hide offline\n"
            else:
                out += "<"+str(len(options))+"> Show offline\n"
            options[len(options)] = "toggle_offline"
            out += "<"+str(len(options))+"> Logout\n"
            options[len(options)] = "_logout"
            out += "<"+str(len(options))+"> Refresh Lobby\n"
            options[len(options)] = "_refresh"

            out += "\n\nSelect which chat room you would like to join\n"
            out += "or which user you would like to chat with\n"
            out += "enter the choice number in the brackets <###>\n"
            print out
        
            choice = raw_input('Choice: ')

            try:
                if len(choice) > 0:
                    idx = int(choice.strip())
                    action = options[int(choice.strip())]
                    if action == "_logout":
                        res = logout(USER_NAME,SESSION_TOKEN)
                        if res.status_code == 200:
                            print "Logged out. See ya!"
                            sys.exit()
                        else:
                            print "Logout failed, sorry you must stay!!!!"
                    elif action == "toggle_offline":
                        SHOW_OFFLINE = not SHOW_OFFLINE
                    elif action == "_refresh":
                        continue
                    elif action == "_create":
                        res = create(USER_NAME,SESSION_TOKEN)
                        print res
            except ValueError as e:
                print choice + " is an invalid Choice"
            except Exception as e:
                print e
except Exception as e:
    write_err(e)
    print e, traceback.format_exc()
    sys.exit()
finally:
    res = logout(USER_NAME,SESSION_TOKEN)
    if res.status_code != 200:
        print "Server error",res.status_code,", user not successfully logged out.  No action required, this has been logged, you will be logged out when your session expires."

def run_chat_room(addr):
    try:
        window = curses_init()
        log, chat, status = split_window(window)

        log.leaveok(1)
        status.leaveok(1)

        # Status Handler
        status_thread = StatusThread(status,status_msg)
        status_thread.start()

        # Message Send/Receive
        message_thread = MessageThread(addr)
        message_thread.start()

        while True:
            # Log Display
            log.erase()
            display_chat_log(log,chat_log)
            log.refresh()

            status.erase()
            display_status(status,0,0,status_msg)
            status.refresh()

            # Message Prep Display
            chat.erase()
            display_div(chat)
            display_chat_msg(chat,chat_msg)
            chat.refresh()
            action,c = get_user_action(window)
            if action == "send":
                chat_log.append((USERS[0],"derp o'clock",chat_msg.strip()))
                chat_msg = ""
            elif action == "delr":
                chat_msg = chat_msg[:-1]
            elif action == "type":
                chat_msg += str(chr(c))
        curses.endwin()
        status_thread.stop()
    except KeyboardInterrupt:
        if curses:
            curses.endwin()
        if status_thread:
            status_thread.stop()
    finally:
        if curses:
            curses.endwin()
        if status_thread:
            status_thread.stop()
    status_thread.stop()
