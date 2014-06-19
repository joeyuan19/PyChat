import re
import sys
import time
import curses
import random
import socket
import getpass
import datetime
import requests
import threading
import traceback

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

def join_messages(msgs):
    _msg = {
        "body":"",
        "name":"",
        "time":"",
        "frmt":[]
    }
    for msg in msgs:
        _msg["body"] += msg["body"]
        _msg["frmt"] += msg["frmt"]
    _msg["name"] = msg["name"]
    _msg["time"] = msg["frmt"]
    return _msg

def serialize(_json):
    return json.dumps(_json,separator=(",",":"))


class StatusThread(threading.Thread):
    def __init__(self,manager,window,status_msg,*args,**kwargs):
        super(StatusThread,self).__init__(*args,**kwargs)
        self.last_index = 0
        self.manager = manager
        self._stop = threading.Event()

    def run(self):
        while not self.isstopped():
            self.display()
            time.sleep(0.9)
            
    def display(self):
        self.last_index = manager.display_status_msg(self.last_index)
    
    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

class MessageThread(threading.Thread):
    RECV_SIZE = 4096
    def __init__(self,manager,window,server_addr,client_addr,*args,**kwargs):
        super(MessageThread, self).__init__(*args,**kwargs)
        self.window = window
        self.manager = manager
        self._stop = threading.Event()
        self.partial_messages = []
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.connect(server_addr)
        _json = {
            "verb":"join",
            "name":manager.USER_NAME,
            "sess":manager.SESSION_TOKEN
        }
        join_request = serialize(_json) 
        self.server_socket.send(join_request)
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client_socket.connect(client_addr)
        self.sockets = [self.server_socket]
    
    def run(self):
        while not self.isstopped():
            self.display()
            r_sock,w_sock,e_sock = select.select(self.sockets,[],[])
            for sock in r_sock:
                if sock == self.server_socket:
                    try:
                        msg = sock.recv(self.RECV_SIZE)
                        self.process(msg)
                    except Exception as e:
                        write_log("ServerReadError:",e)
                        self.stop()
                        break
            _next = self.get_next_msg()
            if _next is not None:
                self.server_socket.send(_next)
        self.disconnect()
    
    def _process_partial_message(self,msg):
        for partial_message in self.partial_messages:
            if msg["mgid"] == partial_message[0]["mgid"]:
                partial_message.append(msg["mgid"])
                if len(partial_message) == msg["totl"]:
                    manager.add_msg(join_messages(partial_message))
                    self.partial_messages.remove(partial_message)
                return
        self.partial_messages.append([msg])

    def display(self):
        manager.display_chat_log()

    def disconnect(self):
        self.server_socket.close()
        self.client_socket.close()

    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

    def process(self,msg):
        if msg["verb"] == "msg":
            if msg["totl"] > 1:
                self._process_partial_message(msg)
            manager.add_msg(msg)
        elif msg["verb"] == "join":
            manager.add_user("verb")

def split_window(window,ratio=0.75):
    height,width = getwindowyx(window)
    larger = int(round(ratio*height))
    log = window.derwin(larger,width,0,0)
    chat = window.derwin(height-larger-1,width,larger,0)
    status = window.derwin(height-1,0)
    return log, chat, status


