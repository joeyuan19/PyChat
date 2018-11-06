import curses
import signal

def split(window):
    h,w = window.getmaxyx()
    _h = int(h/2.)
    top = window.derwin(_h,w,0,0)
    bot = window.derwin(_h,0)
    return top,bot

def resize_handler(n,frame):
    curses.endwin()
    global main_win
    main_win = curses.initscr()
    global wins
    wins = split(main_win)
    global resize_count
    resize_count += 1

resize_count = 0
main_win = curses.initscr()
curses.curs_set(0)
main_win.leaveok(1)
wins = split(main_win)
ch = 1
signal.signal(signal.SIGWINCH,resize_handler)
while ch != ord('q'):
    for win,name in zip(wins,("a","b")):
        win.erase()
        h,w = win.getmaxyx()
        win.addstr(1,1,"w: "+str(w)+" h: "+str(h))
        win.addstr(2,1,"main: "+str(main_win.getmaxyx()))
        win.addstr(3,1,"r: " + str(resize_count))
        win.border(name,name,name,name)
        win.refresh()
    ch = main_win.getch()

curses.endwin()


