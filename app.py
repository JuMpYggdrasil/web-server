import paho.mqtt.client as mqtt
from flask import Flask,g,render_template,request,Response
from flask_socketio import SocketIO, emit
from flask_apscheduler import APScheduler
from libDB import logDB,clearOldDB,queryDB
import numpy as np
import json
from libPickle import *

from pyimagesearch.motion_detection import SingleMotionDetector
from imutils.video import VideoStream
import threading
import argparse
import datetime
import imutils
import schedule
import time
import cv2


class Config(object):
    SCHEDULER_API_ENABLED = True
    SECRET_KEY = 'secret!'
    threaded=True
    
scheduler = APScheduler()

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing tthe stream)
outputFrame = None
lock = threading.Lock()

app = Flask(__name__)
app.config.from_object(Config())
socketio = SocketIO(app)

# initialize the video stream and allow the camera sensor to
# warmup
#vs = VideoStream(usePiCamera=1).start()
vs = VideoStream(src=0).start()


# Create a dictionary called devices to store the device number, name, and device state:
devices = {
    'one' : {'floor' : 'fl1','position' : 'garage','object' : 'door', 'cmd' : '01', 'state' : 'False', 'type' : 'on/off', 'topic' : 'fl1/garage/door/01', 'temp' : '0', 'humid' : '0', 'th_enable' : 'False', 'time_enable' : 'False'},
    'two' : {'floor' : 'fl1','position' : 'garage','object' : 'door', 'cmd' : '02', 'state' : 'False', 'type' : 'latch', 'topic' : 'fl1/garage/door/02', 'temp' : '0', 'humid' : '0', 'th_enable' : 'False', 'time_enable' : 'False'},
    'three' : {'floor' : 'fl1','position' : 'com','object' : 'light', 'cmd' : '01', 'state' : 'False', 'type' : 'on/off', 'topic' : 'fl1/com/light/01', 'temp' : '0', 'humid' : '0', 'th_enable' : 'False', 'time_enable' : 'False'},
    'four' : {'floor' : 'fl1','position' : 'com','object' : 'light', 'cmd' : '02', 'state' : 'False', 'type' : 'on/off', 'topic' : 'fl1/com/light/02', 'temp' : '0', 'humid' : '0', 'th_enable' : 'False', 'time_enable' : 'False'},
    'five' : {'floor' : 'fl2','position' : 'liv','object' : 'fan', 'cmd' : '01', 'state' : 'False', 'type' : 'on/off', 'topic' : 'fl2/liv/fan/01', 'temp' : '0', 'humid' : '0', 'th_enable' : 'False', 'time_enable' : 'False'},
    'six' : {'floor' : 'fl2','position' : 'cen','object' : 'light', 'cmd' : '01', 'state' : 'False', 'type' : 'on/off', 'topic' : 'fl2/cen/light/01', 'temp' : '0', 'humid' : '0', 'th_enable' : 'False', 'time_enable' : 'False'},
    'seven' : {'floor' : 'fl3','position' : 'bed','object' : 'fan', 'cmd' : '01', 'state' : 'False', 'type' : 'on/off', 'topic' : 'fl3/bed/fan/01', 'temp' : '0', 'humid' : '0', 'th_enable' : 'False', 'time_enable' : 'False'}
    }
try:
    devices = load_pickle_obj('devices')
    # print(devices)
    print("devices exist")
except:
    save_pickle_obj(devices,'devices')

sensors = {
    'one' : {'name' : 'sensorName1'}
    }

jobCron = { 'startHour':'14',
            'startMinute':'00',
            'stopHour':'14',
            'stopMinute':'30'
    }
try:
    jobCron = load_pickle_obj('jobCron')
    # print(jobCron)
    print("jobCron exist")
except:
    save_pickle_obj(jobCron,'jobCron')

queryDatas = {'temp':{},
            'timeStamp':{},
            'humid':{}}

