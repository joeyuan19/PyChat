import mosquitto
import sys, select


def prompt():
    sys.stdout.write('>>> ')
    sys.stdout.flush()

def on_connect(mosq, obj, rc):
    if rc == 0:
        client.subscribe("room/1")
        print "Connected successfully"
        prompt()
    else:
        raise Exception("Connection to chat room unsuccessful")

def on_message(mosq, obj, msg):
    if str(msg.payload).startswith(username):
        return
    sys.stdout.write(str(msg.payload))
    prompt()

def on_disconnect(mosq, obj, rc):
    print "Disconnected.  Bye!"

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    username = "Anonymous"

client = mosquitto.Mosquitto(username)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect("127.0.0.1",port=8000) 
client.loop_start()

while True:
    try:
         rsock, wsock, esock = select.select([sys.stdin],[],[])
         for sock in rsock:
            msg = sys.stdin.readline()
            client.publish("room/1",username+": "+msg,1)
            prompt()
    except KeyboardInterrupt:
        print "Leaving room..."
        break
        
client.loop_stop()
client.disconnect()
