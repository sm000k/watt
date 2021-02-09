# -*- coding: utf-8 -*-
import numpy as np

# from datetime import *

import time
# from DFRobot_INA219 import INA219
# import i2c_stm as i2c_expander
import threading  # alternate solution is multiprocessing lib.
from typing import Any
from decimal import *
from datetime import datetime

import importlib

# INA219       = importlib.import_module('watt_measurements.DFRobot_INA219')
# i2c_expander = importlib.import_module('watt_measurements.i2c_stm')
import i2c_stm as i2c_expander
from DFRobot_INA219 import INA219
from VADC_MCP import VADC

class WattMeter(object):
    results_avg = [0, 0, 0, 0]
    results_min = [0, 0, 0, 0]
    results_max = [0, 0, 0, 0]
    measure_is_done = 0

    def __init__(self, watt_meterx):
        # self.measure_period = measure_period

        self.watt_meterx = watt_meterx
        if watt_meterx == 'watt_meter_1':
            self.ina = INA219(1, INA219.INA219_I2C_ADDRESS1)
        if watt_meterx == 'watt_meter_2':
            self.ina = INA219(1, INA219.INA219_I2C_ADDRESS2)
        if watt_meterx == 'watt_meter_3':
            self.ina = INA219(1, INA219.INA219_I2C_ADDRESS3)
        if watt_meterx == 'watt_meter_4':
            self.ina = INA219(1, INA219.INA219_I2C_ADDRESS4)
        if watt_meterx == 'watt_meter_5':
            self.ina = INA219(1, INA219.INA219_I2C_ADDRESS5)
        if watt_meterx == 'watt_meter_6':
            self.ina = INA219(1, INA219.INA219_I2C_ADDRESS6)
        # dodać obsluge kolejnego pomiaru
        no_i2c_connection_count = 0
        while not self.ina.begin():
            time.sleep(0.2)
            no_i2c_connection_count += 1
            if no_i2c_connection_count == 2:
                return

        ina219_reading_mA = 1000
        ext_meter_reading_mA = 1000

        self.ina.linear_cal(ina219_reading_mA, ext_meter_reading_mA)

        self.ina.set_bus_RNG(self.ina.bus_vol_range_16V)
        self.ina.set_PGA(self.ina.PGA_bits_2)
        self.ina.set_bus_ADC(self.ina.adc_bits_12, self.ina.adc_sample_1)  # był adc_samble_8
        self.ina.set_shunt_ADC(self.ina.adc_bits_12, self.ina.adc_sample_1)  # było adc_sample_8
        self.ina.set_mode(self.ina.shunt_and_bus_vol_con)

        suffix = self.watt_meterx
        self.file_name = 'cpu_temp' + suffix + '.csv'
        open(self.file_name, 'w+').write("{0} raw_signal_array\n".format(self.watt_meterx))

    def measure_val(self, measure_period, vadc_channel, vadc_address,   debug="debug_on"):
        vadc_chx = vadc_channel
        if vadc_chx == "vadc_ch0":
            vadc_chx = 0
        if vadc_chx == "vadc_ch1":
            vadc_chx = 1
        if vadc_chx == "vadc_ch2":
            vadc_chx = 2
        if vadc_chx == "vadc_ch3":
            vadc_chx = 3
        self.vadc_address = vadc_address
        self.measure_period = measure_period
        open(self.file_name, 'a').write("Timestamp: {0}\n".format(datetime.now()))
        open(self.file_name, 'a').write("sample\telapsed_time\tcurrent\tvoltage\tpower\n")
        open(self.file_name, 'a').write("[-]\t[s]\t[mA]\t[V]\t[mW]\n")
        # open(self.file_name, 'w+').close()

        t_start = time.perf_counter()
        duration_time = 0

        self.prev_signal_val = 0
        raw_signal = [0, 0, 0, 0]
        current_signal_val = []
        self.prev_signal_val = np.array([0, 0, 0, 0])
        float_formatter = lambda x: "%.2f" % x
        np.set_printoptions(formatter={'float_kind': float_formatter})
        self.sample_number = 0
        min_signal_val = np.array([np.nan, np.nan, np.nan, np.nan])
        max_signal_val = np.array([np.nan, np.nan, np.nan, np.nan])
        while duration_time < self.measure_period:
            self.sample_number += 1
            duration_time = time.perf_counter() - t_start

            raw_signal_array = np.array([self.ina.get_current_mA(), self.ina.get_bus_voltage_V(), \
                                         self.ina.get_power_mW(), self.vadc_address.results[vadc_chx]], )
            if self.sample_number == 1:
                for elmnts in range(0, 4):
                    min_signal_val[elmnts] = raw_signal_array[elmnts]
                    max_signal_val[elmnts] = raw_signal_array[elmnts]
                    self.prev_signal_val[elmnts] = raw_signal_array[elmnts]

            for elmnts in range(0, 4):
                # print(raw_signal_array[elmnts])
                if raw_signal_array[elmnts] < min_signal_val[elmnts]: min_signal_val[elmnts] = raw_signal_array[elmnts]
                if raw_signal_array[elmnts] > max_signal_val[elmnts]: max_signal_val[elmnts] = raw_signal_array[elmnts]

            # for elements in raw_signal_array:
            #     for i_temp in raw_signal_array:
            #         if raw_signal_array[i_temp] < min_signal_val[i_temp] : min_signal_val[i_temp] = raw_signal_val [i_temp]
            #         elif raw_signal_array[i_temp] > max_signal_val[i_temp] : max_signal_val[i_temp] = raw_signal_val [i_temp]

            self.prev_signal_val = averaging_signal(self.prev_signal_val, raw_signal_array)

            with open(self.file_name, 'a') as log:
                log.write("{0}\t{1}\t{2}\n".format(self.sample_number, np.around(duration_time, 4), raw_signal_array))

            time.sleep(0.01)

            if debug == "debug_on":
                print(
                    "s {0} av_signal= {1}".format(self.sample_number, self.prev_signal_val))
                # print(
                # "s {0} av_signal= {1}, raw_signal= {2}".format(self.sample_number, prev_signal_val, raw_signal_array))

        with open(self.file_name, 'a') as log:
            log.write("results:\nmeasurement_time:{0}\navg:{1}\nmin:{2}\nmax:{3}\n" \
                      .format(np.around(duration_time, 3), \
                              self.prev_signal_val, \
                              min_signal_val, \
                              max_signal_val))

        self.results_avg = self.prev_signal_val
        self.results_min = min_signal_val
        self.results_max = max_signal_val
        self.measure_is_done = 1

def averaging_signal(prev_signal_val, current_signal_val):
    a = 0.1
    avg_signal = (prev_signal_val + current_signal_val) / 2
    prev_signal_val = avg_signal
    # robust enviroment will may need some different averaging
    # temp_meas_val = a*u +(1-a)*t_previous
    return prev_signal_val

if __name__ == "__main__":
    mcp_v_relays = VADC(0x6a)
    mcp_v_aux = VADC(0x6e)
    mcp_v_relays.results = [0, 0, 0, 0]
    mcp_v_aux.results = [0, 0, 0, 0]

    print("direct execution")
    measure_period = 10
    watt_meter_6 = WattMeter('watt_meter_6')
    watt_meter_6.measure_val(measure_period,"vadc_ch0",mcp_v_relays)
