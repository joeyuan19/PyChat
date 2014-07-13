import sys
import time
import json
import curses
import signal
import datetime
import threading
import traceback
import mosquitto

# To Do
# 1. Make it work
# 2. Add formatting
# 3. code snippets
# 4. ASCII image sharing


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

def time_now():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

def time_to_display(s):
    return datetime.datetime.now().strptime(s,"%Y%m%d%H%M%S%f").strftime("%H:%M:%S")

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

def sort_on_index(msgs):
    temp = [i for i in msgs]
    while True:
        swap = False
        for i in range(len(temp)-1):
            if temp[i]["idx"] > temp[i+1]["idx"]:
                _temp = temp[i]
                temp[i] = temp[i+1]
                temp[i+1] = _temp
                swap = True
        if not swap:
            return temp

            
def join_messages(msgs):
    _msg = {
        "body":"",
        "name":"",
        "time":"",
        "frmt":[]
    }
    msgs = sort_on_index(msgs)
    for msg in msgs:
        _msg["body"] += msg["body"]
        _msg["frmt"] += msg["frmt"]
    _msg["name"] = msg["name"]
    _msg["time"] = msg["time"]
    return _msg

def serialize(_json):
    return json.dumps(_json,separators=(",",":"))

def deserialize(_json):
    try:
        return json.loads(_json)
    except:
        write_log("JSONDecodeERROR:",_json,"\n",traceback.format_exc())

class StatusThread(threading.Thread):
    def __init__(self,manager,*args,**kwargs):
        super(StatusThread,self).__init__(*args,**kwargs)
        self.last_index = 0
        self.manager = manager
        self._stop = threading.Event()
        self.setDaemon(True)

    def run(self):
        while not self.isstopped():
            self.update_display()
            time.sleep(0.9)
            
    def update_display(self):
        h,w = getwindowyx(self.manager.status)
        msg = ""
        u_list,frmt = self.manager.users_in_room()
        msg += u_list
        const_info = " " + datetime.datetime.now().strftime("%H:%M:%S")
        eff_w = w - len(const_info) - 1
        if len(msg) > eff_w:
            idx = (idx +1)%len(msg)
            msg = (msg + "      " + msg + "      ")[idx:idx+eff_w-3] + "..."
        else:
            idx = -1
        self.manager.status_msg = fill_middle(msg,const_info,w)
        self.last_index = idx

    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

def split_window(window,ratio=0.75):
    height,width = getwindowyx(window)
    larger = int(round(ratio*height))
    log = window.derwin(larger,width,0,0)
    chat = window.derwin(height-larger-1,width,larger,0)
    status = window.derwin(height-1,0)
    return log, chat, status


