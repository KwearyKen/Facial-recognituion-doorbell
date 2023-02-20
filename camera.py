#importing packages
import face_recognition
import cv2
import cv2 as cv
from imutils.video.pivideostream import PiVideoStream
from subprocess import call 
import datetime, time
import time
from datetime import datetime
import numpy as np
import os
import RPi.GPIO as GPIO
import glob
import pyrebase
from twilio.rest import Client

#front facing facial detection algorithm
face_cascade=cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml") 
ds_factor=0.6

#creates a shots folder in the directory
try:
    os.mkdir('./shots')
except OSError as error:
    pass

#Globalize variables for incrementation
Recognized = False
Unrecognized = False

Recognized_counter = 0
Unrecognized_counter = 0

pause = 0
pause_counter = 0

prevTime = 0
doorUnlock = False

#GPIO pin setup
RELAY=11
LEDGREEN=15
LEDRED=13
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY,GPIO.OUT)
GPIO.setup(LEDGREEN,GPIO.OUT)
GPIO.setup(LEDRED,GPIO.OUT)
GPIO.output(RELAY,GPIO.LOW)
GPIO.output(LEDGREEN,GPIO.LOW)
GPIO.output(LEDRED,GPIO.LOW)


#Firebase database setup
config = {
  "apiKey": "AIzaSyA4qtExVNwVe6spE6O3MmJj-TlZe25DPcE",
  "authDomain": "doorbell-8e8ab.firebaseapp.com",
  "databaseURL": "https://doorbell-8e8ab-default-rtdb.firebaseio.com",
  "projectId": "doorbell-8e8ab",
  "storageBucket": "doorbell-8e8ab.appspot.com",
  "messagingSenderId": "301276265136",
  "appId": "1:301276265136:web:946478a1713329a5f89975",
  "measurementId": "G-GH2512X8PK"
}

firebase=pyrebase.initialize_app(config)
storage=firebase.storage()


account_sid = 'AC3489741578b6ae5212666b16aed9253b'
auth_token = '538ca545a0730f2ba954d77eb8572af3'
client = Client(account_sid, auth_token)

from_whatsapp_number='whatsapp:+14155238886'
to_whatsapp_number='whatsapp:+601118691283'


#Store objects in array
known_person=[] #Name of person string
known_image=[] #Image object
known_face_encodings=[] #Encoding object

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True



#Loop to add images in friends folder
for file in os.listdir("/home/pi/Pi-Smart-Doorbell/profiles"):
    try:
        known_person.append(file.replace(".jpg", ""))
        file=os.path.join("/home/pi/Pi-Smart-Doorbell/profiles/", file)
        known_image = face_recognition.load_image_file(file)
        known_face_encodings.append(face_recognition.face_encodings(known_image)[0])

    except Exception as e:
        pass
    
#set camera to use default camera
camera = cv2.VideoCapture(0)


class VideoCamera(object):
    
    def __init__(self, flip = False, file_type  = ".jpg", photo_string= "stream_photo"):
        
        self.flip = flip # Flip frame vertically
        self.file_type = file_type
        self.photo_string = photo_string
        time.sleep(2.0)
    
        
    def flip_if_needed(self, frame):
        if self.flip:
            return np.flip(frame, 0)
        return frame

     
    def get_frame(self): #display frame and facial recognition
        
        global Recognized, Unrecognized
        global pause, pause_counter
        global Recognized_counter
        global Unrecognized_counter
        
        success, image = camera.read()
        
        process_this_frame = True
        
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]
        
       # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            global name_gui;
            #face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                
                #print(face_encoding)
                print(matches)

                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]: #if recognize face
                    name = "Known"
                    Recognized_counter = Recognized_counter + 1
                    
                if matches: #if unrecognize face
                    Unrecognized_counter = Unrecognized_counter + 1
         
                if Recognized_counter > 11: #actions if recognized 11 times
                    Recognized = True
                    client.messages.create(body="Someone you know is at the door, check who it is! <192.168.1.102:5000>", from_=from_whatsapp_number, to=to_whatsapp_number)
                    GPIO.output(RELAY, GPIO.HIGH)
                    GPIO.output(LEDGREEN, GPIO.HIGH)
                    print("green led on")
                    prevTime = time.time()
                    doorUnlock = True
                    print("door unlock")
                    time.sleep(4) #Keeps door open and LED on for 4 seconds
                    doorUnlock = False
                    GPIO.output(RELAY,GPIO.LOW)
                    GPIO.output(LEDGREEN, GPIO.LOW)
                    print("door lock")
                    Recognized_counter = 0
                    Unrecognized_counter = 0
                    pause = 1
                     
                if Unrecognized_counter > 15: #actions if unrecognized 15 times
                    Unrecognized = True
                    GPIO.output(LEDRED, GPIO.HIGH)
                    print("red led on")
                    today_date = datetime.now().strftime("%m%d%Y-%H%M%S")
                    p = os.path.sep.join(['shots', "shot_{}.png".format(str(today_date).replace(":",''))])
                    cv2.imwrite(p,image) #saves the captured image with labelled date
                    client.messages.create(body="Unknown Person detected, Check stream: <192.168.1.102:5000>", from_=from_whatsapp_number, to=to_whatsapp_number)
                    storage.child(my_image).put(p)
                    GPIO.output(LEDRED, GPIO.LOW)
                    pause = 1
                    Recognized_counter=0
                    Unrecognized_counter = 0
                     
                if pause == 1: #stops recognition for roughly 1 second to refresh itself
                    pause_counter = pause_counter + 1
                if pause_counter>5 :
                    pause = 0
                    Recognized = False
                    Unrecognized = False
                    pause_counter = 0
                    

                print(name)
                #print(face_locations)
                face_names.append(name)
                
        
                name_gui = name
                            

        process_this_frame = not process_this_frame
            
        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names): 
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(image, (left, top), (right, bottom), (255, 255, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (255, 255, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(image, name_gui, (left + 10, bottom - 10), font, 1.0, (0, 0, 0), 1)
            

        
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def take_picture(self): #takes picture by button and saves it with current date labelled
        global ID
        success, image = camera.read()
        today_date = datetime.now().strftime("%m%d%Y-%H%M%S")
        p = os.path.sep.join(['/home/pi/Pi-Smart-Doorbell/shots', "shot_{}.png".format(str(today_date).replace(":",''))])
        cv2.imwrite(p,image)
        client.messages.create(body="Images: <https://console.firebase.google.com/u/0/project/doorbell-8e8ab/storage/doorbell-8e8ab.appspot.com/files/~2Fhome~2Fpi~2FPi-Smart-Doorbell~2Fshots>", from_=from_whatsapp_number, to=to_whatsapp_number)
        print(p)
        storage.child(my_image).put(my_image)
        
list_of_files = glob. glob('/home/pi/Pi-Smart-Doorbell/shots/*') #List all files and picks one with the latest date
latest_file = max(list_of_files, key=os. path. getctime)
my_image = latest_file        
