import socket
import numpy as np
import cv2
import time
import threading

print('Setup socket')
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)      # For UDP
print('Setting addresses')
udp_host = '192.168.0.101'          # Host IP
udp_port = 9000                    # specified port to connect
command_address = ('192.168.10.1', 8889)
video_address = ('udp://192.168.10.1:11111')
print('Bind socket')
sock.bind(('',9000))

print('Entering SDK mode')
sock.sendto(b'command', command_address)
print('Streamon')
sock.sendto(b'streamon', command_address)
ack_rcv = True
bitCount = 6
rcv = b''
addr = ('',0)
s = b''
pc_ready = False


def vidCap():
    global s
    global pc_ready
    cap = cv2.VideoCapture(video_address)
    sock.sendto(b'pi2',(udp_host,udp_port))
    while True:
        ret = cap.grab()
        if pc_ready:
            print("Retrieving frame")
            ret, frame = cap.retrieve()
            frame = cv2.resize(frame, (672,504))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            s = frame.tobytes()
            pc_ready = False
        
def recv():
    global rcv
    global addr
    global pc_ready
    while True:
        rcv, addr = sock.recvfrom(1024)
        if rcv != b'ack':
            print("Received: " + rcv.decode(encoding="utf-8"))
        elif rcv == b'ready':
            pc_ready = True
        

vidThread = threading.Thread(target=vidCap)
vidThread.start()
rcvThread = threading.Thread(target=recv)
rcvThread.start()

while True:
    if len(s) == 338688:
        print("Frame in s")
        if(bitCount == 6):
            print("Storing s")
            data = s
            #print("Full frame sent")
            bitCount = 0
        else:
            print('We send')
            sock.sendto(data[bitCount*56448:(bitCount+1)*56448],(udp_host,udp_port))     # Sending message to UDP server
            ack_rcv = False
            bitCount += 1
            if bitCount == 6:
                print("Resetting s")
                s = b''
        while ack_rcv == False:
            if(rcv == b'ack'):
                #print("Acknowledgement received")
                rcv = b''
                addr = ('',0)
                ack_rcv = True
sock.close()