import socket
import time
command_address = ('192.168.0.1', 8889)


print("Binding Socket 1")
drone1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
drone1.setsockopt(socket.SOL_SOCKET, 2, b'wlp20sf3')
print("End bind 1")

print("binding drone 2")
drone2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
drone2.setsockopt(socket.SOL_SOCKET, 2, b'wlxd037459baaf1')
print("end bind 2")

print("entering SDK mode")
drone1.sendto('command'.encode(), 0, ('192.168.10.1', 8889))
print("entering SDK mode")
drone2.sendto('command'.encode(), 0, ('192.168.10.1', 8889))

print("takeoff")
drone1.sendto('takeoff'.encode(), 0, ('192.168.10.1', 8889))
drone2.sendto('takeoff'.encode(), 0, ('192.168.10.1', 8889))

time.sleep(5)

print("entering SDK mode")
drone1.sendto('command'.encode(), 0, ('192.168.10.1', 8889))
print("entering SDK mode")
drone2.sendto('command'.encode(), 0, ('192.168.10.1', 8889))

print("landing")
drone1.sendto('land'.encode(), 0, ('192.168.10.1', 8889))
print("landing")
drone2.sendto('land'.encode(), 0, ('192.168.10.1', 8889))

drone1.close()
drone2.close()