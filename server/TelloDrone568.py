import threading
import socket
import time
import platform
import av
import numpy
import tellopy
import sys
import traceback
import cv2.cv2 as cv2  # for avoidance of pylint error

def connection():

    host = ''
    port = 9000
    locaddr = (host,port)
    i = range(5)

    #Create a UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    tello_address = ('192.168.10.1', 8889)

    #sock.bind(locaddr)

    def recv():
        while True:
            try:
                data, server = sock.recvfrom(1518)
                print(data.decode(encoding="utf-8"))
            except Exception:
                print ('\nExit..\n')
                break

    print ('Tello: command takeoff land flip forward back left right \r\n   up down cw ccw speed speed?\r\n')

    #recvThread create
    recvThread = threading.Thread(target=recv)
    recvThread.start()

def video():
    drone = tellopy.Tello()

    try:
        drone.connect()
        drone.wait_for_connection(60.0)

        retry = 3
        container = None
        while container is None and 0 < retry:
            retry -= 1
            try:
                container = av.open(drone.get_video_stream())
            except av.AVError as ave:
                print(ave)
                print('retry...')

        # skip first 300 frames
        frame_skip = 300
        while True:
            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                cv2.imshow('Original', image)
                cv2.waitKey(1)
                if frame.time_base < 1.0/60:
                    time_base = 1.0/60
                else:
                    time_base = frame.time_base
                frame_skip = int((time.time() - start_time)/time_base)
                    

    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        drone.quit()
        cv2.destroyAllWindows()

def commands():
    while True:
        try:
            sent = sock.sendto(b'command', tello_address)
            sent = sock.sendto(b'battery?', tello_address)
            print ('Wait for the ok')

            python_version = str(platform.python_version())
            version_init_num = int(python_version.partition('.')[0])
                #print (version_init_num)
            if version_init_num == 3:
                msg = input("").rstrip()
                #elif version_init_num == 2:
                #    msg = raw_input("").rstrip();

            if not msg:
                break

            if 'end' in msg:
                print('...')
                sock.close()
                break

                #Send data
            msg = msg.encode(encoding="utf-8")
            sent = sock.sendto(msg, tello_address)
            
        except KeyboardInterrupt:
            print ('\n...\n')
            sock.close()
            break

connection()
video()
commands()