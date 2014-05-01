import curses
import time
import datetime

DIV_CHAR = "="

user_name = "joe"

def display_chat_log(window, log, w, h):
    pass
    
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
        window.addstr(height*3/4,0,div)
        display_chat_log(window, chat_log, width, height)
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
        window.addstr((height*3/4)+1,0,chat_msg)
        window.refresh()
except KeyboardInterrupt:
    print "derp"
    if curses:
        curses.endwin()
finally:
    print "derp"
    if curses:
        curses.endwin()
