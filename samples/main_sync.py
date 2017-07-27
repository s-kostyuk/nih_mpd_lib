#!/usr/bin/env python

import socket


TCP_IP = '127.0.0.1'
TCP_PORT = 6600
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

# Returns something like this: b'OK MPD 0.19.0\n'
data = s.recv(BUFFER_SIZE)  # type: bytes

if data.startswith(b'OK'):
    print("Connection succeed: ", data)

idle_command_string = "idle\n"

try:
    data_counter = 0
    while True:
        # All communication data is encoded in UTF-8
        s.send(idle_command_string.encode(encoding='utf-8'))

        # Returns something like this: b'changed: player\nOK\n'
        data = s.recv(BUFFER_SIZE)  # type: bytes

        print(data_counter, "Received: ", data, flush=True)

        data_counter += 1

except KeyboardInterrupt:
    pass

finally:
    s.close()
