#!/usr/bin/python
# -*- coding: utf-8 -*-
import multiprocessing
import os
import argparse

from multithreading import Multithreading
from config import IMAGE_PROCESS_SERVER_URLS

parser = argparse.ArgumentParser(description='Main Program for MDP')
parser.add_argument(
    '-i', 
    '--image_recognition', 
    choices=IMAGE_PROCESS_SERVER_URLS.keys(),
    default=None,
)

def init():
    args = parser.parse_args()
    image_processing_server = args.image_recognition


    os.system('sudo hciconfig hci0 piscan')

    try:
        multiprocess_comm = Multithreading(
            IMAGE_PROCESS_SERVER_URLS.get(image_processing_server)
        )
        multiprocess_comm.start()
    except Exception:
        multiprocess_comm.disconnect()
    
if __name__ == '__main__':
    init()
