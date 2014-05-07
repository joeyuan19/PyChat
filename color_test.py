import curses


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
    for i in range(8):
        for j in range(8):
            if i != j:
                curses.init_pair(c, get_color(i), get_color(j))
                c += 1
    return c


c = assign_color_pairs()
w.nodelay(1)

wi,he = w.getmaxyx()

ch = -1
while ch != ord('q'):
    ch = w.getch()
    w.addstr(0,0,"<")
    for i in range(1,c):
        w.addstr(0,i,"a",curses.color_pair(i))
    w.addstr(0,i,">")

curses.endwin()

