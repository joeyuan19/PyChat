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

# Functions to handle printing to the screen



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
    def __init__(self,manager,window,status_msg,*args,**kwargs):
        super(StatusThread,self).__init__(*args,**kwargs)
        self.last_index = 0
        self.window = window
        self.manager = manager
        self._stop = threading.Event()
        self.status_msg = status_msg
        self.mode = MODE_INSERT

    def run(self):
        while not self.isstopped():
            self.display()
            time.sleep(0.9)
            
    def display(self):
        self.last_index = manager.display_status_msg(self.window,(self.status_msg,self.last_index,self.mode))
    
    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

class MessageThread(threading.Thread):
    RECV_SIZE = 2048
    def __init__(self,manager,window,server_addr,client_addr=('localhost',0),message_history=[],*args,**kwargs):
        super(MessageThread, self).__init__(*args,**kwargs)
        self.window = window
        self.manager = manager
        self._stop = threading.Event()
        self.message_history = message_history
        self.partial_messages = []
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.connect(server_addr)
        self.server_socket.send(USER_NAME)
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client_socket.connect(client_addr)
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
        manager.display_chat_log(self.window,self.message_history)

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
    HAS_COLORS = False
    CAN_CHANGE_COLORS = False
    USER_COLOR_INDEX = (-1,-1)
    DIV_CHAR = "="
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
        window = curses.initscr()
        window.nodelay(1)
        window.keypad(1)
        curses.noecho()
        curses.cbreak()
        init_colors()
        return window
    
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
    
    def _addstr(window,y,x,s,c=None):
        if self.HAS_COLORS and c is not None:
            if c[0] < 0 or c[1] < 0:
            
            else:
                curses.init_pair(1,self.COLOR_INDEX[c[0]],self.COLOR_INDEX[c[1]])
                window.addstr(y,x,s,curses.color_pair(1))
        else:
            window.addstr(y,x,s)
        
    def get_color(idx):
        if not self.HAS_COLORS:
            return -1
        return self.COLOR_INDEX[idx]
        
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

    def run_chat_room(self,addr):
        try:
            window = self.curses_init()
            log, chat, status = split_window(window)

            log.leaveok(1)
            status.leaveok(1)

            # Status Handler
            status_thread = StatusThread(status,self.status_msg)
            status_thread.start()

            # Message Send/Receive
            message_thread = MessageThread(log,addr)
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
                action,c = self.get_user_action(window)
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

