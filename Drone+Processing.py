import threading
import socket
import time
import cv2.cv2 as cv2
import numpy as np
import math

host = ''
port = 9000
locaddr = (host,port)
stream_state = False
frame = np.zeros((720,960,3),np.uint8)
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

def forward(vel):
    print("We're moving forward!")
    sent = sock.sendto(b'takeoff', command_address)
    sent = sock.sendto(b'rc 0 '+ str(vel).encode() + b' 0 0', command_address)

def rotation(tvel,vvel,rvel):
    print("We're yawing!")
    #sent = sock.sendto(b'takeoff', command_address)
    sent = sock.sendto(b'rc 0 '+ str(tvel).encode() + str(vvel).encode() + str(rvel).encode(), command_address)

    
def videoDisplay():
    global frame
    while stream_state:
        #New portion Image Processing
        scale_percent = 70  # percent of original size
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        # resize image
        resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        #Center Point
        x = width/2
        y = height/2
        center_coordinates = (int(x),int(y))
        radius = 3
        color = (0,0,255)
        thickness = -1
        cv2.circle(resized,center_coordinates,radius,color,thickness)
        cv2.imshow('original', resized)
        cv2.waitKey(1)

        #############################################################
        #########WALL AVOIDANCE######################################
        #############################################################

        #Median Blur
        medianBlur = cv2.medianBlur(resized, 45)
        cv2.imshow('Median Blur', medianBlur)
        cv2.waitKey(1)

        #Gresycale
        grey_scale = cv2.cvtColor(medianBlur, cv2.COLOR_BGR2GRAY)
        cv2.imshow('Grey Scale', grey_scale)
        cv2.waitKey(1)

        #Treshold
        ret,thresh1 = cv2.threshold(grey_scale,127,255,cv2.THRESH_BINARY)
        cv2.imshow('Treshold', thresh1)
        cv2.waitKey(1)

        # Closing
        closekernel = np.ones((15,15),np.uint8)
        closing = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, closekernel)
        cv2.imshow('Closing', closing)
        cv2.waitKey(1)

        # Blob Data
        n, labels, stats, _ = cv2.connectedComponentsWithStats(closing)
        print(n)
        #print(labels)
        print(stats[labels][4])


        #############################################################
        ##########OBSTACLE AVOIDANCE#################################
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
        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for c in contours:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            # print(cX,cY)

            list1 = [[int(x), cX],[int(y), cY]]
            # print(list1)

            matrix = np.array(list1)

            # print(vector)
            dilation2 = cv2.cvtColor(dilation, cv2.COLOR_GRAY2BGR)

            #Circles and Lines for dilation
            cv2.circle(dilation2,center_coordinates,radius,(0,0,255),thickness)
            cv2.drawContours(dilation2, contours, -1, (0, 255, 0), 3) 
            cv2.circle(dilation2, (cX, cY), 5, (255, 0, 0), -1)
            cv2.arrowedLine(dilation2, center_coordinates, (cX, cY), (0,0,255), 1)

            #Image distance
            dist =((x-cX)**2 + (y-cY)**2)**.5
            #print(dist)

            #Defining Quadrants 
            quadrant = 0

            if dist < 150:
                if cX < 336 and cY < 252:
                    quadrant = 1
                    #print("This point belongs to quadrant number " + str(quadrant))
                    # try:
                    #     rotation(2,10,100)
                    # except:
                    #     break                        
                
                elif 336 < cX  and cX < 675 and cY < 252:
                    quadrant = 2
                    #print("This point belongs to quadrant number " + str(quadrant))
                    # try:
                    #     rotation(2,10,-100)
                    # except:
                    #     break           

                elif cX < 336 and 252 < cY and cY < 504:
                    quadrant = 3
                    #print("This point belongs to quadrant number " + str(quadrant))
                    # try:
                        # rotation(2,-10,100)
                    # except:
                    #     break     

                elif 336 < cX and cX < 675 and 252 < cY and cY < 504:
                    quadrant = 4
                    #print("This point belongs to quadrant number " + str(quadrant))
                    # try:
                    #     rotation(2,-10,-100)
                    # except:
                    #     break     

            #elif dist > 150:
                #forward(25)

            #Circles and Lines for Original
            cv2.circle(resized,center_coordinates,radius,(0,0,255),thickness)
            cv2.drawContours(resized, contours, -1, (0, 255, 0), 3) 
            cv2.circle(resized, (cX, cY), 5, (255, 0, 0), -1)
            cv2.arrowedLine(resized, center_coordinates, (cX, cY), (0,0,255), 1)

            # cv2.imshow('Original', resized)
            # cv2.waitKey(1)
            # cv2.imshow('Final', dilation2)
            # cv2.waitKey(1)

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
      
commands()
