import socket
import numpy as np
import cv2.cv2 as cv2
import threading
import time

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)      # For UDP
rec  = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
data = b''
_addr = ('',0)
check1 = b''
check2 = b''
check3 = b''
ct = 1
counter = 0

udp_host = socket.gethostname()		    # Host IP
udp_port = 9000		                # specified port to connect


sock.bind((udp_host, udp_port))

class StreamHandler:
    def __init__(self, addr):
        self.addr = addr
        self.string = b''
        self.frame = np.zeros((504,672),dtype=np.uint8)
        self.full = False
        dataThread = threading.Thread(target=self.fetch)
        dataThread.start()
    def fetch(self):
        global _addr
        global data
        global ct
        while True:
            if self.addr == _addr:
                print("Packet received")
                self.string += data
                _addr = ('',0)
                sock.sendto(b'ack', self.addr)
                if len(self.string) == 338688:
                    print("Full frame")
                    self.frame = np.frombuffer(self.string, dtype=np.uint8)
                    self.frame = self.frame.reshape(504,672,1)
                    self.full = True
                    self.string = b''
                    data = b''
                    ct += 1
                    if ct > 2:
                        ct = 1


def rcv():
    global data
    global _addr
    while True:
        data, _addr = sock.recvfrom(56448)
    
streamOne = StreamHandler(('192.168.0.104', 9000))
streamTwo = StreamHandler(('192.168.0.105', 9000))
streamThree = StreamHandler(('192.168.0.106', 9000))

rcvThread = threading.Thread(target=rcv)
rcvThread.start()


while True:
    if data == b'pi2':
        print("Pi2 ready")
        check1 = data
        data = b''
    elif data == b'pi3':
        print("Pi3 ready")
        check2 = data
        data = b''
    if check1 == b'pi2' and check2 == b'pi3':
        print("Breaking")
        break
start_time = time.time()
while counter < 60:
    #if ct == 1:
     #   sock.sendto(b'ready',('192.168.0.104', 9000))
      #  while streamOne.full == False:
       # cv2.imshow('frames from drone(1)', streamOne.frame)
    if ct == 1:
        sock.sendto(b'ready',('192.168.0.105', 9000))
        while True:
            if streamTwo.full == True:
                data = b''
                print(streamTwo.full)
                streamTwo.full = False
                counter += 1
                break
        cv2.imshow('frames from drone(2)', streamTwo.frame)
    elif ct == 2:
        sock.sendto(b'ready',('192.168.0.106', 9000))
        while True:
            if streamThree.full == True:
                data = b''
                streamThree.full = False
                counter += 1
                break
        cv2.imshow('frames from drone(3)', streamThree.frame)

    cv2.waitKey(1)
end_time = time.time()

seconds = end_time - start_time
print("Time elapsed: {0}".format(seconds))

fps = 60/seconds
print("Estimated frames per second: {0}".format(fps))