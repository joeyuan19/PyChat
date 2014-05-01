import curses
import time
import datetime

DIV_CHAR = "="

user_name = "joe"

def display_chat_log(window, log, w, h):
    line_height = 

try:
    window = curses.initscr()
    curses.noecho()
    window.nodelay(1)
    height,width = window.getmaxyx()
    
    chat_log = []
    chat_msg = ""
    div = DIV_CHAR*width

    q = -1
    while q != ord('q'):
        window.clear()
        window.addstr(height*CHAT_PORTION,0,div)
        display_chat(window, chat_log, width, height)
        window.refresh()
        q = window.getch()
        if q == 10:
            chat_log.append( user_name + "(" + datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S') + "): " + chat_msg )
            chat_msg = ""
        elif q >= 0:
            chat_msg += str(chr(q))
            if q == ord('q'):
                break
            q = -1
        window.addstr((height*2/3)+1,0,chat_msg)
        window.refresh()
finally:
    if curses:
        curses.endwin()
