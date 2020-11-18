import threading
import socket
import time
import cv2
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
quadrant = "none"

distance_list = []
direction_list = []
time_flown = 0
distance_flown = 0
start = 0

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
    print("We're taking off!")
    sent = sock.sendto(b'takeoff', command_address)

def land():
    print("We're landing!")
    sent = sock.sendto(b'land', command_address)

def stop():
    print("We're stopping!")
    sent = sock.sendto(b'stop', command_address)

def simpleforward(vel):
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)

def forward(vel,time_int):
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)
    realvel = abs(vel)
    distance = realvel * time_int
    if vel > 0:
        print("We're moving forwards!")
        distance_list.append(distance)
        direction_list.append("forward")
    elif vel < 0:
        print("We're moving backwards!")
        distance_list.append(distance)
        direction_list.append("backward")
    time.sleep(time_int)
    if vel != 0:
        print("The distance flown was: " + str(distance) + "cm!")

def turn(tvel,time_tvel):
    sent = sock.sendto(b'rc '+ str(tvel).encode() + b' 0 0 0', command_address)
    realvel = abs(tvel)
    distance = realvel * time_tvel
    if tvel > 0:
        print("We're moving right!")
        distance_list.append(distance)
        direction_list.append("right")
    elif tvel < 0:
        print("We're moving left!")
        distance_list.append(distance)
        direction_list.append("left")
    time.sleep(time_tvel)
    if tvel != 0:
        print("The distance flown was: " + str(distance) + "cm!")

def right():
    stop()
    turn(30,5)
    stop()
    forward(30,10)
    stop()
    turn(-30,5)
    stop()
    simpleforward(30)
    #land()
    distance()

def left():
    stop()
    turn(-30,5)
    stop()
    forward(30,10)
    stop()
    turn(30,5)
    stop()
    forward(30,5)
    stop()
    land()
    distance()

def distance():
    for i in range(0,len(distance_list)):
        print(direction_list[i],distance_list[i])
        i += 1

def videoDisplay():
    global start
    start = time.time()
    global frame
    global resized
    global dilation
    global box
    global time_flown
    #simpleforward(10)
    while stream_state:
        quadrant = "none"
        #forward(30)
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
        # cv2.imshow('original', resized)

        #GaussianBlur
        blur = cv2.GaussianBlur(resized, (3, 3), 0)
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
                end = time.time()
                time_flown = end - start
                print(time_flown)
                distance_flown = 10 * time_flown
                print(distance_flown)
                start_point = (xList, yList)
                end_point = (xList+wList, yList+hList)
                color = (255, 0, 0)
                thickness = -1
                image = cv2.rectangle(final, start_point, end_point, color, thickness) 

                if cX < int(width/2) and areaList < 337500:
                    quadrant = "left"
                    left()
                    #print("This blob belongs to the " + quadrant + " side.")
                elif cX > int(width/2) and areaList < 337500:
                    quadrant = "right"
                    right()
                    #print("This blob belongs to the " + quadrant + " side.")
        cv2.imshow('Final', final)
        cv2.imshow('Original', resized)
        cv2.waitKey(20)
        
def battery():
    global current_time
    while True:
        if time.time() - current_time > 10:
            sent = sock.sendto(b'battery?', command_address)
            current_time = time.time()
batteryThread = threading.Thread(target=battery)
batteryThread.start()

def commands():
    time.sleep(10)
    sent = sock.sendto(b'command', command_address)
    sent = sock.sendto(b'battery?', command_address)
    global data
    streamon()
    #takeoff()
    
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













# blank_image = 255 * np.zeros(shape=[800,800,3],dtype=np.uint8)
# width, height = 800, 800

# #General Parameters
# radius = 3
# color = (0,0,255)
# thickness = -1
# line_thickness = 2
# #Drone 1 initial coordinates
# x1, y1 = 0, 200
# image1 = cv2.circle(blank_image, (x1,y1), radius, color, thickness)
# #Drone 1 initial coordinates
# x2, y2 = 0, 400
# image1 = cv2.circle(blank_image, (x2,y2), radius, color, thickness)
# #Drone 1 initial coordinates
# x3, y3 = 0, 600
# image1 = cv2.circle(blank_image, (x3,y3), radius, color, thickness)

# if distance_flown > 0 and quadrant == "none":
#     nextpoint = (distance_flown, 200)
#     cv2.line(blank_image, (x1, y1), nextpoint, (0, 255, 0), thickness=line_thickness)
#     start = 0

# cv2.imshow("White Blank", blank_image)
# cv2.waitKey(20)


# def testflight():
#     takeoff()
#     forwardtest(100)
#     stop()
#     righttest(100)
#     stop()
#     forwardtest(100)
#     stop()
#     lefttest(100)
#     stop()
#     land()
#     attitude()

# def testmovement():
#     print("Test Movement IN")
#     time.sleep(2)
#     forward(15,5)
#     forward(0,10)
#     forward(-10,10)
#     forward(0,2)
#     land()
#     print("Land")
#     print("Test Movement OUT")