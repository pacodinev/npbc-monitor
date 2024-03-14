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

    def run(self):
        sp = serial.Serial(settings.SERIAL_PORT, settings.SERIAL_BAUDRATE, timeout=1)
        print ("communicating on port: " + sp.portstr)

        dbconn = sqlite3.connect(settings.DATABASE)


        while (sp.isOpen()):

            #resetFFWorkTimeCounterCommandResponseData = bytearray(self.testresetFFWorkTimeCounterCommandResponse)

            try:
                print ("exec: generalInformationCommand()")

                time.sleep(0.1)
                sp.flushInput()
                sp.flushOutput()

                time.sleep(0.1)
                requestData = npbc_communication.generalInformationCommand().getRequestData()
                sp.write(requestData)

                time.sleep(0.5)
                responseData = bytearray()
                if (sp.in_waiting() > 0):
                    responseData = bytearray(sp.read(sp.in_waiting()))

                if (len(responseData) > 0):
                    response = npbc_communication.generalInformationCommand().processResponseData(responseData)

                    if (isinstance(response, npbc_communication.failResponse)):
                        print( "   -> failed")

                    if (isinstance(response, npbc_communication.generalInformationResponse)):
                        print( "   -> success")

                        if (response.FFWorkTime > 0):
                            print ("exec: resetFFWorkTimeCounterCommand()")

                            time.sleep(0.1)
                            sp.flushInput()
                            sp.flushOutput()

                            time.sleep(0.1)
                            resetFFWorkTimeCounterCommandRequestData = npbc_communication.resetFFWorkTimeCounterCommand().getRequestData()
                            sp.write(resetFFWorkTimeCounterCommandRequestData)

                            time.sleep(0.5)
                            resetFFWorkTimeCounterCommandResponseData = bytearray()
                            if (sp.in_waiting > 0):
                                resetFFWorkTimeCounterCommandResponseData = bytearray(sp.read(sp.in_waiting()))

                            if (len(resetFFWorkTimeCounterCommandResponseData) > 0):
                                resetFFWorkTimeCounterCommandResponse = npbc_communication.resetFFWorkTimeCounterCommand().processResponseData(resetFFWorkTimeCounterCommandResponseData)

                                if (isinstance(resetFFWorkTimeCounterCommandResponse, npbc_communication.failResponse)):
                                    print ("   -> failed")

                                if (isinstance(resetFFWorkTimeCounterCommandResponse, npbc_communication.successResponse)):
                                    print ("   -> success")

                                    params = [response.SwVer, response.Date, response.Mode, response.State, response.Status, response.IgnitionFail, response.PelletJam, response.Tset, response.Tboiler, response.Flame,
                                              response.Heater, response.CHPump,response.DHW, response.BF, response.FF, response.Fan, response.Power, response.ThermostatStop, response.FFWorkTime, response.DhwPump]

                                    dbconn.execute("INSERT INTO [BurnerLogs] ([Timestamp], [SwVer], [Date], [Mode], [State], [Status], [IgnitionFail], [PelletJam], [Tset], [Tboiler], [Flame], \
                                                           [Heater],[CHPump],[DHW],  [BF], [FF], [Fan], [Power], [ThermostatStop], [FFWorkTime], [DhwPump]) VALUES (datetime(), ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
                                    dbconn.commit()

                        else:
                            params = [response.SwVer, response.Date, response.Mode, response.State, response.Status, response.IgnitionFail, response.PelletJam, response.Tset, response.Tboiler, response.Flame,
                                      response.Heater, response.CHPump, response.DHW, response.BF, response.FF, response.Fan, response.Power, response.ThermostatStop, response.FFWorkTime, response.DhwPump]

                            dbconn.execute("INSERT INTO [BurnerLogs] ([Timestamp], [SwVer], [Date], [Mode], [State], [Status], [IgnitionFail], [PelletJam], [Tset], [Tboiler], [Flame], \
                                                   [Heater], [CHPump], [DHW], [BF], [FF], [Fan], [Power], [ThermostatStop], [FFWorkTime], [DhwPump]) VALUES (datetime(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
                            dbconn.commit()

            except Exception as e1:
                print ("error communicating...: " + str(e1))

            time.sleep(15)
