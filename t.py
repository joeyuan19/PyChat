import curses


s = curses.initscr()
print curses.has_colors()

curses.endwin()
