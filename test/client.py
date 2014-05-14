import socket
import sys


HOST = raw_input('HOST: ')
PORT = int(raw_input('PORT: '))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

sockets = [sys.stdin, s]

def prompt():
    sys.stdout.write('<You> ')
    sys.stdout.flush()

while True:
    for sock in sockets:
        if sock == s:
            data = sock.recv(64)
            if not data:
                print "derp"
                sys.exit()
            else:
                sys.stdout.write(data)
        else:
            msg = sys.stdin.readlin()
            s.send(msg)
            prompt()
    msg = raw_input("Your Message: ")
    s.send(msg)
    print "Awaiting Reply"
    reply = s.recv(1024)
    print "Received",repr(reply)

s.close()

