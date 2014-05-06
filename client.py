import curses
import time
import datetime


# BUFFER THE WHOLE THING!!!!!!!!!!!!


DIV_CHAR = "="

USERS = ["Joe","Adrian","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1","User1"]


def write_log(entry):
    with open('pychat.log','a') as f:
        f.write(str(entry)+"\n")

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


def display_chat_log(window, log):
    h,w = window.getmaxyx()
    row = 0
    for entry in log[-h:]:
        # print the header and first line
        header = entry[0] + " (" + entry[1] + ")" + ": "
        index = entry[2][:w-len(header)].rfind(" ")
        if index < 0 or len(entry[2][:w-len(header)]) < w:
            index = w - len(header)
        window.addstr(row,0,header + entry[2][:index])
        row += 1
        if row >= h:
            return
        for line in parse_entry_to_fit(entry[2][index:].strip(),w):
            window.addstr(row,0,line)
            row += 1
            if row >= h:
                return

def display_chat_msg(window,msg):
    h,w = window.getmaxyx()
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
    #window.move(min(y,h-1),min(x,w-1))


def display_div(window):
    h,w = window.getmaxyx()
    window.addstr(0,0,DIV_CHAR*w)


# Status display

MODE_INSERT = 0

def get_mode_str(mde):
    if mde == MODE_INSERT:
        return "Insert"
    else:
        return "Normal"

def fill_middle(msg,trailer,width):
    if len(msg + trailer) < width:
        return msg + " "*(width - len(msg + trailer)-1) + trailer
    return msg + trailer

def users_in_room():
    return "Connected to: " + ", ".join(i for i in USERS)

def display_status_msg(window,msg_info):
    h,w = window.getmaxyx()
    msg = msg_info[0] + " " + users_in_room()
    idx = msg_info[1]
    mde = get_mode_str(msg_info[2])
    
    const_info = " " + mde + " " + datetime.datetime.now().strftime("%H:%M:%S")
    eff_w = w - len(const_info) - 1
    if len(msg) > eff_w:
        idx = (idx + 1)%len(msg)
        msg = (msg + "      " + msg + "      ")[idx:idx+eff_w-3] + "..."
    else:
        idx = -1
    msg = fill_middle(msg,const_info,w)
    write_log(msg)
    window.addstr(0,0,msg)
    time.sleep(0.5)
    return idx


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
    curses.start_color()
    return window

def init_colors(window):
    pass


def split_window(window,ratio=0.75):
    height,width = window.getmaxyx()
    larger = int(round(ratio*height))
    log = window.derwin(larger,width,0,0)
    chat = window.derwin(height-larger-1,width,larger,0)
    status = window.derwin(height-1,0)
    return log, chat, status

def get_window_dims(window):
    return window.getmaxyx()

try:
    window = curses_init()
    log, chat, status = split_window(window)

    chat.keypad(1)
    log.leaveok(1)
    status.leaveok(1)

    chat_log = []
    chat_msg = ""
    status_msg = "Happy Birthday!"
    last_scroll_index = -1
    mode = 0


    while True:
        # Log Display
        log.erase()
        display_chat_log(log,chat_log)
        log.refresh()

        # Status Message
        status.erase()
        last_scroll_index = display_status_msg(status,(status_msg,last_scroll_index,mode))
        status.refresh()


        # Message Prep Display
        chat.erase()
        display_div(chat)
        display_chat_msg(chat,chat_msg)
        chat.refresh()
        if window.getch() == curses.KEY_RESIZE:
            log, chat, status = split_window(window)
        action,c = get_user_action(window)
        if action == "send":
            chat_log.append((USERS[0],"derp o'clock",chat_msg.strip()))
            chat_msg = ""
        elif action == "delr":
            chat_msg = chat_msg[:-1]
        elif action == "type":
            chat_msg += str(chr(c))
            write_log(chat_msg)
    curses.endwin()
except KeyboardInterrupt:
    if curses:
        curses.endwin()
finally:
    if curses:
        curses.endwin()
