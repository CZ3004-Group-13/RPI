#!/usr/bin/python
# -*- coding: utf-8 -*-
import serial
import time

from config import *


class STM():
    def __init__(self, serialport = SERIAL_PORT, baudrate=BAUD_RATE):
        self.serial_port=serialport
        self.baudrate = baudrate
        self.ser = 0
        self.STM_msg_length = 10
    
    def connect(self):
        # connect to serial port
        try:
            print("-------------------------------")
            print("Trying to connect to STM...")
            self.ser = serial.Serial(
              self.serial_port, 
              self.baudrate,
              parity=serial.PARITY_NONE,
              stopbits=serial.STOPBITS_ONE,
              bytesize=serial.EIGHTBITS, 
              timeout=None #timeout=3
            )
            time.sleep(1)

            if (self.ser != 0):
                print("Connected to STM!")
                #self.read() #remove this for test with stm code alone
            return 1

        except Exception as e:
            print("SERIAL_PORT")
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=3)
            # print "STM connection exception: %s" %str(e)
            return 1

    def write(self, msg):
        for i in range(self.STM_msg_length -len(msg)):
            msg = msg + '|'
        try:
            self.ser.write(msg.encode())  # write msg with | as end of msg
        except Exception as e:
            print("STM write exception: %s" % str(e))

    def read(self):
        try:
            #msg = self.ser.readline()  # read msg from stm sensors
            msg = self.ser.read(5)
            if len(msg) >0:
                return msg.decode('UTF-8').strip(u'\u0000') #strip null character
        except Exception as e:
            print("STM read exception: %s" % str(e))
            raise e
    def disconnect(self):
        try:
            if self.ser is not None:
                self.ser.close()
                self.ser = None

                print('Successfully closed connection with STM')
        except Exception as e:
            print("STM closed connection failed: %s" % str(e))

if __name__ == '__main__':
    stm = STM()
    stm.connect()
    count = 0
    print("attempt connect")
    while stm.ser.inWaiting() > 0:
        # stm.ser.read(1)
        pass
    try:
        print("attempting")

        stm.write("w50")
        
        # while True:
        #     stm.write('w50')
        #     if stm.read().strip() == "done":
        #         stm.write('s50')
        #         print(stm.read())
            # count+=1
            # print(count)

    except KeyboardInterrupt:
        print("Terminating the program now...")

"""if __name__ == '__main__':
    stm = STM()
    stm.connect()
    print("attempt connect")
    while stm.ser.inWaiting() > 0:
        stm.ser.read(1)
    try:
        print("attempting")
        # while True:
            # print(stm.read())

        ####### Test Straight Line #################################
        #! Tested on 3 Sep 2021 10.45am
        #! Checklist required: Straight 80cm - 100cm (8 - 10 Grids)
        GridUnit = 1.2 # speed 700 - 800

        print("F")
        stm.write("F")
        time.sleep(3*GridUnit)
        print("s")
        stm.write("s")
        time.sleep(3)


        print("r")
        stm.write("r")
        time.sleep(3)
        print("c")
        stm.write("c")
        time.sleep(3)

        
        print("l")
        stm.write("l")
        time.sleep(3)
        print("c")
        stm.write("c")
        time.sleep(3)

        print("F")
        stm.write("F")
        time.sleep(3*GridUnit)
        print("s")
        stm.write("s")
        time.sleep(3)
        #############################################################

        #####################################################################
        #! Checklist required: Turn 360deg -> for what speed and how long?
        ####### Test Turn Right (Not tested) ################################
        print("r")
        stm.write("r")
        time.sleep(3)

        print("f")
        stm.write("f")
        time.sleep(3)

        # Recalibrate?
        print("s")
        stm.write("s")
        time.sleep(3)
        print("c")
        stm.write("c")
        time.sleep(3)
        #########################################

        ####### Test Turn Left (Not tested) ######
        print("l")
        stm.write("l")
        time.sleep(3)

        print("f")
        stm.write("f")
        time.sleep(3)

        # Recalibrate?
        print("s")
        stm.write("s")
        time.sleep(3)
        print("c")
        stm.write("c")
        time.sleep(3)
        #########################################
    except KeyboardInterrupt:
        print("Terminating the program now...")"""