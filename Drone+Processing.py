import threading
import socket
import time
import cv2.cv2 as cv2
import numpy as np

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
        cv2.imshow('original', resized)
        cv2.waitKey(1)

        #GaussianBlur
        blur = cv2.GaussianBlur(resized, (3, 3), 0)
        #cv2.imshow('Gaussian Blur', blur)
        #cv2.waitKey(1)

        #HSV
        HSV = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
        #cv2.imshow('HSV', HSV)

        #Mask
        light_orange = (0, 0, 0)
        dark_orange = (180, 180, 130)
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

        #sobelx = cv2.Sobel(vertical,cv2.CV_8U,1,0,ksize=3)
        #cv2.imshow('Sobel', sobelx)

        #Opening
        kernelo= np.ones((31,31),np.uint8)
        opening = cv2.morphologyEx(vertical, cv2.MORPH_OPEN, kernelo)
        cv2.imshow('opening', opening)
        cv2.waitKey(1)

        kernele = np.ones((11,11),np.uint8)
        erosion = cv2.morphologyEx(opening, cv2.MORPH_ERODE, kernele)
        cv2.imshow('erosion', erosion)
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
      
commands()
