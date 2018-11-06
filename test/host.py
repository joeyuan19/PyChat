import socket
import threading
import re
import select

class SocketThread(threading.Thread):
    def __init__(self,socket,*args,**kwargs):
        super(SocketThread, self).__init__(*args,**kwargs)
        self._kill = threading.Event()
    
    def kill(self):
        self._kill.set()

    def alive(self):
        return not self._kill.isSet()

def parse_conn_info(msg):
    exp = r'(\d+?\.\d+?\.\d+?\.\d+?):(\d+?)'
    m = re.search(exp,msg)
    if m.matches():
        return m.group(0), m.group(1)
    return -1,-1

def broadcast(msgs,socks):
    for msg in msgs:
        for sock in socks:
            sock.send(msg)

HOST = 'localhost'
PORT = 0

socket_list = []

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST,PORT))
socket_list.append(server_socket)


q = []

print server_socket.getsockname()

while True:
    sockets,write,err = select.select(socket_list,[],[])
    for sock in sockets:
        if sock == server_socket:
            try:
                sockfd, addr = server_socket.accept()
                sockets.append(sockfd)
                print "New connection:",addr
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print "Failed connection", e
        else:
            msg = sock.recv(64)
            print sock.getsockname(),msg
            q.append(msg)
    broadcast(q,sockets)
            
            

socket.close()

           
