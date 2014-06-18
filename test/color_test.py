import curses
import random

w = curses.initscr()
curses.start_color()


def get_color(idx):
    if idx == 0:
        return curses.COLOR_BLACK
    elif idx == 1:
        return curses.COLOR_GREEN
    elif idx == 2:
        return curses.COLOR_CYAN
    elif idx == 3:
        return curses.COLOR_BLUE
    elif idx == 4:
        return curses.COLOR_RED
    elif idx == 5:
        return curses.COLOR_YELLOW
    elif idx == 6:
        return curses.COLOR_MAGENTA
    elif idx == 7:
        return curses.COLOR_WHITE
    else:
        return -1
    
def assign_color_pairs():
    c = 1
    ci = []
    for i in range(8):
        for j in range(8):
            curses.init_pair(c, get_color(i), get_color(j))
            print i,j,curses.color_pair(c)
            ci.append(str(i) + "," + str(j))
            c += 1
    return c, ci


c,ci = assign_color_pairs()
w.nodelay(1)

wi,he = w.getmaxyx()

ch = -1
while ch != ord('q'):
    ch = w.getch()
    for i in range(1,c):
        # Disco Colors
        N = 256
        curses.init_pair(N,get_color(random.randint(0,7)),get_color(random.randint(0,7)))
        y = int(ci[i-1][-1])
        x = int(ci[i-1][0])
        w.addstr(0,i-1,"a",curses.color_pair(N))
        w.addstr(y+2,x*5,"a",curses.color_pair(N))
        w.addstr(y+2,x*5+1,ci[i-1])
curses.endwin()

