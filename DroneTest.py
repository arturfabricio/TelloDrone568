import threading
import socket
import sys
import time
import cv2.cv2 as cv2
import os
import queue

host = ''
port = 9000
locaddr = (host,port)
stream_state = False
q = queue.Queue()
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

    cap = cv2.VideoCapture(video_address, cv2.CAP_FFMPEG)
    ret, frame = cap.read()
    q.put(frame)
    while ret:
        ret, frame = cap.read()
        q.put(frame)


def videoDisplay():
    while stream_state:
        if q.empty() != True:
            frame=q.get()
            cv2.imshow('feed', frame)
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
