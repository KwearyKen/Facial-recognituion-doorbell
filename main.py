#credit: template is obtained from https://github.com/EbenKouao/Pi-Smart-Doorbell
#and further modified for my use

# importing packages
from flask import Flask, render_template, Response, request, send_from_directory
from camera import VideoCamera
import time
import threading
import os
import RPi.GPIO as GPIO
import sys


#globalise take picture variable
global take_picture
take_picture=0

#GPIO setup
RELAY=11
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY,GPIO.OUT)
GPIO.output(RELAY,GPIO.LOW)

#Uses the VideoCamera object class in camera.py 
pi_camera = VideoCamera(flip=False)

# App Globals to react with HTML web app
app = Flask(__name__)

#background process happening without any refreshing
@app.route('/lock')
def lock():
    print ("Lock")
    GPIO.output(RELAY, GPIO.LOW)
    return ("nothing")

@app.route('/unlock')
def unlock():
    print ("Unlock")
    GPIO.output(RELAY, GPIO.HIGH)
    return ("nothing")


@app.route('/', methods=['GET', 'POST']) #uses the html file as the web app template
def move():
    result = ""
    if request.method == 'POST':
        
        return render_template('index.html', res_str=result)
                        
    return render_template('index.html')


def gen(camera):
    while True:
        frame = camera.get_frame()        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/picture') #take pictures
def take_picture():
    pi_camera.take_picture()
    return "None"

if __name__ == '__main__': #runs the app on local link
    app.run(host='0.0.0.0', debug=False)