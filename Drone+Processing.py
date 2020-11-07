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
        #New portion Image Processing
        scale_percent = 70  # percent of original size
        width = int(frame.shape[1] * scale_percent / 100)
        # print(width) 
        height = int(frame.shape[0] * scale_percent / 100)
        # print(height)
        #print(width*height)
        dim = (width, height)
        # resize image
        resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        #Center Point
        xreal = width/2
        yreal = height/2
        cX_IF = 0
        cY_IF = 0
        center_coordinates = (int(xreal),int(yreal))
        radius = 3
        color = (0,0,255)
        thickness = -1
        cv2.circle(resized,center_coordinates,radius,color,thickness)
        cv2.imshow('original', resized)
        cv2.waitKey(1)

        #############################################################
        ########## OBSTACLE AVOIDANCE ###############################
        #############################################################

        #GaussianBlur
        blur = cv2.GaussianBlur(resized, (11, 11), 0)
        # cv2.imshow('Gaussian Blur', blur)
        # cv2.waitKey(1)

        #HSV
        HSV = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
        # cv2.imshow('HSV', HSV)
        # cv2.waitKey(1)

        #Mask
        #Hue -> [0,179]
        #Saturation -> [0,255]
        #Value -> [0,255]
        threshold1 = (0, 0, 0)
        threshold2 = (110, 110, 100)
        mask = cv2.inRange(HSV, threshold1, threshold2)
        # cv2.imshow('mask', mask)
        # cv2.waitKey(1)

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
        # cv2.imshow("vertical", vertical)
        # cv2.waitKey(1)

        #Opening
        kernel = np.ones((15,15),np.uint8)
        opening = cv2.morphologyEx(vertical, cv2.MORPH_OPEN, kernel)
        # cv2.imshow('opening', opening)
        # cv2.waitKey(1)

        #Erosion
        kernel1 = np.ones((3,19),np.uint8)
        erosion = cv2.morphologyEx(vertical, cv2.MORPH_ERODE, kernel1)
        # cv2.imshow('erosion', erosion)
        # cv2.waitKey(1)

        #New portion of code for BLOB detection and line drawing
        kernel2 = np.ones((55,35),np.uint8)
        dilation = cv2.morphologyEx(erosion, cv2.MORPH_DILATE, kernel2)
        # cv2.imshow('dilation', dilation)
        # cv2.waitKey(1)

        #contours[0] = 0
        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if len(contours) > 0:
            cnt = contours[0]
            M = cv2.moments(cnt)
            area = cv2.contourArea(cnt)

            dilation2 = cv2.cvtColor(dilation, cv2.COLOR_GRAY2BGR)

            for c in contours:
                box = np.zeros((504,672,3),np.uint8)
                rect = cv2.boundingRect(c)
                height = rect[3]
                #print(height)
                area = cv2.contourArea(c)
                x,y,w,h = rect
                cX = int(x+(w/2))
                cY = int(y+(h/2))
                dist = int(((xreal-cX)**2 + (yreal-cY)**2)**.5)
                #print(dist)
                # radius = int(200)
                # cv2.circle(box,center_coordinates,radius,(0,255,0),2)
                cv2.circle(box,center_coordinates,radius,color,thickness)
                #print(area)
                decision = False
                if rect[3] > 50 and area < 60000.0:
                    if dist < 300:
                        #print(rect)
                        #print(height)
                        print(" ")
                        cX_IF = int(rect[0] + (rect[2]/2))
                        print(cX_IF)
                        cY_IF = int(rect[1] + (rect[3]/2))
                        print(cY_IF)
                        new_coordinates = (int(cX_IF),int(cY_IF))
                        cv2.rectangle(dilation2,(x,y),(x+w,y+h),(0,255,0),2)
                        cv2.circle(box,center_coordinates,radius,(0,255,0),2)
                        cv2.putText(dilation2,"YES",(x+w+10,y+h),0,0.3,(0,255,0))
                        cv2.rectangle(box,(x,y),(x+w,y+h),(0,255,0),2)
                        cv2.putText(box,"YES",(x+w+10,y+h),0,1,(0,255,0))
                        cv2.arrowedLine(box, center_coordinates, (cX_IF, cY_IF), (0,0,255), 1)
                        decision = True

                        #print(int(width/2))
                        #print(int(height/2))

                        if cX_IF < int(width/2) and cY_IF < int(height/2):
                            quadrant = 1
                            print("This point belongs to quadrant number " + str(quadrant))                
                        
                        elif int(width/2) < cX_IF  and cX_IF < int(width) and cY_IF < int(height/2):
                            quadrant = 2
                            print("This point belongs to quadrant number " + str(quadrant))

                        elif cX_IF < int(width/2) and int(height/2) < cY_IF and cY_IF < height:
                            quadrant = 3
                            print("This point belongs to quadrant number " + str(quadrant))

                        elif int(width/2) < cX_IF and cX_IF < width and int(height/2) < cY_IF and cY_IF < height:
                            quadrant = 4
                            print("This point belongs to quadrant number " + str(quadrant))
                else:
                    decision = False
                    break           
        else:
            print("Sorry No contour Found.")
    

        decision1 = input()

        if decision1 == True:
            forward(0)
            print("forward")
            time.sleep(1000)
            turn(-30)
            print("first turn")
            time.sleep(5000)
            forward(20)
            print("forward")
            time.sleep(5000)
            turn(30)
            print("second turn")
            time.sleep(5000)
            forward(20)
            print("forward")
            time.sleep(2500)
            forward(0)
            land()
            print("land")


        cv2.imshow("Show", dilation2)
        cv2.waitKey(1)
        cv2.imshow("box", box)
        cv2.waitKey(1)

            

        
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

