import curses
import time
import datetime

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
        index = entry[2][:width-len(header)].rfind(" ")
        if index < 0:
            index = width - len(header)
        window.addstr(row,0,header + entry[2][:index])
        row += 1
        for line in parse_entry_to_fit(entry[index].strip(),w):
            window.addstr(row,0,line)
            row += 1
            if row >= h:
                return

def display_chat_msg(window,msg):
    h,w = window.getmaxyx()
    row = 1
    for entry in parse_entry_to_fit(msg,w):
        window.addstr(row,0,entry)
        row += 1
        if row >= h:
            return


def get_user_action(window):
    ch = window.getch()
    if ch == 10:
        return "send",ch
    elif ch > 0:
        return "type",ch
    else:
        return "pass",ch




def curses_init():
    window = curses.initscr()
    curses.noecho()
    curses.cbreak()
    window.nodelay(1)
    return window




try:
    window = curses_init()
    height,width = window.getmaxyx()
    
    log = window.subwin(3*height/4,width,0,0)
    chat = window.subwin(3*height/4 + 1,0)
    
    chat_height,chat_width = chat.getmaxyx()
    log_height,log_width = log.getmaxyx()
    
    chat_log = []
    chat_msg = ""
    div = DIV_CHAR*log_width

    while True:
        # Log Display
        log.erase()
        display_chat_log(log,chat_log)
        log.refresh()

        # Message Prep Display
        chat.erase()
        display_chat_msg(chat,chat_msg)
        chat.addstr(0,0,div[5])
        chat.refresh()
        action,c = get_user_action(chat)
        if action == "send":
            chat_log.append((user_name,"derp o'clock",chat_msg.strip()))
            chat_msg = ""
        elif action == "type":
            chat_msg += str(c)
        c = -1
    curses.endwin()
except KeyboardInterrupt:
    if curses:
        curses.endwin()
finally:
    if curses:
        curses.endwin()
