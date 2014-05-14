import curses
import threading
import time
import random
import datetime

# Debug functions

def write_log(entry):
    with open('pychat.log','a') as f:
        f.write(str(entry)+"\n")

# Global constants

COLORS = False
USER_COLOR_INDEX = 1
DIV_CHAR = "-"
USER_NAME = "Joe"
USERS = []
USER_COLORS = {
    
}

status_msg = ""
chat_msg = ""
chat_log = []

LAST_COLOR_INDEX = -1

write_log(GOOD_COLOR_PAIRS)

# Style info

MODE_INSERT = 0

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
            window.addstr(row,0,user_name,get_curses_color(USER_COLOR_INDEX))
        else:
            window.addstr(row,0,user_name,curses.color_pair(2))
        header = " (" + entry[1] + ")" + ": "
        index = entry[2][:w-len(header)].rfind(" ")
        if index < 0 or len(entry[2][:w-len(header)]) < w:
            index = w - len(header)
        window.addstr(row,len(user_name),header + entry[2][:index])
        row += 1
        if row >= h:
            return
        for line in parse_entry_to_fit(entry[2][index:].strip(),w):
            window.addstr(row,0,line)
            row += 1
            if row >= h:
                return

def display_chat_msg(window,msg):
    h,w = getwindowyx(window)
    row = 1
    entry = ""
    for entry in parse_entry_to_fit(msg,w)[-h:]:
        window.addstr(row,0,entry)
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
    window.addstr(0,0,DIV_CHAR*w)

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
        global status_msg
        write_log("Update: " + status_msg)
    
    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

def get_user_action(window):
    ch = window.getch()
    if ch == 10:
        action = "send"
    elif ch == 127:
        action = "delr"
    elif ch > 256 or ch < 0:
        #write_log("passed char" + str(ch))
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

def generate_color_pair():
    pass

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

status_thread = None

try:
    window = curses_init()
    log, chat, status = split_window(window)

    log.leaveok(1)
    status.leaveok(1)

    status_thread = StatusThread(status,status_msg)
    status_thread.start()

    while True:
        # Log Display
        log.erase()
        display_chat_log(log,chat_log)
        log.refresh()

        status.erase()
        status.addstr(0,0,status_msg)
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