# Put the device dictionary into the template data dictionary:
templateData = {
    'devices' : devices,
    'sensors' : sensors,
    'jobCron': jobCron,
    'queryDatas':queryDatas
    }

@scheduler.task('cron', id='do_job_on', hour=jobCron['startHour'], minute=jobCron['startMinute'])
def jobOn():
    print('Job on executed')
    for device in devices:
        if devices[device]['type'] == 'on/off':
            if devices[device]['time_enable'] == 'True':
                devices[device]['state'] = 'True'
                mqtt_client.publish(devices[device]['topic'],"on")
            print(device+' '+devices[device]['time_enable'])
    try:
        save_pickle_obj(devices,'devices')
    except:
        print("error")

@scheduler.task('cron', id='do_job_off', hour=jobCron['stopHour'], minute=jobCron['stopMinute'])
def jobOff():
    print('Job off executed')
    for device in devices:
        if devices[device]['type'] == 'on/off':
            if devices[device]['time_enable'] == 'True':
                devices[device]['state'] = 'False'
                mqtt_client.publish(devices[device]['topic'],"off")
            print(device+' '+devices[device]['time_enable'])
    try:
        save_pickle_obj(devices,'devices')
    except:
        print("error")

@scheduler.task('cron', id='do_job_DB', minute='*')
def jobDB():
    print('Job DB executed')
    for device in devices:
        if devices[device]['th_enable'] == 'True':
            logDB(devices[device]['topic'],devices[device]['temp'],devices[device]['humid'],"DHT","true")
            try:
                save_pickle_obj(devices,'devices')
            except:
                print("error")
        
@scheduler.task('cron', id='do_job_ClrDB', day='*')
def jobClrDB():
    print('Job ClrDB executed')
    clearOldDB()

scheduler.init_app(app)
scheduler.start()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("fl1/#")#  + single-level wild card, # multi-level wild card, 
    client.subscribe("fl2/#")
    client.subscribe("fl3/#")
    client.subscribe("tele/#")
    
def whx(ownval,owndicts):
    for x in owndicts:
        if (ownval) in owndicts[x].values():
            return x
    return 'none'

# The callback for when a PUBLISH message is received from the ESP8266.
def on_message(client, userdata, message):
    # socketio.emit('my variable')
    # print("Received message '" + str(message.payload.decode('utf8')) + "' on topic '"+ message.topic + "' with QoS " + str(message.qos))
    if message.topic.startswith('fl'):
        topicMsgSplit = message.topic.split("/")
        slash_count = message.topic.count("/")
        if slash_count>=3:
            topicMsg = topicMsgSplit[0]+"/"+topicMsgSplit[1]+"/"+topicMsgSplit[2]+"/"+topicMsgSplit[3]
            indexName = whx(topicMsg,devices)
            devices_list = list(devices)
            n_index = devices_list.index(indexName)
            if "/temperature" in message.topic:
                devices[indexName]['th_enable'] = 'True'
                devices[indexName]['temp'] = str(message.payload.decode('utf8'))
                socketio.emit('temp' , {'data': devices[indexName]['temp'],'pos':n_index})
                #print("temperature update")
            if "/humidity" in message.topic:
                devices[indexName]['th_enable'] = 'True'
                devices[indexName]['humid'] = str(message.payload.decode('utf8'))
                socketio.emit('humid' , {'data': devices[indexName]['humid'],'pos':n_index})
                # print("humidity update")            
            if "/feedback" in message.topic:
                if "on" in str(message.payload.decode('utf8')):
                    if devices[indexName]['state'] == 'False':
                        devices[indexName]['state'] = 'True'
                        socketio.emit('refresh' , {})
                        # print("refresh")
                    
                else:
                    if devices[indexName]['state'] == 'True':
                        devices[indexName]['state'] = 'False'
                        socketio.emit('refresh' , {})
                        # print("refresh")
                # print("feedback update")
        else:
            print("message.topic error")
    elif message.topic.startswith('tele'):
        #print("tasmota")
        topicMsgSplit = message.topic.split("/")#[0]:tele,[1]:name,[2]:classify
        #topicMsg = topicMsgSplit[0]+"/"+topicMsgSplit[1]+"/"+topicMsgSplit[2]
        if topicMsgSplit[2] == "SENSOR":
            #print(topicMsgSplit[1])
            topic_json=json.dumps(str(message.payload.decode('utf8')))
            print(topic_json["ENERGY"])
            
    else:
        print("unknown topic: "+message.topic)
        
    try:
        save_pickle_obj(devices,'devices')
    except:
        print("error")
    

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("127.0.0.1",1883,60)
# mqtt_client.connect("192.168.2.46",1883,60)
mqtt_client.loop_start()


