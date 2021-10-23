#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from datetime import datetime
from bluetooth import *
import os as os


from config import *

class Android():

    def __init__(self):
        print("Android starting to initialise")

        self.server_sock = None
        self.client_sock = None
        
        os.system("sudo hciconfig hci0 piscan")
        print("Finished BT initialising")

    def connect(self, uuid):
        try:
            self.server_sock = BluetoothSocket(RFCOMM)
            # self.server_sock.allow_reuse_address = True
            # self.server_sock = self.server_socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.server_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            self.server_sock.bind(("", RFCOMM_PORT))
            self.server_sock.listen(RFCOMM_PORT)
            port = self.server_sock.getsockname()[1]

            advertise_service(self.server_sock, "RPi-RFCOMM",
                              service_id=uuid,
                              service_classes=[uuid, SERIAL_PORT_CLASS],
                              profiles=[SERIAL_PORT_PROFILE], )

            print("-----------------------------------------")
            print("Waiting connection from RFCOMM channel %d" % port)

            self.client_sock, client_info = self.server_sock.accept()
            secure = client_info[0]

            print("Accepted connection from ", client_info)
            print("Connected to Android!")
            return 1
        except Exception as e:
            print("Bluetooth connection exception: %s" % str(e))
            try:
                print("%s" % str(e))
                self.client_sock.close()
                self.client_sock = None
            except:
                print("Error")
            return 0
    def current_time(self):
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f") + '\t'

    def disconnect(self):
        #disconnect client_socket 
        try:
            if self.client_sock is not None:
                self.client_sock.close()
                self.client_sock = None
            print("Android has been disconnected successfully")
        except Exception as e:
            print("Bluetooth disconnection exception: %s" % str(e))
        
    def disconnect_all(self):
        #disconnect both client_socket and server socket
        try:
            if self.client_sock is not None:
                self.client_sock.close()
                self.client_sock = None

            if self.server_sock is not None:
                self.server_sock.close()
                self.server_sock = None

            print("Android has been disconnected Successfully")

        except Exception as e:	
            print("Bluetooth disconnection exception: %s" % str(e))



    def reconnect(self):
        connected = 0
        while connected == 0:
            print("Attempting reconnection...")
            # self.disconnect()
            time.sleep(1)
            connected = self.connect(UUID)


    def write(self, msg):
        try:
            if msg == "":
                print("Socket WRITE: Closed. Skipped write.")
                return
            elif msg  == "REP":
                print("Socket WRITE: Repeat Read -- ")
                msg = self.read(timeout=None)
            

            self.client_sock.send(msg) #did not encode here
            
        except Exception as e:
            print("Bluetooth write exception: %s" % str(e))
            self.reconnect()


    def read(self):
        try:

            message = self.client_sock.recv(ANDROID_SOCKET_BUFFER_SIZE).decode('utf-8')
            print('From android:')
            print(message)

            if message is None:
                return None
            
            if len(message) > 0:
                return message

            


            return None
        except Exception as e:
           
            print("Bluetooth read exception: %s" % str(e))
            self.reconnect()
    


if __name__ == '__main__':

    android = Android()
    android.connect(UUID)

    try:
        while True:
            android.read()
            android.write(input("Socket WRITE: Opened.\nSend Message: "))

    except KeyboardInterrupt:
        print("Terminating the program now...")    