import cv2.cv2 as cv2
import numpy as np
import time
import socket

frame = np.zeros((720,960), dtype=np.uint8)

command_address = ('192.168.10.1', 8889)
video_address = ('udp://192.168.10.1:11111')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 9000))

sock.sendto(b'command', command_address)
sock.sendto(b'streamon', command_address)

cap = cv2.VideoCapture(video_address)
time.sleep(2)
start = time.time()
for i in range(0, 120):
    ret, frame = cap.read()    

end = time.time()
seconds = end - start

print("Time elapsed: {0} seconds".format(seconds))

fps = 120 / seconds
print("Estimated frames per seconds: {0}".format(fps))

cap.release()