@app.route("/")
def main():
    queryDatas['temp'] = queryDB("temp")
    queryDatas['humid'] = queryDB("humid")
    queryDatas['timeStamp'] = queryDB("timeStamp")

    # print(queryDatas['timeStamp'])

    templateData = {
        'devices' : devices,
        'sensors' : sensors,
        'jobCron': jobCron,
        'queryDatas':queryDatas
    }
    
    try:
        save_pickle_obj(devices,'devices')
    except:
        print("error")

    # Pass the template data into the template main.html and return it to the user
    return render_template('main.html', async_mode=socketio.async_mode, **templateData)

# The function below is executed when someone requests a URL with the device number and action in it:
@app.route("/<device>/<floor>/<position>/<object>/<cmd>/<ctrl>",methods = ['POST', 'GET'])
def action(device, floor, position, object, cmd, ctrl):
    # Convert the device from the URL into an integer:
    #function = function#int(function)
    # Get the device name for the device being changed:
    # deviceName = devices[function]['name']
    # If the action part of the URL is "1" execute the code indented below:
    if ctrl == "on":
        mqtt_client.publish(devices[device]['topic'],"on")
        #print('mp '+devices[device]['topic'])
        devices[device]['state'] = 'True'
    # if ctrl == "0" and object == 'door':
    if ctrl == "off":
        mqtt_client.publish(devices[device]['topic'],"off")
        #print('mp '+devices[device]['topic'])
        devices[device]['state'] = 'False'
    if ctrl == "toggle":
        if devices[device]['state'] == 'True':
            mqtt_client.publish(devices[device]['topic'],"off")
            #print('mp '+devices[device]['topic'])
            devices[device]['state'] = 'False'
        else:   
            mqtt_client.publish(devices[device]['topic'],"on")
            #print('mp '+devices[device]['topic'])
            devices[device]['state'] = 'True'
    if ctrl == "click":
        mqtt_client.publish(devices[device]['topic'],"click")
        print('click '+devices[device]['topic'])
        devices[device]['state'] = 'False'
        
    # Along with the device dictionary, put the message into the template data dictionary:
    templateData = {
        'devices' : devices,
        'sensors' : sensors,
        'jobCron': jobCron,
        'queryDatas':queryDatas
    }
    try:
        save_pickle_obj(devices,'devices')
    except:
        print("error")
    return render_template('main.html', **templateData)

@app.route("/addSched/<device>")
def addSched(device):
    print('time_enable '+devices[device]['time_enable'])
    devices[device]['time_enable'] = 'True'

    templateData = {
        'devices' : devices,
        'sensors' : sensors,
        'jobCron': jobCron,
        'queryDatas':queryDatas
    }
    try:
        save_pickle_obj(devices,'devices')
    except:
        print("error")
    return render_template('main.html', **templateData)
    
    
@app.route("/rmSched/<device>")
def rmSched(device):
    print('time_enable '+devices[device]['time_enable'])
    devices[device]['time_enable'] = 'False'

    templateData = {
        'devices' : devices,
        'sensors' : sensors,
        'jobCron': jobCron,
        'queryDatas':queryDatas
    }
    try:
        save_pickle_obj(devices,'devices')
    except:
        print("error")
    return render_template('main.html', **templateData)

