import glob

# import smbus
import smbus2 as smbus
try:
    from watt_measurements.MCP342x import MCP342x
except:
    from MCP342x import MCP342x

# import numpy as np
import time

from os import system, name
import statistics


# import inspect
# print(inspect.getfile(MCP342x))

# from hotplug.machine_interface import *
# from com_ports import serial_ports
# import keyboard


# def get_stjets_com_ports():
#     # com_ports= ["/dev/ttyACM1"]
#     com_ports = serial_ports()
#     return com_ports


__author__ = 'Steve Marple'
__version__ = '0.3.4'
__license__ = 'MIT'


#### test komunikacji
def get_smbus():
    candidates = []
    prefix = '/dev/i2c-'
    for bus in glob.glob(prefix + '*'):
        try:
            n = int(bus.replace(prefix, ''))
            candidates.append(n)
        except:
            pass
    if len(candidates) == 1:
        # return smbus.SMBus(candidates[0])
        return smbus.SMBus(1)
    elif len(candidates) == 0:
        raise Exception("Could not find an I2C bus")
    else:
        raise Exception("Multiple I2C busses found")
# class VADC_new (object):
#     results = 0
#     def __init__ (self,VADC_i2c_address):
#
#         self.bus = get_smbus()
#         MCP342x.general_call_reset(self.bus)
#         self.VADC_i2c_address = VADC_i2c_address
#         self.VADC_CHn = [0]
#         self.VADC_CHn[0]=MCP342x(self.bus, self.VADC_i2c_address, channel=0, resolution=12,continuous_mode=True)
#
#     def _speed_test(self, debug):
#
#         t_start = time.perf_counter()
#         sample = 0
#         while True:
#             reading = MCP342x.convert_and_read(self.VADC_CHn, samples=None, raw=False)
#             if debug == 1:
#                 sample += 1
#                 duration_time = time.perf_counter() - t_start
#                 print(sample / duration_time)
#                 print('sample', sample)
#                 print(reading)
#
#     def measure_continous_beta(self, measure_period, stop_event=None, debug=0):
#         # divider = 1  # (9.7+1)/1 # divder adjusted to  vad_aux value = 11 was set previously
#         results = 0
#
#         while not stop_event.is_set():
#             # readings = MCP342x.convert_and_read_many(self.VADC_CHn, samples=1, raw=True)
#             readings = MCP342x.convert_and_read(self.VADC_CHn[0], samples=1, raw=True)
#             results = readings
#             self.results = results
#     def measure_continous(self, measure_period, stop_event, debug=0):
#         divider = 1  # (9.7+1)/1 # divder adjusted to  vad_aux value = 11 was set previously
#         results = 0
#         self.measure_period = measure_period
#         t_start = time.perf_counter()
#         duration_time = 0
#         if self.measure_period == 0:
#             while not stop_event.is_set():
#                 readings = MCP342x.convert_and_read_many(self.VADC_CHn[], samples=1)
#                 # self.results[0],config = readings[0]
#                 self.results[0] = 0
#                 if debug == 1:
#                     time.sleep(0.01)
#                     for n in readings:
#                         print("{0:.3f} ".format(n[0]), end='')
#                     print("")
#             else:
#                 while duration_time < self.measure_period:
#                     duration_time = time.perf_counter() - t_start
#                     readings = MCP342x.convert_and_read_many(self.VADC_CHn, samples=1)
#                     time.sleep(0.2)
#                     for n in range(0, 4):
#                         self.results[n] = divider * readings[n][0]
#                     if debug == 1:
#                         time.sleep(0.01)
#                         for n in readings:
#                             print("{0:.3f} ".format(n[0]), end='')
#                         print("")