class ChatDisplayManager(object):
    status_thread = None
    message_thread = None
    window = None
    log = None
    status = None
    chat = None
    HAS_COLORS = False
    CAN_CHANGE_COLORS = False
    USER_COLOR_INDEX = (-1,-1)
    DIV_CHAR = "="
    USER_NAME = ""
    USERS = []
    DEFAULT_BACKGROUND = 7
    DEFAULT_FOREGROUND = 0
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

    COLOR_INDEX = {
        0: curses.COLOR_WHITE,
        1: curses.COLOR_YELLOW,
        2: curses.COLOR_CYAN,
        3: curses.COLOR_GREEN,
        4: curses.COLOR_BLUE,
        5: curses.COLOR_MAGENTA,
        6: curses.COLOR_RED,
        7: curses.COLOR_BLACK,
    }
    status_msg = ""
    chat_msg = ""
    chat_log = []

    def curses_init():
        self.window = curses.initscr()
        self.window.nodelay(1)
        self.window.keypad(1)
        curses.noecho()
        curses.cbreak()
        init_colors()
    
    def init_colors():
        self.HAS_COLORS = curses.has_colors()
        self.CAN_CHANGE_COLOR = curses.can_change_colors()
        if self.COLORS:
            curses.start_color()
    
    def addstr(window,y,x,string,formatting=None):
        if formatting is None or not self.HAS_COLORS:
            self._addstr(window,y,x,string)
        else:
            last = (0,0,-1,-1)
            for _format in formatting:
                _string = string[last[1]:_format[1]]
                self._addstr(window,y,x+last[1],_string,(_format[3],_format[4]))
                last = _format
            _string = string[last[1]:_format[1]]
            self._addstr(window,y,x+last[1],_string)
            
    
    def _addstr(window,y,x,s,c=None):
        if self.HAS_COLORS and c is not None:
            curses.init_pair(1,self.COLOR_INDEX[c[0]],self.COLOR_INDEX[c[1]])
            window.addstr(y,x,s,curses.color_pair(1))
        else:
            window.addstr(y,x,s)
            
    def display_status_msg(self,idx):
        h,w = getwindowyx(self.status)
        msg = self.get_status() + " " + self.users_in_room()
        const_info = " " + datetime.datetime.now().strftime("%H:%M:%S")
        if len(const_info) > w:
            const_info = datetime.datetime.now().strftime("%H:%M:%S")
        eff_w = w - len(const_info) - 1
        if len(msg) > eff_w:
            idx = (idx +1)%len(msg)
            msg = (msg + "      " + msg + "      ")[idx:idx+eff_w-3] + "..."
        else:
            idx = -1
        msg = fill_middle(msg,const_info,w)
        self.addstr(self.status,0,0,msg)
        return idx
    
    def display_chat_log(self):
        window = self.log
        log = self.chat_log
        h,w = getwindowyx(window)
        row = 0
        for entry in log[-h:]:
            # print the header and first line
            if True:
                self.addstr(window,row,0,user_name)
            else:
                self.addstr(window,row,0,user_name)
            header = " (" + entry[1] + ")" + ": "
            index = entry[2][:w-len(header)].rfind(" ")
            if index < 0 or len(entry[2][:w-len(header)]) < w:
                index = w - len(header)
            self.addstr(window,row,len(user_name),header + entry[2][:index])
            row += 1
            if row >= h:
                return
            for line in parse_entry_to_fit(entry[2][index:].strip(),w):
                self.addstr(window,row,0,line)
                row += 1
                if row >= h:
                    return

    def display_div(window):
        h,w = getwindowyx(window)
        div = DIV_CHAR*(w/len(DIV_CHAR)) + DIV_CHAR[:w%len(DIV_CHAR)]
        color_safe_(window,0,0,div)
    
    def display_chat_msg():
        window = self.chat
        msg = self.chat_msg
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

    def users_in_room(self):
        return "Connected to: " + ", ".join(i for i in self.USERS)

    def get_colors(self,c):
        if c[0] < 0:
            c[0]  = self.DEFAULT_FOREGROUND
        if c[1] < 0:
            c[1]  = self.DEFAULT_BACKGROUND
        return self.COLOR_INDEX[c[0]],self.COLOR_INDEX[c[1]]

    def get_color(idx):
        if not self.HAS_COLORS:
            return -1
        return self.COLOR_INDEX[idx]
    
    def resize_handler(self,n,frame):
        curses.endwin()
        self.window = curses.initscr()
        self.log, self.chat, self.status = split_window(self.window)
        
    def get_user_action(self):
        ch = self.window.getch()
        if ch == 10:
            action = "send"
        elif ch == 127:
            action = "delr"
        elif ch > 256 or ch < 0:
            action = "pass"
        else:
            action = "type"
        return action,ch

    def send(self):
        self.message_thread.send(self.chat_msg.strip())
        self.chat_msg = ""

    def run_chat_room(self,server_address):
        try:
            self.curses_init()
            self.log, self.chat, self.status = split_window(self.window)

            signal.signal(signal.SIGWINCH,self.resize_handler)
            
            self.log.leaveok(1)
            self.status.leaveok(1)

            # Status Handler
            self.status_thread = StatusThread(status,self.status_msg)
            self.status_thread.start()

            self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.sock.bind(("localhost",0))
            
            # Message Send/Receive
            self.message_thread = MessageThread(log,server_address,self.sock.getsockname())
            self.message_thread.start()

            while True:
                # Log Display
                self.log.erase()
                self.display_chat_log()
                self.log.refresh()

                self.status.erase()
                self.display_status()
                self.status.refresh()

                # Message Prep Display
                self.chat.erase()
                display_div(chat)
                display_chat_msg()
                self.chat.refresh()
                action,c = self.get_user_action()
                if action == "send":
                    self.send()
                elif action == "delr":
                    self.chat_msg = chat_msg[:-1]
                elif action == "type":
                    self.chat_msg += str(chr(c))
            curses.endwin()
            self.status_thread.stop()
            self.message_thread.stop()
        except KeyboardInterrupt:
            if curses:
                curses.endwin()
            if status_thread is not None:
                status_thread.stop()
            if message_thread is not None:
                message_thread.stop()
        finally:
            if curses:
                curses.endwin()
            if message_thread is not None:
                message_thread.stop()
            if status_thread is not None:
                status_thread.stop()
