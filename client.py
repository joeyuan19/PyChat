import curses
import time
import datetime


# BUFFER THE WHOLE THING!!!!!!!!!!!!


DIV_CHAR = "="

user_name = "joe"


def write_log(entry):
    with open('pychat.log','a') as f:
        f.write(entry)

def parse_entry_to_fit(entry,width):
    remaining = entry
    split = []
    while len(remaining) > width:
        index = remaining[:width].rfind(' ')
        if index < 0 or remaining[:width].count(' ') < 2:
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
        header = entry[0] + "(" + entry[1] + ")" + ": "
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
        if row >= h:
            break
    if len(entry) >= h:
        x = 0
        y = row + 1
    elif len(entry) == 0:
        x = 0
        y = 1
    else:
        x = len(entry)
        y = row
    window.move(min(y,h-1),min(x,w-1))

def display_div(window):
    h,w = window.getmaxyx()
    window.addstr(0,0,DIV_CHAR*w)


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
    curses.noecho()
    curses.cbreak()
    window.nodelay(1)
    return window

def split_window(window,ratio=0.75):
    height,width = window.getmaxyx()
    larger = int(round(ratio*height))
    log = window.subwin(larger,width,0,0)
    chat = window.subwin(height-larger-2,width,larger,0)
    status = window.subwin(height-1,0)
    return log, chat, status

def get_window_dims(window):
    return window.getmaxyx()

try:
    window = curses_init()
    log, chat, status = split_window(window)

    window.keypad(1)
    chat.keypad(1)
    
    window.leaveok(1)
    chat.leaveok(1)
    window.idlok(1)
    chat.idlok(1)
    window.idcok(1)
    chat.idcok(1)
    chat_height,chat_width = chat.getmaxyx()
    log_height,log_width = log.getmaxyx()
    
    chat_log = []
    chat_msg = ""

    while True:
        # Log Display
        log.erase()
        display_chat_log(log,chat_log)
        log.refresh()

        # Message Prep Display
        chat.erase()
        display_div(chat)
        display_chat_msg(chat,chat_msg)
        chat.refresh()
        action,c = get_user_action(chat)
        if action == "send":
            chat_log.append((user_name,"derp o'clock",chat_msg.strip()))
            chat_msg = ""
        elif action == "delr":
            chat_msg = chat_msg[:-1]
        elif action == "type":
            chat_msg += str(chr(c))
    curses.endwin()
except KeyboardInterrupt:
    if curses:
        curses.endwin()
finally:
    if curses:
        curses.endwin()
