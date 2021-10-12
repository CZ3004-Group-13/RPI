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

#For Image Recog
import cv2
import imagezmq

from imageclient import * 


from picamera import PiCamera
from picamera.array import PiRGBArray


class Multithreading:

    def __init__(self, image_processing_server_url: str=None):

        self.stm = STM() #connection to STM32
        self.algo = Algorithm() #connection to Algo side
        self.android = Android() #connection to Android

        #011021 change
        #self.imagerec = ImageClient()

        self.manager = Manager() #multiprocessing lib
        
        
        #message queue
        self.message_queue = self.manager.Queue()
        self.msg_to_android_queue =self.manager.Queue()
        self.algo_to_stm_commands_queue = self.manager.Queue()


        #self.stmIsReady = self.manager.Value(True)
        self.stmIsReady = self.manager.Value('i', 1)

        #Processes
        self.read_stm_process = Process(target=self._read_stm)
        self.read_algo_process = Process(target=self._read_algo)
        self.read_android_process = Process(target=self._read_android)

        #self.read_imagerec_process = Process(target=self._read_imagerec)

        self.write_process = Process(target=self._write_target_)
        self.write_android_process = Process(target=self._write_android_)

        self.status = Status.IDLE

        self.dropped_connection = Value('i',0) # 0 - stm, 1 - algorithm

        self.image_process = Process(target=self._process_pic)

        self.image_queue = self.manager.Queue()

        self.image_processing_server_url = image_processing_server_url

        self.image_count = self.manager.Value('i',0)

        #300921 change

        self.image_process = None 
        print(image_processing_server_url)

        if image_processing_server_url is not None:
            print('inside image processing server')
            
            self.image_process = Process(target=self._process_pic)

            self.image_queue = self.manager.Queue()

            self.image_processing_server_url = image_processing_server_url

            self.image_count = self.manager.Value('i',0)

    
    def start(self):
        try:
            self.stm.connect()
            self.algo.connect()
            self.android.connect(UUID)

            

            print("Connected to STM, ALGO and ANDROID")

            self.read_stm_process.start()
            self.read_algo_process.start()
            self.read_android_process.start()
            self.write_process.start()
            self.write_android_process.start()
            
            self.image_process.start() #300921 change

            # if self.image_process is not None:
            #     self.image_process.start()
            #     print('image_process started')
            
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

                if self.image_process is not None and not self.image_process.is_alive():
                   self.image_process.terminate()



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
                raw_msg = self.stm.read()
                #[up, (73,104),55,115]

                if raw_msg is None:
                    continue
                message_list = raw_msg.splitlines()

                for msg in message_list:

                    if len(msg) <=0:
                        continue

                    new_msg = msg[1:-1]
                    #up, (73,104),55,115

                    splitmsg = new_msg.split(",")
                    #[up, (73, 104), 55, 115]

                    msgid = splitmsg[0]

                    msgx = splitmsg[1] #check if image on left or right?
                    msgy = splitmsg[2]

                    #distance - use height - h>190

                    msgwidth = splitmsg[3]
                    msgheight = splitmsg[4]


                   


                    print("Read from STM: %s" %msg)
                    if (msg == 'done'):
                        self.stmIsReady.value = 1
                    self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg)) #check if header is correct
                    #self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg)) #check if header is correct


            except Exception as e:
                print("Process of reading stm failed %s" % str(e))

    



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
                    self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, msg)) #check if header is correct
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


                        elif msg == AndroidToAlgorithm.START_EXPLORATION:
                                self.status = Status.EXPLORING
                                self.message_queue.put_nowait(self._formatted_(STM_HEADER,RPiToSTM.START_EXPLORATION + NEWLINE))
                            
                        elif msg == AndroidToAlgorithm.START_FASTEST_PATH:
                                self.status = Status.FASTEST_PATH
                                self.message_queue.put_nowait(self._formatted_(STM_HEADER, RPiToSTM.START_FASTEST_PATH + NEWLINE))

                        elif msg == AlgorithmToRPi.TAKE_PICTURE: #put this here for testing take pic
                                print('entered this loop check')
                                self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, AlgorithmToRPi.TAKE_PICTURE + NEWLINE))
                        
                        else:
                            self.message_queue.put_nowait(self._formatted_(STM_HEADER, msg + NEWLINE))
                        print("Read from Android: %s" %msg)

                    #self.message_queue.put_nowait(self._formatted_(STM_HEADER, msg+"\n"))
                    
                    """Android has no socket to connect and send to. Will be STM or Algo"""

            except Exception as e:
                print("Process of reading android failed %s" % str(e))
    
    """CHECK IF ALGO START FAST PATH ETC APPLIES"""

    def _read_algo(self):
        while True:
            try:
                raw_msg = self.algo.read()
                
                if raw_msg is None:
                    continue
                message_list = raw_msg.split("|")
                #print('Test msg: %s' %message_list)


                for msg in message_list:
                    # print(len(msg))
                    # print(type(msg))
                    # print(msg)
                    print('inside read algo')

                    if len(msg) <=0:
                        continue

                    elif msg[0] == AndroidToSTM.ALL_MESSAGES:
                        self.algo_to_stm_commands_queue.put_nowait(self._formatted_(STM_HEADER, msg))

                    
                    elif msg == AlgorithmToRPi.TAKE_PICTURE and not self.algo_to_stm_commands_queue.empty: #need to change this.
                        print("in loop")


                        if self.image_count.value >=5:
                            self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,RPiToAlgorithm.DONE_IMG_REC)) #remove newline
                        
                        else:

                            msg = msg[2:-1]
                            self.msg_to_android_queue.put_nowait(RPiToAndroid.STATUS_TAKING_PICTURE + NEWLINE) #change 300921

                            image = self._takepic()
                            print('Picture taken')
                    
                            self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, RPiToAlgorithm.DONE_TAKING_PICTURE)) #remove newline
                            self.image_queue.put_nowait([image,msg])
                            print('image queued ')
                            
                    elif msg == AlgorithmToRPi.EXPLORATION_COMPLETE:
                        self.status = Status.IDLE
                        self.image_queue.put_nowait(cv2.imread(STOPPING_IMAGE), "-1,-1|-1,-1|-1,-1")
                    
                    elif msg[0] == AlgorithmToAndroid.MDF_STRING:
                        self.msg_to_android_queue.put_nowait(msg[1:]+NEWLINE)
                    
                    else:
                        self.algo_to_stm_commands_queue.put_nowait(self._formatted_(STM_HEADER, msg))  #TO-DO check
                    
                        #self._forward_msg_algo_to_android(msg) #testing this so added 290921
                        #self.msg_to_android_queue.put_nowait(msg) #testing
                    
            except Exception as e:
                print("Process of reading algo failed %s" % str(e))

            """INCOMPLETE - TAKE PIC EXPLORATION MDF STRING?"""

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
                if self.stmIsReady.value:
                    if not self.algo_to_stm_commands_queue.empty():
                        message = self.algo_to_stm_commands_queue.get_nowait()
                        target, payload = message['target'],message['payload']
                        
                        if payload == AlgorithmToRPi.TAKE_PICTURE:

                            #image = self.imageclient.read()


                            if self.image_count.value >=5:
                                self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER,RPiToAlgorithm.DONE_IMG_REC+ NEWLINE)) #remove newline
                            
                            else:
                                payload = payload[2:-1]
                                self.msg_to_android_queue.put_nowait(RPiToAndroid.STATUS_TAKING_PICTURE + NEWLINE) #change 300921
                                
                                

                                image = self._takepic() 
                                print('Picture taken')
                        
                                self.message_queue.put_nowait(self._formatted_(ALGORITHM_HEADER, RPiToAlgorithm.DONE_TAKING_PICTURE+NEWLINE)) #remove newline
                                self.image_queue.put_nowait([image,payload])
                                print('image queued ')
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
                        #print('without stm connection')
                    elif target == ALGORITHM_HEADER:
                        self.algo.write(payload)
                        print("Write to Algo: %s" %payload)
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

    def _takepic(self):
        try:
            

            start_time = datetime.now()

            camera = PiCamera(resolution=(1920,1080)) #tbc
            rawCam = PiRGBArray(camera)

            #delay
            time.sleep(0.1)

            camera.capture(rawCam,format=IMAGE_FORMAT)
            image = rawCam.array
            camera.close()

            print("Time taken to take picture: " +str(datetime.now() - start_time)+'seconds')

        except Exception as e:
            print("Error when taking picture: %s" % str(e))

        return image
    
    def _process_pic(self):


        image_sender = imagezmq.ImageSender(
            connect_to= self.image_processing_server_url
        )
        print('connected to imagezmq hub')
        image_id_list =[]
        while True:
            try:
                if not self.image_queue.empty():
                    start_time = datetime.now()

                    image_message = self.image_queue.get_nowait()
                    print(image_message)
                    print(type(image_message))

                    obstacle_coordinates = image_message[1]

                    reply = image_sender.send_image('image from RPI',image_message[0])

                    print(reply.decode('utf-8'))
                    reply = reply.decode('utf-8')

                    if reply == 'End':
                        break 

                    else:
                        detections = reply.split(MESSAGE_SEPARATOR)
                        obstacle_coordinate_list = obstacle_coordinates.split(MESSAGE_SEPARATOR)

                        for detection, coordinates in zip(detections, obstacle_coordinate_list):

                            if coordinates == '-1,-1':
                                continue
                            elif detection == '-1':
                                continue
                            else:
                                id_string_to_android = '{"image":[' + coordinates + \
                                ',' + detection + ']}'

                                print(id_string_to_android)

                                if detection not in image_id_list:
                                    self.image_count.value += 1
                                    image_id_list.put_nowait(detection)

                                self.msg_to_android_queue.put_nowait(id_string_to_android +NEWLINE) #removed newline

                        print('Time taken to process image: ' + str(datetime.now()-start_time)+ 'seconds')
            except Exception as e:
                print('Image processing failed: %s' %str(e))





    def _formatted_ (self, target, payload):
        return{'target':target, 'payload':payload}

                