@app.route('/startTime',methods = ['POST', 'GET'])
def startTime():
    if request.method == 'POST':
        print(request.form)
        result1 = str(request.form['startTime1'])
        result2 = str(request.form['startTime2'])
        for job in scheduler.get_jobs():
            print(job.id)
        
        try:
            scheduler.scheduler.reschedule_job('do_job_on', trigger='cron', hour=result1, minute=result2)
            jobCron['startHour']=result1
            jobCron['startMinute']=result2
        except:
            pass

    templateData = {
        'devices' : devices,
        'sensors' : sensors,
        'jobCron': jobCron,
        'queryDatas':queryDatas
    }
    try:
        save_pickle_obj(devices,'devices')
        save_pickle_obj(jobCron,'jobCron')
    except:
        print("error")
    return render_template('main.html', **templateData)
        

@app.route('/stopTime',methods = ['POST', 'GET'])
def stopTime():
    if request.method == 'POST':
        result1 = str(request.form['stopTime1'])
        result2 = str(request.form['stopTime2'])
        for job in scheduler.get_jobs():
            print(job.id)
                
        try:
            scheduler.scheduler.reschedule_job('do_job_off', trigger='cron', hour=result1, minute=result2)
            jobCron['stopHour']=result1
            jobCron['stopMinute']=result2
        except:
            pass
        
    templateData = {
        'devices' : devices,
        'sensors' : sensors,
        'jobCron': jobCron,
        'queryDatas':queryDatas
    }
    try:
        save_pickle_obj(devices,'devices')
        save_pickle_obj(jobCron,'jobCron')
    except:
        print("error")
    return render_template('main.html', **templateData)

@app.route("/videoStream")
def videoStream():
    # return the rendered template
    return render_template("videoStream.html")

def detect_motion(frameCount):
    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, outputFrame, lock

    # initialize the motion detector and the total number of frames
    # read thus far
    md = SingleMotionDetector(accumWeight=0.1)
    total = 0

    # loop over frames from the video stream
    while True:
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        # grab the current timestamp and draw it on the frame
        timestamp = datetime.datetime.now()
        cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), 
            (10, frame.shape[0] - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # if the total number of frames has reached a sufficient
        # number to construct a reasonable background model, then
        # continue to process the frame
        if total > frameCount:
            # detect motion in the image
            motion = md.detect(gray)

            # cehck to see if motion was found in the frame
            if motion is not None:
                # unpack the tuple and draw the box surrounding the
                # "motion area" on the output frame
                (thresh, (minX, minY, maxX, maxY)) = motion
                cv2.rectangle(frame, (minX, minY), (maxX, maxY),(0, 0, 255), 2)
        
        # update the background model and increment the total number
        # of frames read thus far
        md.update(gray)
        total += 1

        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            outputFrame = frame.copy()
            # outputFrame = gray.copy()
            
        
def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),mimetype = "multipart/x-mixed-replace; boundary=frame")
        
@socketio.on('my event')
def handle_my_custom_event(json):
    #print('received json data here: ' + str(json))
    pass

# function for responses
def results():
    # build a request object
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))
    # print(req,flush=True)
    # fetch fulfillmentText from json
    fulfillmentText = req.get('queryResult').get('fulfillmentText')
    # print(req,flush=True)
    # print(fulfillmentText, flush=True)

    mqtt_client.publish("fl1/garage/door/02","slide")

    # return a fulfillment response
    #return {'fulfillmentText': 'This is a response from webhook.'}

    return 'results'

@app.route('/webhook',methods=['GET','POST'])
def webhook():
    if request.method == 'POST':
        return results()
    else:
        return 'Hello'

if __name__ == "__main__":
    t = threading.Thread(target=detect_motion, args=(64,))
    t.daemon = True
    t.start()
    socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False)
    
# release the video stream pointer
vs.stop()