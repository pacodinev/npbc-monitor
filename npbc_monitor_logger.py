#!/usr/bin/python

import os
import time
import multiprocessing
from multiprocessing.managers import BaseManager
import serialworker
import json
import sqlite3
import settings
import npbc_communication

if __name__ == '__main__':
    ## start the serial worker in background (as a deamon)
    sp = serialworker.SerialProcess()
    #sp.daemon = True
    sp.start()
