#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import date
from multiprocessing import Process, Value, Queue, Manager
from typing import NewType


from android import *
from stm32 import *
from config import *
from protocols import *
from ultrasonic import *

import statistics

#Only used android, stm and ultrasonic


class Multithreading:

    def __init__(self):

        self.stm = STM() #connection to STM32
        self.android = Android() #connection to Android


        self.manager = Manager() #multiprocessing lib
        
        
        #message queue
        self.message_queue = self.manager.Queue()
        self.msg_to_android_queue =self.manager.Queue()


        #self.stmIsReady = self.manager.Value(True)
        self.stmIsReady = self.manager.Value('i', 1)
        
        self.ultraDist = self.manager.Value('i', 0)

        #Processes
        self.read_stm_process = Process(target=self._read_stm)
        self.read_android_process = Process(target=self._read_android)

        self.read_ultra_process = Process(target=self._read_ultra)


        self.write_process = Process(target=self._write_target_)
        self.write_android_process = Process(target=self._write_android_)

        self.status = Status.IDLE

        self.dropped_connection = Value('i',0) # 0 - stm, 1 - algorithm


    
    def start(self):
        try:
            self.stm.connect()
            self.android.connect(UUID)

            

            print("Connected to STM and ANDROID")

            self.read_stm_process.start()
            self.read_android_process.start()
            self.write_process.start()
            self.write_android_process.start()
            self.read_ultra_process.start()

            
            print('Started all processes')
            print('Multithreading started')

            
            

        
        except Exception as e:
            raise e
        self._allreconnection()

    def disconnect(self):
        self.android.disconnect_all()


        print('Multithread process has ended')
        
    
    def _allreconnection(self):

        print('You can reconnect to RPI after disconnecting now')

        while True:
            try:

                if not self.read_stm_process.is_alive():
                    self._reconnect_stm()

                if not self.read_android_process.is_alive():
                    self._reconnect_android()   

                if not self.write_process.is_alive():
                    if self.dropped_connection.value == 0:
                        self._reconnect_stm()
                    # elif self.dropped_connection.value == 1:
                    #     self._reconnect_algo()
                        
                        
                if not self.write_android_process.is_alive():
                    self._reconnect_android()
                



            except Exception as e:
                print('Error while reconnecting %s' % str(e))
                raise e

    
    def _reconnect_stm(self):
        self.stm.disconnect()

        #terminate all processes
        self.read_stm_process.terminate()
        self.write_process.terminate()
        self.write_android_process.terminate()

        #reconnect stm
        self.stm.connect()

        #Recreate all processes
        self.read_stm_process = Process(target=self._read_stm)
        self.read_stm_process.start()

        self.write_process = Process(target=self._write_target_)
        self.write_process.start()

        self.write_android_process = Process(target=self._write_android_)
        self.write_android_process.start()

        #Output in terminal
        print('Reconnected to STM')
        
    def _reconnect_android(self):
        self.android.disconnect()

        #terminate all processes
        self.read_android_process.terminate()
        self.write_process.terminate()
        self.write_android_process.terminate()

        #reconnect android
        self.android.connect()

        #Recreate all processes
        self.read_android_process = Process(target=self._read_android)
        self.read_android_process.start()

        self.write_process = Process(target=self._write_target_)
        self.write_process.start()

        self.write_android_process = Process(target=self._write_android_)
        self.write_android_process.start()

        #Output in terminal
        print('Reconnected to Android')



    def _read_ultra(self):
        ultrasonic = Ultrasonic()
        values = [] 
        while True:
            try:
                
                dist = ultrasonic.distance()
                values.append(dist)
                #once a min of 5 values are in
                if len(values) >= 5:
                    self.ultraDist.value = statistics.median(values)
                time.sleep(1)
            except KeyboardInterrupt:
                ultrasonic.cleanup()
            except Exception as e:
                print("Error with Ultra: %s" %str(e))
                


    def _read_stm(self):
        while True:
            try:
                raw_msg = self.stm.read().strip()

                if raw_msg is None:
                    continue
                message_list = raw_msg.splitlines()

                for msg in message_list:

                    if len(msg) <=0:
                        continue

                    print("Read from STM: %s" %msg)
                    if (msg == 'DONE'):

                        self.msg_to_android_queue.put_nowait(msg+NEWLINE)

            except Exception as e:
                print("Process of reading stm failed %s" % str(e))

    def _read_android(self):
        while True:
            try:
                raw_msg = self.android.read()
                

                if raw_msg is None:
                    continue
                message_list = raw_msg.splitlines()
                

                for msg in message_list:
                    #print("Test %s"%msg)
                    #print(type(msg))

                    if len(msg) <=0:
                        continue

                    elif msg in AndroidToSTM.ALL_MESSAGES: #can change
        
                        self.message_queue.put_nowait(self._formatted_(
                                STM_HEADER, msg))


                    else: 
                        print(msg[0:3])
                        if msg[0:3] == 'OBS':
                            self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,msg+ NEWLINE))

                        elif msg == AndroidToAlgorithm.DRAW_PATH:
                            #self.status = Status.FASTEST_PATH
                            self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg + NEWLINE))
                        
                        elif msg == AndroidToAlgorithm.RESET:
                            #self.status = Status.FASTEST_PATH
                            self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg + NEWLINE))

                        elif msg == AndroidToAlgorithm.START_IMGREC:
                            #self.status = Status.EXPLORING
                            self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,msg+NEWLINE))
                            
                        elif msg == AndroidToAlgorithm.START_FASTEST_PATH:
                            self.status = Status.FASTEST_PATH
                            # self.message_queue.put_nowait(self._formatted_(STM_HEADER, RPiToSTM.START_FASTEST_PATH + NEWLINE))

                            if self.ultraDist.value <=50:
                                distSend = 0
                            else:
                                distSend = self.ultraDist.value - 50
                            self.message_queue.put_nowait(self._formatted_(STM_HEADER,'T%.2f' %distSend))
                        else:
                            self.message_queue.put_nowait(self._formatted_(STM_HEADER, msg + NEWLINE))
                        print("Read from Android: %s" %msg)

                    #self.message_queue.put_nowait(self._formatted_(STM_HEADER, msg+"\n"))
                    
                    # """Android has no socket to connect and send to. Will be STM or Algo"""

            except Exception as e:
                print("Process of reading android failed %s" % str(e))
            
    
    def _write_target_(self):
        while True:
            target = None
            
            try:



                if not self.message_queue.empty(): #if not empty queue
                    message = self.message_queue.get_nowait()
                    target, payload = message['target'],message['payload']

                    if target == STM_HEADER:
                        self.stm.write(payload)
                        print("Write to STM: %s" %payload)
                
                    elif target == ALGORITHM_HEADER:
                        self.algo.write(payload)
                        print("Write to Algo: %s" %payload)
                    elif target == 'IMG':
                        self.imagerec.write(payload)
                        print('Write to IMGrec %s'%payload)
                    else:
                        print('Invalid target', target)


            
            except Exception as e:
                print('Process of writing target failed: %s' % str(e))

                if target == STM_HEADER:
                    self.dropped_connection.value = 0

                elif target == ALGORITHM_HEADER:
                    self.dropped_connection.value =1
                
                break

    def _write_android_(self):
        while True:
            try:
                if not self.msg_to_android_queue.empty():
                    msg = self.msg_to_android_queue.get_nowait()

                    self.android.write(msg)
                    print("Write to Android: %s"%msg)


            except Exception as e:
                print("Process of writing to android failed: %s" % str(e))
                break

   





    def _formatted_ (self, target, payload):
        return{'target':target, 'payload':payload}

                


