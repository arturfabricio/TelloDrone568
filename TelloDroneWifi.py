import socket
import cv2.cv2 as cv2




class DroneHandler:
    def __init__(self, address,driver):
        self.command_address = ('192.168.10.1', 8889)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET,2, driver)
        self.sock.bind(address)
        self.sock.sendto(b'command',command_address)
        self.sock.close()



drone1 = DroneHandler(('192.168.0.107', 9000,'wlp2s0'))
drone2 = DroneHandler(('192.168.0.104', 9000,'wlxd037459baaf1'))