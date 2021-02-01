import board
import busio

i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
# i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
# import numpy as np
from datetime import *

import time
#
# ads0 = ADS.ADS1015(i2c, mode=0x0000, data_rate=3300, address=0x48)
# ads1 = ADS.ADS1015(i2c, mode=0x0000, data_rate=3300, address=0x49)
# ads2 = ADS.ADS1015(i2c, mode=0x0000, data_rate=3300, address=0x4a)
# ads3 = ADS.ADS1015(i2c, mode=0x0000, data_rate=3300, address=0x4b)
#



class VADC_ADS():
    results = [0]*4
    def __init__(self, VADC_i2_address):
        self.VADC_CHn = [0, 0, 0, 0]
        # self.bus = get_smbus()
        self.VADC_i2c_address = VADC_i2_address
        self.sleep = 0.0000000
        try:
            self.ads = ADS.ADS1015(i2c, mode=0x0000, data_rate=3300, address=self.VADC_i2c_address)
        except:
            print("VADC ADS not detected", self.VADC_i2c_address)

    def measure_continous(self,measure_period, stop_event, debug=0):
        print("start pomiaru TEST VADC RELAYS")
        if stop_event != None:
            while not stop_event.is_set():
                self.results[0] = AnalogIn(self.ads, ADS.P0).voltage
                self.results[1] = AnalogIn(self.ads, ADS.P1).voltage
                self.results[2] = AnalogIn(self.ads, ADS.P2).voltage
                self.results[3] = AnalogIn(self.ads, ADS.P3).voltage
                time.sleep(self.sleep)
        else:
            while True:
                self.results[0] = AnalogIn(self.ads, ADS.P0).voltage
                self.results[1] = AnalogIn(self.ads, ADS.P1).voltage
                self.results[2] = AnalogIn(self.ads, ADS.P2).voltage
                self.results[3] = AnalogIn(self.ads, ADS.P3).voltage
                time.sleep(self.sleep)


def single():
    sample_sum = 3000
    sample_now = 0
    chan = []
    timer = []
    measurement = []
    sample_now = 0
    time_passed = 0
    print("start")
    t_start = time.perf_counter()
    while time_passed < 0.1:
        chan.append(AnalogIn(ads, ADS.P3).value)
        time_passed = time.perf_counter() - t_start
        timer.append(time_passed)
        sample_now += 1

        # time.sleep(0.001)

    t_end = time.perf_counter()
    print("stop")
    time_overall = t_end - t_start
    SPS = sample_now / time_overall

    print("sample_sum=", sample_now, "time_overall=", time_overall, "SPS=", SPS)
    f = open("results.csv", "w+")
    i = 0
    for i in range(len(chan)):
        chan[i] = chan[i] * 4.096 / 32767
        string_temp = str(i) + "\t" + "{:.6f}".format(timer[i]) + "\t" + "{:.6f}".format(chan[i]) + "\n"
        string_conv = string_temp.replace(".", ",")

        f.write(string_conv)


def online():
    chan = []
    t_start = time.perf_counter()
    time_passed = 0
    time_pos = 0
    time_neg = 0
    t_del = t_start
    while time_passed < 10:
        chan.append(AnalogIn(ads, ADS.P3))
        time_passed = time.perf_counter() - t_start
        sec_passed = time.perf_counter() - t_del
        t1 = time_passed
        if chan[-1].voltage > 1:
            time_pos += 1
        else:
            time_neg += 1
        if sec_passed > 1:
            print(time_pos / (time_neg + time_pos))
            time_pos = 0
            time_neg = 0
            t_del = time.perf_counter()


def single_sample():
    sample_sum = 3000
    sample_now = sample_sum
    t_start = time.perf_counter()
    chan1 = []
    chan2 = []
    chan0 = []
    chan3 = []
    timer = []
    measurement = []
    sample_now = 0
    time_passed = 0
    # while sample_now <1000:
    time_passed = 0
    while sample_now < 3000:
        # chan0.append(ads.read(ADS.P0))
        # chan1.append(ads.read(ADS.P1))
        # chan2.append(AnalogIn(ads, ADS.P2).voltage)
        # chan3.append(AnalogIn(ads, ADS.P3).voltage)
        # print(chan0[-1],"\t",chan1[-1],"\t",chan2[-1],"\t",chan3[-1])
        # chan2.append(ads2.read(ADS.P2))
        # chan2.append(ads.read(ADS.P2))
        # time.sleep(0.001)
        # chan2.append(0)
        # chan3.append(ads.read(ADS.P3))
        # chan2.append(ads3.read(ADS.P3))

        # chan3.append(0)
        # *4.096/32767

        chan0.append(AnalogIn(ads0, ADS.P3).voltage)
        chan1.append(AnalogIn(ads1, ADS.P3).voltage)
        chan2.append(AnalogIn(ads2, ADS.P3).voltage)
        chan3.append(AnalogIn(ads3, ADS.P3).voltage)
        # print(chan3[-1])
        # time.sleep(0.5)
        # chan3.append(ads.read(ADS.P3))
        # print(chan3[-1])
        # print(chan2[-1])
        time_passed = time.perf_counter() - t_start
        timer.append(time_passed)
        sample_now += 1

    t_end = time.perf_counter()
    time_overall = t_end - t_start
    SPS = sample_now / time_overall

    print("sample_sum=", sample_now, "time_overall=", time_overall, "SPS=", SPS)
    f = open("results.csv", "w+")
    i = 0
    for i in range(len(chan3)):
        string_temp = str(i) + "\t" + "{:.6f}".format(timer[i]) + "\t" + "{:.6f}".format(
            chan3[i]) + "\t" + "{:.6f}".format(chan2[i]) + "\n"
        string_conv = string_temp.replace(".", ",")
        f.write(string_conv)
    print(chan0[-1])
    print(chan1[-1])
    print(chan2[-1])
    print(chan3[-1])


def testy_ads():
    while True:
        print(ads.read(ADS.P3, is_differential=True))
        # print(ads.get_last_result(fast=True))
if __name__ == '__main__': #
    vadc_temp = VADC_ADS(0x48)
    vadc_temp.measure_continous()
# single()
# single()
# single_sample()
# single_sample()
# online()
# testy_ads()
