import curses
import time
import datetime
import threading

time_msg = "Not set yet"
entry_msg = ""


def parse_single_line(s,w):
    if len(s) > w:
        idx = s.rfind(" ")
        if idx < 0:
            idx = w
    else:
        idx = len(s)
    return s[:idx],idx
    

def parse_to_fit_line(s,w):
    temp = s.strip()
    li = []
    while len(temp) > w:
        t,idx = parse_single_line(temp,w)
        li.append(t)
        temp = temp[:idx].lstrip()
    if len(temp) > 0:
        li.append(temp)
    return li
            

class StatusThread(threading.Thread):
    def __init__(self,*args,**kwargs):
        super(StatusThread,self).__init__()
        self._stop = threading.Event()
        
    def run(self):
        while True:
            if self.isstopped():
                break
            global time_msg
            time_msg = datetime.datetime.today().strftime("%H:%M:%S")
    
    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()

class ThreadSafeCursesManager(threading.Thread):
    def __init__(self,window,*args,**kwargs):
        self.window = window
        self._stop = threading.Event()
        self._lock = threading.Event()
        self.queue = []

    def run(self):
        while not self.isstopped():
            t = self.check_queue()
            if t:
                t.give_lock()
                while self.islocked():
                    time.sleep(0.1)
                    

    def check_queue(self):
        if len(queue) > 0:
            return queue.pop(0)
        else:
            return False

    def safe_addstr(self,y,x,s):
        if not self.islocked():
            self.lock()
            window.addstr()
            self.unlock()
            return True
        else:
            return False

    def unlock(self):
        self._lock.unset()

    def lock(self):
        self._lock.set()

    def islocked(self):
        return self._lock.isSet()

    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()


class SubwindowManager(threading.Thread):
    def __init__(self,window,y,x,w,h):
        self.window = window
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.has_lock = False

    def display(self,s):
        lines = parse_to_fit_line(s,self.w)[-self.h:]
        row = 0
        while row < h:
            self.addstr(line)

    def addstr(self,y,x,st):
        x, y = self.assert_bounds(self.y+y,self.x+x)
        self.window.addstr(y,x,st)
    
    def assert_bounds(self,y,x):
        return max(min(y,self.y+self.h),self.y),max(min(x,self.x+self.w),x)

    def give_lock(self):
        self.has_lock = True

    def take_lock(self):
        self.has_lock = False

    def wait_for_lock(self):
        while not self.has_lock:
            time.sleep(0.5


def get_divisions(window,ratio=0.75):
    h,w = window.getmaxyx()
    log_w = chat_w = status_w = w
    log_x = chat_x = status_x = 0
    log_y = 0
    log_h = round(h*ratio)
    chat_y = log_h
    chat_h = h-1-log_h
    status_y = h-1
    status_h = 1
    return SubWindowManager(log_x,log_y,log_w,log_x),
        SubwindowManager(chat_x,chat_y,chat_w,chat_h),
        SubwindowManager(status_x,status,y,status_w,status_h)
    
    



w = curses.initscr()
w = curses.initscr()
w.nodelay(1)


try:
    status_thread = StatusThread()
    status_thread.start()
    c = -1
    while c != ord('q'):
        c = w.getch()
        w.addstr(0,0,"")
        w.addstr(1,0,time_msg)
        w.addstr(2,0,str(status_thread.is_alive()))
        w.refresh()
    curses.endwin()
    if status_thread.is_alive():
        status_thread.stop()
except KeyboardInterrupt:
    curses.endwin()
    if status_thread.is_alive():
        status_thread.stop()
except Exception as e:
    curses.endwin()
    if status_thread.is_alive():
        status_thread.stop()
finally:
    if status_thread and status_thread.is_alive():
        status_thread.stop()
    curses.endwin()



