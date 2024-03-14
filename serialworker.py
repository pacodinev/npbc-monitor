#!/usr/bin/python

import serial
import time
import multiprocessing
import settings
import sqlite3
import npbc_communication
import binascii
import random

class SerialProcess(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def __writeToDB(self, dbconn, response):
        params = [response.SwVer, response.Date, response.Mode, response.State, response.Status, response.IgnitionFail, 
                  response.PelletJam, response.Tset, response.Tboiler, response.Flame, response.Heater, response.CHPump,
                  response.DHW, response.BF, response.FF, response.Fan, response.Power, response.ThermostatStop, 
                  response.FFWorkTime, response.DhwPump]

        dbconn.execute("INSERT INTO [BurnerLogs] ([Timestamp], [SwVer], [Date], [Mode], [State], [Status], [IgnitionFail], [PelletJam], [Tset], [Tboiler], [Flame], \
                               [Heater],[CHPump],[DHW],  [BF], [FF], [Fan], [Power], [ThermostatStop], [FFWorkTime], [DhwPump]) \
                               VALUES (datetime(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
        dbconn.commit()

    def run(self):
        print ("communicating on port: " + settings.SERIAL_PORT)

        dbconn = sqlite3.connect(settings.DATABASE)
        requestData = npbc_communication.generalInformationCommand().getRequestData()
        resetFFWorkTimeCounterCommandRequestData = npbc_communication.resetFFWorkTimeCounterCommand().getRequestData()

        # while (sp.isOpen()):
        while (True):
            time.sleep(15)

            print ("exec: generalInformationCommand()")

            sp = None
            try:
                sp = serial.Serial(settings.SERIAL_PORT, settings.SERIAL_BAUDRATE, timeout=1, exclusive=True)
                if(sp.is_open):
                    sp.reset_output_buffer()
                    time.sleep(0.1)
                    sp.reset_input_buffer()

                    sp.write(requestData)
                    time.sleep(0.5)

                    responseData = bytearray()
                    if (sp.in_waiting > 0):
                        responseData = bytearray(sp.read(sp.in_waiting))

                    if (len(responseData) > 0):
                        response = npbc_communication.generalInformationCommand().processResponseData(responseData)

                        if (isinstance(response, npbc_communication.failResponse)):
                            print( "   -> failed")

                        if (isinstance(response, npbc_communication.generalInformationResponse)):
                            print( "   -> success")

                            if (response.FFWorkTime > 0):
                                print ("exec: resetFFWorkTimeCounterCommand()")

                                sp.reset_output_buffer()
                                time.sleep(0.1)
                                sp.reset_input_buffer()

                                sp.write(resetFFWorkTimeCounterCommandRequestData)

                                time.sleep(0.5)
                                resetFFWorkTimeCounterCommandResponseData = bytearray()
                                if (sp.in_waiting > 0):
                                    resetFFWorkTimeCounterCommandResponseData = bytearray(sp.read(sp.in_waiting))

                                if (len(resetFFWorkTimeCounterCommandResponseData) > 0):
                                    resetFFWorkTimeCounterCommandResponse = npbc_communication.resetFFWorkTimeCounterCommand().processResponseData(resetFFWorkTimeCounterCommandResponseData)

                                    if (isinstance(resetFFWorkTimeCounterCommandResponse, npbc_communication.failResponse)):
                                        print ("   -> failed")

                                    if (isinstance(resetFFWorkTimeCounterCommandResponse, npbc_communication.successResponse)):
                                        print ("   -> success")

                                        self.__writeToDB(dbconn, response);
                            else:
                                self.__writeToDB(dbconn, response);

            except Exception as e1:
                print ("error communicating...: " + str(e1))
            finally:
                if sp is not None:
                    sp.close()
