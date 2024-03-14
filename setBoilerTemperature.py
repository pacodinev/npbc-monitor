#!/usr/bin/python

import serial
import time
import multiprocessing
import settings
import sqlite3
import npbc_communication
import binascii


class SerialProcessSet(multiprocessing.Process):
    def __init__(self, boilerTemperature):
        multiprocessing.Process.__init__(self)
        self.__boilerTemperature=boilerTemperature

    def __runCommand(self):
        sp = None
        try:
            sp = serial.Serial(settings.SERIAL_PORT, settings.SERIAL_BAUDRATE, timeout=1, exclusive=True)
            print ("communicating on port: " + sp.name)
            if (sp.is_open):
                sp.reset_output_buffer()
                time.sleep(0.1)
                sp.reset_input_buffer()

                print ("exec: setBoilerTemperatureCommand()")
                requestData = npbc_communication.setBoilerTemperatureCommand(self.__boilerTemperature).getRequestData()
                sp.write(requestData)

                time.sleep(0.5)
                responseData = bytearray()
                if (sp.in_waiting > 0):
                    responseData = bytearray(sp.read(sp.in_waiting))

                # print(requestData)
                # print(responseData)

                if (len(responseData) > 0):
                    response = npbc_communication.setBoilerTemperatureCommand(self.__boilerTemperature).processResponseData(responseData)

                    if (isinstance(response, npbc_communication.successResponse)):
                        print( "   -> success")
                        return True
                    else:
                        print( "   -> failed")
                else:
                    print( "   -> failed in response data")

        except Exception as e1:
            print ("error communicating...: " + str(e1))
        finally:
            if sp is not None:
                sp.close()
        return False

    def run(self):
        for x in range(3):
            success = self.__runCommand();
            if success == True:
                break
            time.sleep(2)
