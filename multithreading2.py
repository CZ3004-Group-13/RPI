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
from ultrasonic import *




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

    # def _reconnect_algo(self):
    #     self.algo.disconnect()

    #     #terminate all processes
    #     self.read_algo_process.terminate()
    #     self.write_process.terminate()
    #     self.write_android_process.terminate()

    #     #reconnect algo
    #     self.algo.connect()

    #     #Recreate all processes
    #     self.read_algo_process = Process(target=self._read_algo)
    #     self.read_algo_process.start()

    #     self.write_process = Process(target=self._write_target_)
    #     self.write_process.start()

    #     self.write_android_process = Process(target=self._write_android_)
    #     self.write_android_process.start()

    #     #Output in terminal
    #     print('Reconnected to Algo')

    def _read_imagerec(self):
        while True:
            try:
                raw_msg = self.imagerec.read()
                #[up, (73,104),55,115]
                #print(raw_msg)

                if raw_msg is None:
                    continue
                message_list = raw_msg.splitlines()

                for msg in message_list:

                    print('Msg from ImgRec: %s'%msg)

                    if len(msg) <=0:
                        continue

                    

                    #incomplete 041021 - implementing handling of IMGREC given msg


                    #TBC 041021

                    elif msg == 'Nothing detected...' or msg == 'Nothing detected!!!':
                        print('msg has nothing: %s'%msg)
                        self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,RPiToAlgorithm.NOTHING_DETECTED + NEWLINE)) #send out 'none'
                    
                    else:



                        splitmsg = msg.split('|') #split into diff 

                        print('splitted up msg is %s' %splitmsg)
                        #if msg == 'taking photo': #not necessary as ImgRec side will send out the de
                        #   time.sleep(10)
                        #  self.message_queue.put_nowait(self._formatted_("IMG",'s'))
                        #else:

                        and_msg = 'TARGET|'+splitmsg[0] +'|' +splitmsg[1]  #TARGET | obs_id | img_id
                        algo_msg = 'D'+splitmsg[0] +','+splitmsg[2] +','+splitmsg[3] #D obs_id | dist | position
                        #splitmsg[1] #tbc
                        #splitmsg[2] #tbc

                        print('msg to android %s'%and_msg)
                        print(type(and_msg))



                        self.msg_to_android_queue.put_nowait(and_msg + NEWLINE)
                        self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,algo_msg+NEWLINE ))
                    



                    # new_msg = msg[1:-1]
                    # #up, (73,104),55,115

                    # splitmsg = new_msg.split(",")
                    # #[up, (73, 104), 55, 115]

                    # msgid = splitmsg[0]

                    # msgx = splitmsg[1] #check if image on left or right?
                    # msgy = splitmsg[2]

                    # #distance - use height - h>190

                    # msgwidth = splitmsg[3]
                    # msgheight = splitmsg[4]


                   


                


            except Exception as e:
                print("Process of reading imageclient failed %s" % str(e))

    def _read_ultra(self):
        ultrasonic = Ultrasonic()
        values = [0,0,0] 
        while True:
            try:
                for i in range(3):
                    dist = ultrasonic.distance()
                    values[i] = dist
                    self.ultraDist.value = sum(values)/3
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
                        # self.stmIsReady.value = 1
                        self.msg_to_android_queue.put_nowait(msg+NEWLINE)
                    #self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg+ NEWLINE)) #check if header is correct
                    #self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg)) #check if header is correct


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

                    elif msg in (AndroidToSTM.ALL_MESSAGES or AndroidToRPi.CALIBRATE_SENSOR): #can change
                        if msg == AndroidToRPi.CALIBRATE_SENSOR:
                            self.message_queue.put_nowait(self._formatted_(STM_HEADER,RPiToSTM.CALIBRATE_SENSOR+NEWLINE)) 
                            #check if header is correct

                        else:
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
    
    """CHECK IF ALGO START FAST PATH ETC APPLIES"""

    # def _read_algo(self):
    #     while True:
    #         try:
    #             raw_msg = self.algo.read()
                
    #             if raw_msg is None:
    #                 continue
    #             message_list = raw_msg.split("|")
    #             #print('Test msg: %s' %message_list)


    #             for msg in message_list:
    #                 # print(len(msg))
    #                 # print(type(msg))
    #                 # print(msg)
    #                 print('inside read algo')

    #                 print('the front of the msg is %s' %str(msg[0]))

    #                 if len(msg) <=0:
    #                     continue

    #                 elif msg[0] == AndroidToSTM.ALL_MESSAGES:
    #                     print('sending msg to STM %s' %msg)
    #                     self.algo_to_stm_commands_queue.put_nowait(self._formatted_(STM_HEADER, msg))

                    
    #                 # elif msg[0] == AlgorithmToRPi.TAKE_PICTURE or msg[0] == AlgorithmToRPi.EXPLORATION_COMPLETE: #need to change this.
    #                 #     print("in loop")

    #                 #     self.algo_to_stm_commands_queue.put_nowait(self._formatted_("IMG",msg))
                    




    #                     #041021 change
    #                     # if self.image_count.value >=5:
    #                     #     self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,RPiToAlgorithm.DONE_IMG_REC)) #remove newline
                        
    #                     # else:

    #                     #     msg = msg[2:-1]
    #                     #     self.msg_to_android_queue.put_nowait(RPiToAndroid.STATUS_TAKING_PICTURE + NEWLINE) #change 300921

    #                     #     image = self._takepic()
    #                     #     print('Picture taken')
                    
    #                     #     self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, RPiToAlgorithm.DONE_TAKING_PICTURE)) #remove newline
    #                     #     self.image_queue.put_nowait([image,msg])
    #                     #     print('image queued ')
                    
    #                 # elif msg[0] == AlgorithmToAndroid.MDF_STRING:
    #                 #     self.msg_to_android_queue.put_nowait(msg[1:]+NEWLINE)
                    
    #                 elif msg == 'DONE':
    #                     time.sleep(1)
    #                     self.msg_to_android_queue.put_nowait(msg+NEWLINE)

    #                 else:
    #                     self.algo_to_stm_commands_queue.put_nowait(self._formatted_(STM_HEADER, msg))  #TO-DO check
                    
    #                     #self._forward_msg_algo_to_android(msg) #testing this so added 290921
    #                     #self.msg_to_android_queue.put_nowait(msg) #testing
                    
    #         except Exception as e:
    #             print("Process of reading algo failed %s" % str(e))

    #         """INCOMPLETE - TAKE PIC EXPLORATION MDF STRING?"""

    def _forward_msg_algo_to_android(self, message):
        messages_for_android = message.split("|")

        for message_android in messages_for_android:

            if len(message_android) <=0:
                continue

            elif message_android[0] == AlgorithmToAndroid.TURN_LEFT:
                self.msg_to_android_queue.put_nowait(RPiToAndroid.TURN_LEFT) #removed newline
            
            elif message_android[0] == AlgorithmToAndroid.TURN_RIGHT:
                self.msg_to_android_queue.put_nowait(RPiToAndroid.TURN_RIGHT) #remove newline
            
            elif message_android[0] == AlgorithmToAndroid.MOVE_FORWARD:
                num_steps_forward = int(messages_for_android.decode()[1:])

                print("Number of steps to move forward: %i" % num_steps_forward)
                for steps in range(num_steps_forward):
                    self.msg_to_android_queue.put_nowait(RPiToAndroid.MOVE_UP) #remove newline


            
    
    def _write_target_(self):
        while True:
            target = None
            
            try:
                # if self.stmIsReady.value:
                #     if not self.algo_to_stm_commands_queue.empty():
                #         message = self.algo_to_stm_commands_queue.get_nowait()
                #         target, payload = message['target'],message['payload']
                        
                #         if payload[0] == AlgorithmToRPi.TAKE_PICTURE or payload[0] == AlgorithmToRPi.EXPLORATION_COMPLETE:

                #             self.message_queue.put_nowait(self._formatted_('IMG',payload))


                #             # image = self.imageclient.read()


                #             # if self.image_count.value >=5:
                #             #     self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,RPiToAlgorithm.DONE_IMG_REC+ NEWLINE)) #remove newline
                            
                #             # else:
                #             #     payload = payload[2:-1]
                #             #     self.msg_to_android_queue.put_nowait(RPiToAndroid.STATUS_TAKING_PICTURE + NEWLINE) #change 300921
                                
                                

                #             #     image = self._takepic() 
                #             #     print('Picture taken')
                        
                #             #     self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, RPiToAlgorithm.DONE_TAKING_PICTURE+NEWLINE)) #remove newline
                #             #     self.image_queue.put_nowait([image,payload])
                #             #     print('image queued ')
                #         else:
                #             self.stm.write(payload)
                #             self.stmIsReady.value = 0
                #             print("Write to STM: %s" %payload)




                if not self.message_queue.empty(): #if not empty queue
                    message = self.message_queue.get_nowait()
                    target, payload = message['target'],message['payload']

                    #print("debug payload %s" %payload)

                    if target == STM_HEADER:
                        self.stm.write(payload)
                        print("Write to STM: %s" %payload)
                        #print('without stm connection')

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

                

