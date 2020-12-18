import threading
import socket
import time
import cv2
import numpy as np
import math
# import matplotlib as plt
from matplotlib import pyplot as plt

host = ''

ret = False
port = 9000
locaddr = (host,port)
stream_state = False
frame = np.zeros((720,960,3),np.uint8)
dilation = np.zeros((720,960,3),np.uint8)
box = np.zeros((504,672,3),np.uint8)
resized = np.zeros((504,672,3),np.uint8)
blank_image = np.full((800, 800), 255, dtype=np.uint8)
path = np.zeros((800,800,3),np.uint8)
data = ""
quadrant = "none"
distance_list = []
current_time = time.time()
x, y = 0, 0
x_old, y_old = 0, 0
forwardvel = 30
final_h = 0

#Create a UDP Socket for commands
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
command_address = ('192.168.10.1', 8889)
video_address = ('udp://192.168.10.1:11111')
sock.bind(locaddr)

print ('Tello: command takeoff land flip forward back left right ')
print ('Wait for the ok')

def streamon():
    sent = sock.sendto(b'streamon', command_address)
    global stream_state
    stream_state = True
    streamThread = threading.Thread(target=videoStream)
    streamThread.start()
    displayThread = threading.Thread(target=videoDisplay)
    displayThread.start()

def recv():
    global data
    while True:
        data, server = sock.recvfrom(1518)
        print(data.decode(encoding="utf-8"))
        data = "executed"
recvThread = threading.Thread(target=recv)
recvThread.start()

def videoStream():
    global ret
    global frame
    cap = cv2.VideoCapture(video_address, cv2.CAP_FFMPEG)
    ret, frame = cap.read()
    while ret:
        ret, frame = cap.read()

def takeoff():
    #print("We're taking off!")
    sent = sock.sendto(b'takeoff', command_address)
    sent = sock.sendto(b'takeoff', command_address)
    sent = sock.sendto(b'takeoff', command_address)
    sent = sock.sendto(b'takeoff', command_address)
    sent = sock.sendto(b'takeoff', command_address)

def height():
    global final_h
    sent = sock.sendto(b'tof?', command_address)
    while True:
        altitude = str(input())
        print(altitude[-1])
        if altitude[4] == 'm':
            final_h = altitude * 0.1
            print(final_h)
    
def land():
    print("We're landing!")
    sent = sock.sendto(b'land', command_address)
    sent = sock.sendto(b'land', command_address)
    sent = sock.sendto(b'land', command_address)
    sent = sock.sendto(b'land', command_address)
    sent = sock.sendto(b'land', command_address)

def stop():
    print("We're stopping!")
    sent = sock.sendto(b'stop', command_address)
    sent = sock.sendto(b'stop', command_address)
    sent = sock.sendto(b'stop', command_address)
    sent = sock.sendto(b'stop', command_address)
    sent = sock.sendto(b'stop', command_address)

def simpleforward(vel):
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)

def forward(vel,time_int):
    global x
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)

    distance = vel * time_int
    x += distance
    if vel > 0:
        print("We're moving forwards!")
        distance_list.append(distance)
    elif vel < 0:
        print("We're moving backwards!")
        distance_list.append(distance)
    time.sleep(time_int)
    distance = abs(distance)
    if vel != 0:
        print("The distance flown was: " + str(distance) + "cm!")

def turn(tvel,time_tvel):
    global y

    sent = sock.sendto(b'rc '+ str(tvel).encode() + b' 0 0 0', command_address)
    sent = sock.sendto(b'rc '+ str(tvel).encode() + b' 0 0 0', command_address)
    sent = sock.sendto(b'rc '+ str(tvel).encode() + b' 0 0 0', command_address)
    sent = sock.sendto(b'rc '+ str(tvel).encode() + b' 0 0 0', command_address)
    sent = sock.sendto(b'rc '+ str(tvel).encode() + b' 0 0 0', command_address)

    distance = tvel * time_tvel
    y += distance
    if tvel > 0:
        print("We're moving right!")
        distance_list.append(distance)
    elif tvel < 0:
        print("We're moving left!")
        distance_list.append(distance)
    time.sleep(time_tvel)
    distance = abs(distance)
    if tvel != 0:
        print("The distance flown was: " + str(distance) + "cm!")

def right():
    stop()
    turn(60,2)
    stop()
    forward(100,2)
    stop()
    turn(-60,2)
    stop()
    land()
    simpleforward(30)
    
