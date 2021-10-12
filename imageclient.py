import socket
import sys
import traceback
import errno
import time
from config import *

host = WIFI_IP
port = 3055

class ImageClient:
    

    def __init__(self, host= WIFI_IP, port=3055):
        self.host = host
        self.port = port

        self.client_sock = None
        self.socket = None
        self.address = None



        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Socket Established")

        try:
            self.socket.bind(('', self.port))
        except socket.error as e:
            print("Bind failed", e)
            sys.exit()

        print("Bind completed")

        self.socket.listen(3)
       
    # receive the first message from client, know the client address
    # print "ImageClient Connected"
    def connect(self):
        while True:
            trying = False
            try: 

                print("Waiting for connection from ImageClient...")

                if self.client_sock is None: 
                    self.client_sock, self.address = self.socket.accept()
                    print("Connected to ImageClient @ " + str(self.address) + "!")
                    trying = False

            except Exception as e:
                    print('Error connecting with Algorithm %s' % str(e))

                    if self.client_sock is not None:
                        self.client_sock.close()
                        self.client_sock = None
                    trying = True
                    
            if not trying:
                break
            print("Retrying Algorithm PC connection")


    def disconnect(self):
        try:
            self.socket.close()
        except Exception as e:
            print("ImageClient disconnection exception: %s" % str(e))

    def write(self, msg):
        try:
            print('To ImgRec %s' %msg.encode('utf-8'))
            self.client_sock.send(msg.encode('utf-8'))
            #self.client_sock.sendto(msg.encode('utf-8'), self.address)
        except socket.error as e:
            if isinstance(e.args, tuple):
                print("errno is %d" % e[0])
                if e[0] == errno.EPIPE:
                    # remote peer disconnected
                    print("Detected remote disconnect")
                else:
                    # for another error
                    pass
            else:
                print("socket error ", e)
            sys.exit()
        except IOError as e:
            print("ImageClient read exception", e)
            print(traceback.format_exc())
            pass

    def read(self):
        try:
            msg = self.client_sock.recv(1024).decode()
            if len(msg) >0:
                print('From ImgRec: %s'%msg)
                return msg
            return None
        except socket.error as e:
            if isinstance(e.args, tuple):
                print("errno is %d" % e[0])
                if e[0] == errno.EPIPE:
                    # remote peer disconnected
                    print("Detected remote disconnect")
                else:
                    # for another error
                    pass
            else:
                print("socket error ", e)
            sys.exit()

        except IOError as e:
            print("ImageClient read exception: ", e)
            print(traceback.format_exc())
            pass


# if __name__ == '__main__':
#     ImageClient = ImageClient()
#     try:
#         counter = 6
#         while True:
#             if counter == 0:
#                 ImageClient.write("s") # signal to stop  
#             ImageClient.write("t") # signal to take picture
#             print(ImageClient.read())
#             time.sleep(5)
#             print("TRYING TO WRITE")
#             counter -= 1
#             #ImageClient.write("")
#     except KeyboardInterrupt:
#         print("Terminating the program now...")
