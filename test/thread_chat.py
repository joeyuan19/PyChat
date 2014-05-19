import curses
import time
import datetime
import threading

DEBUG = True

time_msg = "Not set yet"
entry_msg = ""

def get_time_now():
    return datetime.datetime.today().strftime("%H:%M:%S")

def get_date_now():
    return datetime.datetime.today().strftime("%m/%d/%Y")

def write_log(msg):
    if DEBUG is False:
        return
    msg = str(msg)
    with open('pychat.log','a') as f:
        f.write(get_date_now() + " " + get_time_now() + ": " + msg + "\n")


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
            

class StoppableThread(threading.Thread):
    def __init__(self):
        super(StoppableThread,self).__init__()
        self._stop = threading.Event()
        

    def stop(self):
        self._stop.set()

    def isstopped(self):
        return self._stop.isSet()


class ThreadSafeCursesManager(StoppableThread):
    def __init__(self,window,*args,**kwargs):
        super(ThreadSafeCursesManager,self).__init__(*args,**kwargs)
        self.window = window
        self.window.nodelay(1)
        self.last_ch = -1
        self.queue = []
        self.cy = 0
        self.cx = 0
        self.last_queue_length = 0

    def run(self):
        write_log("Main start")
        while not self.isstopped():
            last_ch = self.window.getch()
            if self.last_queue_length != len(self.queue):
                write_log("Queue change " + str(self.queue) )
            self.last_queue_length = len(self.queue)
            action,inx = self.check_queue()
            if action == "add":
                if len(inx) > 3:
                    self.add_string(inx[0],inx[1],inx[2],inx[3])
                elif len(inx) > 2:
                    self.add_string(inx[0],inx[1],inx[2])
            elif action == "clear":
                self.clear_section(inx[0],inx[1],inx[2],inx[3])
            self._setcursor()
        write_log("Main done")
    
    
    def getch(self):
        return self.last_ch
    
    def setcursor(self,y,x):
        self.cy = y
        self.cx = x
    
    def setcursor(self,yx):
        self.cy = yx[0]
        self.cx = yx[1]
    
    def _setcursor(self):
        self.window.move(self.cy,self.cx)

    def check_queue(self):
        if len(self.queue) > 0:
            return self.queue.pop(0)
        else:
            return "empty",None

    def clear_section(self,x1,y1,x2,y2):
        for x in range(x1,x2):
            for y in range(x2,y2):
                self.clearyx(y,x)


    def add_string(self,y,x,s,attr=None):
        try:
            if attr is None:
                self.window.addstr(y,x,s)
            else:
                self.window.addstr(y,x,s,attr)
        except Exception as e:
            write_log(str(e) + str(y) +","+ str(x) +",<"+ str(s) + ">," + str(len(s)) )
            raise e
    def clearyx(self,y,x):
        self.window.add_string(self,y,x," ")

    def request_addstr(self,add_instructions):
        self.queue.append(("add",add_instructions))
    
    def request_addstrs(self,li):
        for it in li:
            self.request_addstr(it)
            
    def request_clear(self, clear_coordinates):
        self.queue.append(("clear",clear_coordinates))

class SubwindowManager(StoppableThread):
    def __init__(self,window_manager,y,x,h,w,*args,**kwargs):
        super(SubwindowManager,self).__init__(*args,**kwargs)
        self.window_manager = window_manager
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def clear(self):
        self.window_manager.request_clear((self.x,self.y,self.x+self.w,self.y+self.h))

    def display(self,s):
        lines = parse_to_fit_line(s,self.w)[-self.h:]
        row = 0
        line = ""
        for line in lines:
            self.addstr(row,0,line)
            row += 1
            if row >= self.h:
                break        
        return row,len(line)
        
    

    def addstr(self,y,x,st):
        x, y = self.x + x, self.y + y
        self.window_manager.request_addstr((y,x,st))
    
    def assert_bounds(self,y,x):
        return max(min(y,self.y+self.h),self.y),max(min(x,self.x+self.w),x)

    def __str__(self):
        return "<SubwindowManager y:" + str(self.y) + " x:" + str(self.x) + " w:" + str(self.w) + " h:" + str(self.h) + ">"

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        return self.__str__()

class ChatLog(SubwindowManager):
    pass

class ChatEntry(SubwindowManager):
    def __init__(self,*args,**kwargs):
        super(ChatEntry,self).__init__(*args,**kwargs)
        self.chat_msg = ""
    
    def run(self):
        write_log("Chat running")
        while not self.isstopped():
            c = self.window_manager.getch()
            if c == ord('q'):
                self.window_manager.stop()
            if c == 10:
                write_log("send to log: " + str(("Joe",time.today(),self.chat_msg)))
                self.window_manager.send_to_log(("Joe",time.today(),self.chat_msg))
            else:
                try:
                    self.msg += chr(c)
                except:
                    pass
            self.draw()
        write_log("Chat done")
    
    def draw(self):
        self.clear()
        self.window_manager.setcursor(self.display(self.chat_msg))
            

class StatusBar(SubwindowManager):
    def __init__(self,*args,**kwargs):
        super(StatusBar,self).__init__(*args,**kwargs)
        self.status_msg = "Hello World"
        self.last_index = 0

    def run(self):
        while not self.isstopped():
            self.draw()
            time.sleep(0.8)

    def draw(self):
        self.clear()
        pad = ""
        if len(self.status_msg) < self.w-1:
            pad = " "*(self.w-1-len(self.status_msg))
        msg = ((self.status_msg + pad)*2)[self.last_index:self.last_index+self.w-1]
        self.addstr(0,0,msg)
        self.last_index += 1

class MainWindow(ThreadSafeCursesManager):
    def __init__(self,*args,**kwargs):
        super(MainWindow,self).__init__(curses.initscr(),*args,**kwargs)
        self.h, self.w = self.window.getmaxyx()
        self.create_subwindows()
        self.start()

    def start(self):
        super(MainWindow,self).start()
        self.log.start()
        self.chat.start()
        self.status.start()

    def create_subwindows(self,ratio=0.75):
        div_height = ratio*self.h
        div_height = int(div_height)
        self.log = ChatLog(self,0,0,div_height,self.w)
        self.chat = ChatEntry(self,div_height,0,self.h-div_height-1,self.w)
        self.status = StatusBar(self,self.h-1,0,1,self.w)

    def resize(self,new_h,new_w):
        self.window.resize(new_h,new_w)

    def send_to_log(self,msg):
        self.log.add_msg(msg)

    def stop(self):
        if not self.log.isstopped():
            self.log.stop()
        if not self.chat.isstopped():
            self.chat.stop()
        if not self.status.isstopped():
            self.status.stop()
        super(MainWindow,self).stop()
        curses.endwin()

try: 
    main = MainWindow()
    while not main.isstopped():
        pass
    curses.endwin()
except KeyboardInterrupt:
    if main:
        main.stop()
    curses.endwin()
finally:
    if main:
        main.stop()
    curses.endwin()

