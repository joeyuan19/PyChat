import curses
import time
import datetime

def curses_init():
    window = curses.initscr()
    curses.noecho()
    curses.cbreak()
    window.nodelay(1)
    return window

try:
    window = curses_init()
    height,width = window.getmaxyx()
    display = ""
    c = -1
    keypad_on = False
    while c != ord('q'):
        # Log Display
        window.erase()
        window.addstr(0,0,display)
        if keypad_on:
            window.addstr(height-1,0,"Keypad on")
        else:
            window.addstr(height-1,0,"Keypad off")
        window.refresh()
        
        # Message Prep Display
        c = window.getch()
        if c == 10:
            display = ""
        elif c == ord('e'):
            if keypad_on:
                window.keypad(0)
                keypad_on = False
            else:
                window.keypad(1)
                keypad_on = True
        if c == 127:
            display = display[:display.rfind('<')]
        elif c > 0:
            display += "<" + str(c) + ":" + str(chr(c)+ "") + ">"
        
    curses.endwin()
except KeyboardInterrupt:
    if curses:
        curses.endwin()
finally:
    if curses:
        curses.endwin()
