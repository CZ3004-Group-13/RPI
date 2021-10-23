#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import date
from multiprocessing import Process, Value, Queue, Manager
from typing import NewType


from android import *
from stm32 import *
from algo import *
from config import *
from protocols import *


from imageclient import *  #for imageclient socket



class Multithreading:

    def __init__(self, image_processing_server_url: str=None):

        self.stm = STM() #connection to STM32
        self.algo = Algorithm() #connection to Algo side
        self.android = Android() #connection to Android

        #added in a socket client to receive and send msg from pc running image rec
        self.imagerec = ImageClient()

        self.manager = Manager() #multiprocessing lib
        
        
        #message queue
        self.message_queue = self.manager.Queue()
        self.msg_to_android_queue =self.manager.Queue()
        self.algo_to_stm_commands_queue = self.manager.Queue()


        self.stmIsReady = self.manager.Value('i', 1)

        #Processes
        self.read_stm_process = Process(target=self._read_stm)
        self.read_algo_process = Process(target=self._read_algo)
        self.read_android_process = Process(target=self._read_android)

        #Image Client reading process
        self.read_imagerec_process = Process(target=self._read_imagerec)

        self.write_process = Process(target=self._write_target_)
        self.write_android_process = Process(target=self._write_android_)

        self.status = Status.IDLE

        self.dropped_connection = Value('i',0) # 0 - stm, 1 - algorithm

 
    
    def start(self):
        try:
            #Connecting of all components
            self.stm.connect()
            self.algo.connect()
            self.android.connect(UUID)
            self.imagerec.connect()

            

            print("Connected to STM, ALGO and ANDROID")

            #Starting of all processes
            self.read_stm_process.start()
            self.read_algo_process.start()
            self.read_android_process.start()
            self.write_process.start()
            self.write_android_process.start()

            self.read_imagerec_process.start()

            
            print('Started all processes')
            print('Multithreading started')

        
        except Exception as e:
            raise e
        self._allreconnection()

    def disconnect(self):
        self.algo.disconnect_all()
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
                
                if not self.read_algo_process.is_alive():
                    self._reconnect_algo()

                if not self.write_process.is_alive():
                    if self.dropped_connection.value == 0:
                        self._reconnect_stm()
                    elif self.dropped_connection.value == 1:
                        self._reconnect_algo()
                        
                        
                if not self.write_android_process.is_alive():
                    self._reconnect_android()
                
                if not self.read_imagerec_process.is_alive():
                    self.read_imagerec_process.terminate()



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

    def _reconnect_algo(self):
        self.algo.disconnect()

        #terminate all processes
        self.read_algo_process.terminate()
        self.write_process.terminate()
        self.write_android_process.terminate()

        #reconnect algo
        self.algo.connect()

        #Recreate all processes
        self.read_algo_process = Process(target=self._read_algo)
        self.read_algo_process.start()

        self.write_process = Process(target=self._write_target_)
        self.write_process.start()

        self.write_android_process = Process(target=self._write_android_)
        self.write_android_process.start()

        #Output in terminal
        print('Reconnected to Algo')

    def _read_imagerec(self):
        while True:
            try:
                raw_msg = self.imagerec.read()
                
                if raw_msg is None:
                    continue
                message_list = raw_msg.splitlines()

                for msg in message_list:

                    print('Msg from ImgRec: %s'%msg) #for debugging

                    if len(msg) <=0:
                        continue

                    #msg sent from server is 'Nothing detected...' or 'Nothing detected!!!'
                    elif msg == 'Nothing detected...' or msg == 'Nothing detected!!!':
                        print('msg has nothing: %s'%msg)
                        self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,RPiToAlgorithm.NOTHING_DETECTED + NEWLINE)) #send out 'none'
                    
                    else:



                        splitmsg = msg.split(MESSAGE_SEPARATOR) #split into diff 

                        print('splitted up msg is %s' %splitmsg)
                        
                        and_msg = 'TARGET|'+splitmsg[0] +'|' +splitmsg[1]  #TARGET | obs_id | img_id
                        algo_msg = 'D'+splitmsg[0] +','+splitmsg[2] +','+splitmsg[3] #D obs_id | dist | position
                        
                        print('msg to android %s'%and_msg)
                        print(type(and_msg))



                        self.msg_to_android_queue.put_nowait(and_msg + NEWLINE)
                        self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,algo_msg+NEWLINE ))
                    


                   


                


            except Exception as e:
                print("Process of reading imageclient failed %s" % str(e))

    



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
                    if (msg == 'done'):
                        self.stmIsReady.value = 1
                    #self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg+ NEWLINE)) #check if header is correct
                   

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
                        print(msg[0:3]) #for debugging
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
                                self.message_queue.put_nowait(self._formatted_(STM_HEADER, RPiToSTM.START_FASTEST_PATH + NEWLINE))


                        elif msg == AlgorithmToRPi.TAKE_PICTURE: #put this here for testing take pic
                                print('entered this loop check')
                                self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, AlgorithmToRPi.TAKE_PICTURE + NEWLINE))
                        
                        else:
                            self.message_queue.put_nowait(self._formatted_(STM_HEADER, msg + NEWLINE))
                        print("Read from Android: %s" %msg)

                    
            except Exception as e:
                print("Process of reading android failed %s" % str(e))
    

    def _read_algo(self):
        while True:
            try:
                raw_msg = self.algo.read()
                
                if raw_msg is None:
                    continue
                message_list = raw_msg.split(MESSAGE_SEPARATOR)


                for msg in message_list:
                    # print(len(msg)) #for debugging
                    # print(type(msg))
                    # print(msg)
                    print('inside read algo')

                    print('the front of the msg is %s' %str(msg[0]))

                    if len(msg) <=0:
                        continue

                    elif msg[0] == AndroidToSTM.ALL_MESSAGES:
                        print('sending msg to STM %s' %msg)
                        self.algo_to_stm_commands_queue.put_nowait(self._formatted_(STM_HEADER, msg))

                    
                    elif msg[0] == AlgorithmToRPi.TAKE_PICTURE or msg[0] == AlgorithmToRPi.EXPLORATION_COMPLETE: #need to change this.
                        print("in loop")

                        self.algo_to_stm_commands_queue.put_nowait(self._formatted_("IMG",msg))
                    
                    elif msg == 'DONE':
                        time.sleep(1)
                        self.msg_to_android_queue.put_nowait(msg+NEWLINE)

                    else:
                        self.algo_to_stm_commands_queue.put_nowait(self._formatted_(STM_HEADER, msg))  #TO-DO check
                    
                        #self.msg_to_android_queue.put_nowait(msg) #testing
                    
            except Exception as e:
                print("Process of reading algo failed %s" % str(e))


            
    
    def _write_target_(self):
        while True:
            target = None
            
            try:
                if self.stmIsReady.value:
                    if not self.algo_to_stm_commands_queue.empty():
                        message = self.algo_to_stm_commands_queue.get_nowait()
                        target, payload = message['target'],message['payload']
                        
                        if payload[0] == AlgorithmToRPi.TAKE_PICTURE or payload[0] == AlgorithmToRPi.EXPLORATION_COMPLETE:

                            self.message_queue.put_nowait(self._formatted_('IMG',payload))

                        else:
                            self.stm.write(payload)
                            self.stmIsReady.value = 0
                            print("Write to STM: %s" %payload)


                if not self.message_queue.empty(): #if not empty queue
                    message = self.message_queue.get_nowait()
                    target, payload = message['target'],message['payload']

                    #print("debug payload %s" %payload)

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

                


