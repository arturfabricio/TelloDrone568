import threading
import socket
import time
import cv2.cv2 as cv2
import numpy as np
import math
import matplotlib as plt

host = ''
port = 9000
locaddr = (host,port)
stream_state = False
frame = np.zeros((720,960,3),np.uint8)
dilation = np.zeros((720,960,3),np.uint8)
box = np.zeros((504,672,3),np.uint8)
resized = np.zeros((504,672,3),np.uint8)
current_time = time.time()
data = ""

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
    global frame
    cap = cv2.VideoCapture(video_address, cv2.CAP_FFMPEG)
    ret, frame = cap.read()
    while ret:
        ret, frame = cap.read()

def takeoff():
    #print("We're taking off!")
    sent = sock.sendto(b'takeoff', command_address)

def land():
    #print("We're landing!")
    sent = sock.sendto(b'land', command_address)

def forward(vel):
    # print("We're moving forward!")
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)

def turn(tvel):
    print("We're turning!")
    #sent = sock.sendto(b'takeoff', command_address)
    sent = sock.sendto(b'rc '+ str(tvel).encode() + b' 0 0 0', command_address)
    
def videoDisplay():
    #takeoff()
    global frame
    global resized
    global dilation
    global box
    while stream_state:
        forward(30)
        #New portion Image Processing
        scale_percent = 70  # percent of original size
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        # print(height)
        # print(width)
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
        #cv2.imshow('original', resized)
        
        CandB = np.zeros(resized.shape, resized.dtype)
        alpha = 1
        beta = 50
        CandB = cv2.convertScaleAbs(resized, alpha=alpha, beta=beta)
        cv2.imshow('Constrast and Brightness', CandB)

        #GaussianBlur
        blur = cv2.GaussianBlur(CandB, (3, 3), 0)
        #cv2.imshow('Gaussian Blur', blur)

        #HSV
        HSV = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
        #cv2.imshow('HSV', HSV)

        #Mask
        light_orange = (0, 0, 0)
        dark_orange = (110, 110, 100)
        mask = cv2.inRange(HSV, light_orange, dark_orange)
        #cv2.imshow('mask', mask)

        # Specify size on vertical axis
        vertical = np.copy(mask)
        rows = vertical.shape[0]
        verticalsize = rows // 10
        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
        # Apply morphology operations
        vertical = cv2.erode(vertical, verticalStructure)
        vertical = cv2.dilate(vertical, verticalStructure)
        # Show extracted vertical lines
        #cv2.imshow("vertical", vertical)

        #Opening
        kernel = np.ones((17,17),np.uint8)
        opening = cv2.morphologyEx(vertical, cv2.MORPH_OPEN, kernel)
        #cv2.imshow('opening', opening)

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

            if hList > 400:
                print("im in!")
                start_point = (xList, yList) 
                end_point = (xList+wList, yList+hList) 
                color = (255, 0, 0)  
                thickness = -1
                image = cv2.rectangle(final, start_point, end_point, color, thickness)

                if xList < int(width/2):
                    quadrant = "left"
                    print("This blob belongs to the " + quadrant + " side.")                
                elif xList > int(width/2):
                    quadrant = "right"
                    print("This blob belongs to the " + quadrant + " side.")                
                    
            cv2.imshow('Final', final)
            cv2.imshow('Original', resized)
            i += 1
        cv2.waitKey(20)

    if quadrant == "left":
        takeoff()
        forward(0)
        print("forward")
        time.sleep(4)
        turn(30)
        print("first turn")
        time.sleep(4)
        forward(20)
        print("forward")
        time.sleep(4)
        turn(-30)
        print("second turn")
        time.sleep(4)
        forward(20)
        print("forward")
        time.sleep(5)
        forward(0)
        land()
        print("land")

    if quadrant == "right":
        takeoff()
        forward(0)
        print("forward")
        time.sleep(4)
        turn(-30)
        print("first turn")
        time.sleep(2)
        forward(20)
        print("forward")
        time.sleep(3)
        turn(30)
        print("second turn")
        time.sleep(2)
        forward(20)
        print("forward")
        time.sleep(2.5)
        forward(0)
        land()
        print("land")
      
def battery():
    global current_time
    while True:
        if time.time() - current_time > 10:
            sent = sock.sendto(b'battery?', command_address)
            current_time = time.time()
batteryThread = threading.Thread(target=battery)
batteryThread.start()

def commands():
    sent = sock.sendto(b'command', command_address)
    sent = sock.sendto(b'battery?', command_address)
    global data
    streamon()

    while True:
        if data != "executed":
            msg = input().rstrip()
            if 'end' in msg:
                sent = sock.sendto(b'streamoff', command_address)
                print('...')
                sock.close()
                break
            msg = msg.encode(encoding="utf-8")
            sent = sock.sendto(msg, command_address)
#takeoff()
time.sleep(10)
commands()   
