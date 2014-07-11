import mosquitto
import sys, select
import time
import datetime
import json

def time_now():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

def time_to_display(s):
    return datetime.datetime.now().strptime(s,"%Y%m%d%H%M%S%f").strftime("%H:%M:%S")

def serialize(_json):
    return json.dumps(_json,separators=(",",":"))

def deserialize(_json):
    try:
        return json.loads(_json)
    except:
        write_log("JSONDecodeERROR:",_json,"\n",traceback.format_exc())

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
    payload = deserialize(msg.payload)
    if str(payload["name"]).startswith(username):
        return
    sys.stdout.write(payload["name"] + ": "+payload["msg"]+"\n")
    prompt()

def on_disconnect(mosq, obj, rc):
    print "Disconnected, bye!"

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
            time_stamp = time_now()
            _msg = {
                "verb":"msg",
                "msg":msg,
                "frmt":[],
                "time":time_stamp,
                "name":username
            }
            client.publish("room/1",serialize(_msg),1)
            prompt()
    except KeyboardInterrupt:
        print "Leaving room..."
        break
        
client.loop_stop()
client.disconnect()
