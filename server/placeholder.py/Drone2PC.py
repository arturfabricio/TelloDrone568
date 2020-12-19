#Libraries needed:
import socket
import cv2.cv2 as cv2
import threading
import numpy as np

#Function for showing frame of the drones:
def showFrame():
    while True:
        cv2.imshow("Drone 1", drone1.frame)
        cv2.waitKey(1)

#Class handling drone connection, connection between the 2 PCs, fetching frames, receiving and sending commands to the drone. 
class DroneHandler:
    def __init__(self, _ID):
        self.ID = _ID
        self.frame = np.zeros((720,960), dtype=np.uint8)
        self.command_address = ('192.168.10.1', 8889)
        self.video_address = ('udp://192.168.10.1:11111')
        self.pc_address = (('192.168.0.108', 9000))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 9000))
        self.sock.sendto(b'command',self.command_address)
        self.fetchThread = threading.Thread(target=self.frameFetch)
        self.fetchThread.start()
        self.rcvThread = threading.Thread(target=self.rcv)
        self.rcvThread.start()
        
    def rcv(self): #Thread for receiving data from the partner PC.
        while True:
            recv, addr = self.sock.recvfrom(1024)
            print(recv)

    def frameFetch(self): #Thread for retrieving the frames from the drone.
        self.sock.sendto(b'streamon', self.command_address) #Initialize the videostream
        self.cap = cv2.VideoCapture(self.video_address)
        while True:
            self.ret, self.frame = self.cap.read()     

    def command(self, _command): #Sending the command to the partner PC.
        self.sock.sendto(_command.rstrip().encode(), self.command_address)
        self.sock.sendto(b"Command: " + _command.rstrip().encode() + b" sent to drone 2", self.pc_address)


drone1 = DroneHandler(1)
showThread = threading.Thread(target=showFrame)
showThread.start()
while True:
    txt = input()
    drone1.command(txt)

    
