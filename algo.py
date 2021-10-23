#!/usr/bin/python
# -*- coding: utf-8 -*-
from sys import modules
import socket

from config import *


class Algorithm:
    def __init__(self, host=WIFI_IP, port = WIFI_PORT):

        #initialisation of ports
        self.host = host
        self.port = port

        self.client_sock = None
        self.socket = None
        self.address = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host,self.port))
        self.socket.listen(1)

    
        print("Algo initialising")

    def connect(self):
        while True:
            trying = False

            try:
                print('Establishing connection with PC')

                if self.client_sock is None:
                    self.client_sock, self.address = self.socket.accept()
                    print('Successfully connected with Algorithm: %s' % str(self.address))
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
        #disconnect client_socket

        try:
            if self.client_sock is not None:
                self.client_sock.close()
                self.client_sock = None
        
            print('Algo disconnected successfully')
        
        except Exception as e:
            print('Algorithm PC disconnection failed: %s' % str(e))
        
    def disconnect_all(self):
        #disconnect both client_socket and socket itself

        try:
            if self.client_sock is not None:
                self.client_sock.close()
                self.client_sock = None

            if self.socket is not None:
                self.socket.close()
                self.socket = None

            print("Algorithm disconnected Successfully")

        except Exception as error:
            print("Algorithm disconnect failed: %s" %str(error))

    
    def write(self, message):
        try:
            print('To Algorithm: ')
            print(message.encode('utf-8'))
            self.client_sock.send(message.encode('utf-8')) #send encoded message

        except Exception as e:
            print('Algorithm PC write failed: %s' % str(e))
            raise e


        
    def read(self):
        #read function for algorithm

        try:
            message =  self.client_sock.recv(ALGO_SOCKET_BUFFER_SIZE).decode() #size is set to 1024

            if len(message) >0:
                print('From Algo:')
                print(message)
                return message
            return None
        
        except Exception as e:
            print('Algorithm PC read failed: %s' %str(e))
            raise e
        
    