class ChatDisplayManager(object):
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
    
    def __init__(self,session_token,username):
        self.status = ""
        self.status_msg = ""
        self.chat_msg = ""
        self.chat_log = []
        self.window = None
        self.log = None
        self.status = None
        self.chat = None
        self.HAS_COLORS = False
        self.CAN_CHANGE_COLORS = False
        self.USER_FORMAT = (-1,-1)
        self.DIV_CHAR = "="
        self.USER_NAME = ""
        self.USERS = []
        self.SESSION_TOKEN = session_token
        self.USER_NAME = username
        self.client = mosquitto.Mosquitto(username)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        # local
        #self.client.connect("127.0.0.1",port=1883)
        # server
        self.client.connect("184.154.221.154",port=1883)


    def on_connect(self, mosq, obj, rc):
        if rc != 0:
            raise Exception("Connection failed")
        else:
            self.client.subscribe("room/1")
            self.client.will_set("room/1",self.USER_NAME+" lost connection...",1)
            time_stamp = time_now()
            _msg = {
                "verb":"join",
                "msg":"",
                "frmt":[],
                "time":time_stamp,
                "name":self.USER_NAME
            }
            self.client.publish("room/1",serialize(_msg),1)

    def on_message(self, mosq, obj, msg):
        msg = deserialize(msg.payload)
        self.add_msg(msg)
   
    def disconnect(self):
        time_stamp = time_now()
        _msg = {
            "verb":"leave",
            "msg":"",
            "frmt":[],
            "time":time_stamp,
            "name":self.USER_NAME
        }
        self.client.publish("room/1",serialize(_msg),1)
        self.client.unsubscribe("room/1")
        self.client.disconnect()

    def on_disconnect(self, mosq, obj, rc):
        pass

    def curses_init(self):
        self.window = curses.initscr()
        self.window.nodelay(1)
        self.window.keypad(1)
        curses.noecho()
        curses.cbreak()
        self.init_colors()
        self.log, self.chat, self.status = split_window(self.window)
        signal.signal(signal.SIGWINCH,self.resize_handler)
        self.log.leaveok(1)
        self.status.leaveok(1)

    def init_colors(self):
        self.HAS_COLORS = curses.has_colors()
        self.CAN_CHANGE_COLOR = curses.can_change_color()
        if self.HAS_COLORS:
            curses.start_color()
    
    def addstr(self,window,y,x,string,formatting=None):
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
    
    def _addstr(self,window,y,x,s,c=None):
        if self.HAS_COLORS and c is not None:
            curses.init_pair(1,self.COLOR_INDEX[c[0]],self.COLOR_INDEX[c[1]])
            window.addstr(y,x,s,curses.color_pair(1))
        else:
            try:
                window.addstr(y,x,s)
            except:
                write_log(traceback.format_exc())
            
            
    def display_status(self):
        self.addstr(self.status,0,0,self.status_msg)
    
    def display_chat_log(self):
        window = self.log
        log = self.chat_log
        h,w = getwindowyx(window)
        row = 0
        for entry,frmt in log[-h:]:
            if row >= h:
                return
            for line in parse_entry_to_fit(entry,w):
                self.addstr(window,row,0,line)
                row += 1
                if row >= h:
                    return

    def display_chat(self):
        window = self.chat
        msg = self.chat_msg
        h,w = getwindowyx(window)
        div = self.DIV_CHAR*(w/len(self.DIV_CHAR)) + self.DIV_CHAR[:w%len(self.DIV_CHAR)]
        self.addstr(window,0,0,div)
        row = 1
        entry = ""
        for entry in parse_entry_to_fit(msg,w)[-h:]:
            self.addstr(window,row,0,entry)
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
        curses.setsyx(y,x)

    def set_room_info(self,_json):
        _json = deserialize(_json)
        for user in _json["users"]:
            self.USERS.append(tuple(user))
        self.ROOM_NAME = _json["name"]
        self.USER_FORMAT

    def add_user(self,msg):
        if msg["name"] != self.USER_NAME:
            self.chat_log.append((msg["name"]+" has joined the room!",None))
            
    def leave_user(self,msg):
        if msg["name"] != self.USER_NAME:
            self.chat_log.append((msg["name"]+" has left the room...",None))
    
    def add_msg(self,msg):
        if msg["verb"] == "msg":
            _msg = msg["name"]+" ("+time_to_display(msg["time"])+"): "+msg["msg"]
            self.chat_log.append((_msg.strip(),None))
            if msg["name"] != self.USER_NAME and len(self.chat_log) > 0 and self.chat_log[-1][0].startswith(self.USER_NAME):
                print '\a'
        elif msg["verb"] == "join":
            self.add_user(msg)
            if msg["name"] != self.USER_NAME:
                print '\a'
        elif msg["verb"] == "leave":
            self.leave_user(msg)
            if msg["name"] != self.USER_NAME:
                print '\a'
    
    def users_in_room(self):
        return "Connected",[]

        #if len(self.USERS) == 0:
        #s = "Connected to: "
        #_frmt = []
        #for user,frmt in self.USERS:
        #    _frmt.append((len(s),len(s)+len(user))+frmt)
        #    s += user + ", "
        #return "Connected",[]

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
        self.curses_init()
        
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
        time_stamp = time_now()
        _msg = {
            "verb":"msg",
            "msg":self.chat_msg,
            "frmt":[],
            "time":time_stamp,
            "name":self.USER_NAME
        }
        self.client.publish("room/1",serialize(_msg),1)
        self.chat_msg = ""

    def run_chat_room(self,server_address):
        try:
            self.curses_init()
            
            # Status Handler
            self.status_thread = StatusThread(self)
            self.status_thread.start()

            self.client.loop_start() 
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
                self.display_chat()
                self.chat.refresh()
                action,c = self.get_user_action()
                if action == "send":
                    self.send()
                elif action == "delr":
                    self.chat_msg = self.chat_msg[:-1]
                elif action == "type":
                    self.chat_msg += str(chr(c))
        except KeyboardInterrupt:
            if curses:
                curses.endwin()
        except Exception as e:
            write_log(e, traceback.format_exc())
        finally:
            self.disconnect()
            self.client.loop_stop()
            if curses:
                curses.endwin()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = ' '.join(i for i in sys.argv[1:])
    else:
        username = "Anonymous"
    c = ChatDisplayManager("",username)
    c.run_chat_room("")
    