class VADC(object):
    results = []
    for i in range(4):
        results.append(int(0))
    def __init__(self, VADC_i2c_address):
        self.VADC_CHn = [0, 0, 0, 0]
        self.bus = get_smbus()
        MCP342x.general_call_reset(self.bus)
        self.VADC_i2c_address = VADC_i2c_address
        for n in range(len(self.VADC_CHn)):
            self.VADC_CHn[n] = MCP342x(self.bus, self.VADC_i2c_address, channel=n, resolution=12,continuous_mode=True)
        self.sleep = 0.0001
        # detection fault connection (no response =no valid connection)
        MCP342x.raw_read(self.VADC_CHn[0])[0]

    def measure(self, debug=0):
        divider = 11
        results = [0, 0, 0, 0]
        readings = MCP342x.convert_and_read_many(self.VADC_CHn, samples=1)

        time.sleep(0.01)
        # print("r",readings)
        for n in range(0, 4):
            results[n] = readings[n]
            # print(n,results[n],end='')
            # print("")
        print("r", results)
        if debug == 1:
            time.sleep(0.01)
            for n in readings:
                print("{0:.3f} ".format(11 * n[0]), end='')
            print("")
        return results
    def measure_continous(self, measure_period, stop_event, debug=0):
        # obj = self.VADC_CHn

        # obj[0] = self.VADC_CHn[0]
        # obj[1] = self.VADC_CHn[1]
        # obj[2] = self.VADC_CHn[2]
        # obj[3] = self.VADC_CHn[3]
        while not stop_event.is_set():
            self.results[0] = MCP342x.raw_read(self.VADC_CHn[0])[0]
            self.results[1] = MCP342x.raw_read(self.VADC_CHn[1])[0]
            self.results[2] = MCP342x.raw_read(self.VADC_CHn[2])[0]
            self.results[3] = MCP342x.raw_read(self.VADC_CHn[3])[0]

    def measure_continous_single_channel(self, measure_period, stop_event,n, debug=0):

        while not stop_event.is_set():
            self.results[n] = MCP342x.raw_read(self.VADC_CHn[n])[0]


    def measure_continous_diagnostic(self, debug = 1 , performance_test = 0, no_sample= 500):
            if debug == 1 :
                while True:
                    self.results[0], config = MCP342x.raw_read(self.VADC_CHn[0])
                    self.results[1], config = MCP342x.raw_read(self.VADC_CHn[1])
                    self.results[2], config = MCP342x.raw_read(self.VADC_CHn[2])
                    self.results[3], config = MCP342x.raw_read(self.VADC_CHn[3])
                    print(self.results)
            else:
                if performance_test == 0:
                    while True:
                        self.results[0], config = MCP342x.raw_read(self.VADC_CHn[0])
                        self.results[1], config = MCP342x.raw_read(self.VADC_CHn[1])
                        self.results[2], config = MCP342x.raw_read(self.VADC_CHn[2])
                        self.results[3], config = MCP342x.raw_read(self.VADC_CHn[3])
                else:
                    t_start = time.perf_counter()
                    sample = no_sample
                    _results   = [0,0,0,0]
                    temp_vadc_chn = self.VADC_CHn[3]
                    while sample > 0:
                        sample -= 1
                        #duration_time = time.perf_counter() - t_start
                        # t1 = time.perf_counter()
                        # print(MCP342x.get_conversion_time(temp_vadc_chn))
                        temp = MCP342x.raw_read_4(temp_vadc_chn)
                        # print(sample)
                        # print(temp3)
                        # t2 = time.perf_counter()
                        # print("t2-t1 raw _read",t2-t1,"temp3=",temp3)
                        # # time.sleep(0.00001)
                        # print(temp,temp2)
                        # zmienna_1 = MCP342x.raw_read(self.VADC_CHn[1])[0]
                        # #time.sleep(0.00001)
                        # zmienna_2 = MCP342x.raw_read(self.VADC_CHn[2])[0]
                        # #time.sleep(0.00001)
                        # zmienna_3 = MCP342x.raw_read(self.VADC_CHn[3])[0]
                        # #time.sleep(0.00001)
                    duration_time = time.perf_counter() - t_start
                    print(sample)
                    print(duration_time)
                    print("sample/duration_time", no_sample/duration_time)



    def _measure_continous_beta(self, measure_period, stop_event=None, debug=0):
        #divider = 1  # (9.7+1)/1 # divder adjusted to  vad_aux value = 11 was set previously
        results = [0, 0, 0, 0]
        #self.measure_period = measure_period
        #t_start = time.perf_counter()
        while not stop_event.is_set():

            readings = MCP342x.convert_and_read_many(self.VADC_CH, samples=1,raw=True)
            results[0] = readings[0][0]
            # results[1] = readings[1][0]
            # results[2] = readings[2][0]
            # results[3] = readings[3][0]
            self.results = results

            #results [0] = (readings[0][0]+ readings[0][1])/2
            #time.sleep(0.05)
                # print("r",readings)
            # for n in range(0, 4):
            #     self.results[n] = divider * readings[n][0]
            # results= readings
            # if debug == 1:
            #     duration_time = time.perf_counter() - t_start
            #     for n in readings:
            #
            #         print(np.around(duration_time, 2), results,end = ' ')
            #         print("{0:.3f} ".format(n[0]), end=' ')
            #     print("")
            #print(results[0],end ='')
    def _speed_test (self,debug):
        #divider = 1  # (9.7+1)/1 # divder adjusted to  vad_aux value = 11 was set previously
        #results = [0, 0, 0, 0]
        #self.measure_period = measure_period
        t_start = time.perf_counter()
        sample = 0
        conv_time = 1.0/240
        while True:
            # readings = MCP342x.convert_and_read_many(self.VADC_CHn,samples = None, raw = True)
            # readings = MCP342x._moj_convert_and_read_many(self.VADC_CHn, samples=None, raw=False)
            reading = MCP342x.convert_and_read(self.VADC_CHn, samples=None, raw=False)

            # # readings = MCP342x.raw_read(self.VADC_CH)
            # readings = vadc.raw_read()

            #time.sleep(    ((10000-sample)/10000) * conv_time)
            # results = readings
            # readings = MCP342x.raw_read(self)
            # time.sleep(0.05)
            # print("r",readings)
            sample +=1
            # for n in range(0, 4):
            #
            #     self.results[n] = divider * readings[n][0]
            if debug == 1:
                duration_time = time.perf_counter() - t_start
                print(sample/duration_time)
                print('sample',sample)
                print(readings)
                #print(results[0])
                # for n in readings:
                #     print("{0:.3f} ".format(n[0]), end=' ')
                # print("")

def diagnostic_test ():
    address = [0x68, 0x69, 0x6a, 0x6c, 0x6e]
    vadc = VADC(0x6a)  # relays
    vadc = VADC(0x6e) #aux
    #vadc.measure_continous_diagnostic()
    vadc.measure_continous_diagnostic(debug = 0 ,performance_test = 1, no_sample = 1000)

if __name__ == '__main__':  # szukanie aktywnego adresu

    for i in range (0,3):
        print("test=", i + 1)
        diagnostic_test()


    # vadc = VADC_new (0x6e)
    # vadc.speed_test(debug=1)