takeoff()
commands()























            # #############################################################
        # #########WALL AVOIDANCE######################################
        # #############################################################

        # #Median Blur
        # medianBlur = cv2.medianBlur(resized, 45)
        # # cv2.imshow('Median Blur', medianBlur)
        # # cv2.waitKey(1)

        # #Gresycale
        # grey_scale = cv2.cvtColor(medianBlur, cv2.COLOR_BGR2GRAY)
        # # cv2.imshow('Grey Scale', grey_scale)
        # # cv2.waitKey(1)

        # #Treshold
        # ret,thresh1 = cv2.threshold(grey_scale,127,255,cv2.THRESH_BINARY)
        # # cv2.imshow('Treshold', thresh1)
        # # cv2.waitKey(1)

        # # Closing
        # closekernel = np.ones((15,15),np.uint8)
        # closing = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, closekernel)
        # #cv2.imshow('Closing', closing)
        # #cv2.waitKey(1)

        # # Blob Data
        # n, labels, stats, _ = cv2.connectedComponentsWithStats(closing)

        # area = stats[labels,cv2.CC_STAT_AREA]
        # #print(area[0][0])




        #     while stream_state:
        # # cv2.imshow('resized', resized)
        # # cv2.waitKey(1)
        # cv2.imshow('dilation', dilation)
        # cv2.waitKey(1)

        # #BLOB detector
        # params = cv2.SimpleBlobDetector_Params()

        # params.filterByArea = True
        # params.minArea = 300
        # params.maxArea = 338688
        # params.filterByColor = True
        # params.blobColor = 255

        # ver = (cv2.__version__).split('.')
        # if int(ver[0]) < 3 :
        #     detector = cv2.SimpleBlobDetector(params)
        # else: 
        #     detector = cv2.SimpleBlobDetector_create(params)

        # keypoints = detector.detect(dilation)
        # print(keypoints)
        # im_with_keypoints = cv2.drawKeypoints(dilation, keypoints, np.array([]), (0,0,255), cv2.DFT_REAL_OUTPUT)

        # cv2.imshow("final",im_with_keypoints)       