def left():
    stop()
    turn(-60,2)
    stop()
    forward(100,2)
    stop()
    turn(60,2)
    stop()
    land()
    simpleforward(30)

def videoDisplay():
    global frame
    global ret
    global resized
    global dilation
    global box
    global blank_image
    global final_h
    simpleforward(forwardvel)
    start_time = time.time()

    ################################################
    global x, y
    global x_old, y_old
    width, height = 800, 800
    path = cv2.cvtColor(blank_image, cv2.COLOR_GRAY2BGR)
    red = (0,0,255)
    radius = 6
    thickness = -1
    cv2.circle(path, (0, 400), radius, red, thickness)
    #################################################

    while stream_state:
        scale_percent = 70  # percent of original size
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        xreal = int(width/2)
        yreal = int(height/2)
        resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        final = np.copy(resized)

        #Center Point
        center_coordinates = (xreal,yreal)
        radius = 2
        color = (0,0,255)
        thickness = -1
        cv2.circle(resized,center_coordinates,radius,color,thickness)
        # cv2.imshow('original', resized)

        #GaussianBlur
        blur = cv2.GaussianBlur(resized, (3, 3), 0)
        #cv2.imshow('Gaussian Blur', blur)

        #HSV
        HSV = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
        #cv2.imshow('HSV', HSV)

        #Mask
        range1 = (0, 0, 0)
        range2 = (110, 110, 100)
        mask = cv2.inRange(HSV, range1, range2)
        #cv2.imshow('mask', mask)

        # Vertical
        vertical = np.copy(mask)
        rows = vertical.shape[0]
        verticalsize = rows // 10
        verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
        vertical = cv2.erode(vertical, verticalStructure)
        vertical = cv2.dilate(vertical, verticalStructure)
        #cv2.imshow("vertical", vertical)

        kernel1 = np.ones((3,10),np.uint8)
        erosion = cv2.morphologyEx(vertical, cv2.MORPH_ERODE, kernel1)
        #cv2.imshow('erosion', erosion)

        #New portion of code for BLOB detection and line drawing
        kernel2 = np.ones((55,35),np.uint8)
        dilation = cv2.morphologyEx(erosion, cv2.MORPH_DILATE, kernel2)
        #cv2.imshow('dilation',dilation)

        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for c in contours:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            area = cv2.contourArea(c)
            rect = cv2.boundingRect(c)

            areaList = area
            xList = rect[0]
            yList = rect[1]
            wList = rect[2]
            hList = rect[3]
            
            dilation2 = cv2.cvtColor(dilation, cv2.COLOR_GRAY2BGR)
            cv2.drawContours(dilation2, contours, -1, (0, 255, 0), 3)
            cv2.drawContours(resized, contours, -1, (0, 255, 0), 3)

            # if areaList < 337500:                                        
            #     takeoff()

            if hList > 400 and areaList < 337500: 
                start_point = (xList, yList)
                end_point = (xList+wList, yList+hList)
                color = (255, 0, 0)
                thickness = -1
                image = cv2.rectangle(final, start_point, end_point, color, thickness)
                image_processing_time = time.time()-start_time
                x += image_processing_time * forwardvel

                if cX < int(width/2) and areaList < 337500:
                    print("This blob belongs to the left side.")          
                    left()
                elif cX > int(width/2) and areaList < 337500:
                    print("This blob belongs to the right side.")
                    right()

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(final, 'x:' + str(x) + " y:" + str(y) + " h:" + str(final_h), (0,25), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('Final', final)
        cv2.imshow('Original', resized)
        cv2.waitKey(20)
        
def battery():
    global current_time
    while True:
        if time.time() - current_time > 10:
            sent = sock.sendto(b'battery?', command_address)
            current_time = time.time()
            height()
batteryThread = threading.Thread(target=battery)
batteryThread.start()

def commands():
    sent = sock.sendto(b'command', command_address)
    sent = sock.sendto(b'battery?', command_address)
    global data
    streamon()
    takeoff()
    
    while True:
        if data != "executed":
            msg = input().rstrip()
            if 'end' in msg:
                sent = sock.sendto(b'streamoff', command_address)
                print('...command sent')
                sock.close()
                print('error streamoff')
                break
            msg = msg.encode(encoding="utf-8") #how the message is encoded
            sent = sock.sendto(msg, command_address)
commands()
