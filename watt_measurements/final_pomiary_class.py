# -*- coding: utf-8 -*-

import numpy as np
from math import nan
import time
import select
import threading
from decimal import *
from datetime import datetime
import importlib

import sys
import os

# claused import in case of call from outside or inside
try:
    import watt_measurements.i2c_stm as i2c_expander
except:
    import i2c_stm as i2c_expander
try:
    from watt_measurements.DFRobot_INA219 import INA219
except:
    from DFRobot_INA219 import INA219
try:
    from watt_measurements.VADC_MCP import VADC
except:
    from VADC_MCP import VADC

from watt_measurements.VADC_ADS import VADC_ADS

# INA219       = importlib.import_module('watt_measurements.DFRobot_INA219')
# i2c_expander = importlib.import_module('watt_measurements.i2c_stm')


"""
klasa Watt_Meter wymagac będzie inicjalizacji posiada konstruktor i inicjalizacje 
input: ???
output: srednia wartosc mierzona za okres T parametrow napiecia pradu i mocy (3)
"""

"""
0x40: "wattmeter_1",
0x41: "wattmeter_2",
0x44: "wattmeter_3",
0x45: "wattmeter_4",
0x46: "wattmeter_5",
0x49: "wattmeter_6"
"""

input_matrix_measurement_group_dict = {
    'msrmnt_set_1': (
        "watt_meter_1", INA219(1, INA219.INA219_I2C_ADDRESS1), "vadc_relays", "vadc_ch_0", 'additional_task', 1523),
    'msrmnt_set_2': (
        "watt_meter_2", INA219(1, INA219.INA219_I2C_ADDRESS2), "vadc_relays", "vadc_ch_1", 'additional_task', 1524),
    'msrmnt_set_3': (
        "watt_meter_3", INA219(1, INA219.INA219_I2C_ADDRESS3), "vadc_relays", "vadc_ch_2", 'additional_task', 1525),
    'msrmnt_set_4': (
        "watt_meter_4", INA219(1, INA219.INA219_I2C_ADDRESS4), "vadc_relays", "vadc_ch_3", 'additional_task', 1526),
    'msrmnt_set_5':
        ("watt_meter_5", INA219(1, INA219.INA219_I2C_ADDRESS5), None, None, None, None),
    'msrmnt_set_6':
        ("watt_meter_6", INA219(1, INA219.INA219_I2C_ADDRESS6), "vadc_aux", "vadc_ch_0", 'watt_meter_aux_test', None)
}

watt_measurement_dict = {}

virtual_limit_switch_output_signal = i2c_expander.GPIO([0], DEVICE_ADDRESS=0x20, PORT="B", GPIOtype="OUTPUT",
                                                       debug_mode="debug_mode_off")  # additionaly relay control
real_limit_switch_input_signal = i2c_expander.GPIO([7], DEVICE_ADDRESS=0x20, PORT="B", GPIOtype="INPUT",
                                                   debug_mode="debug_mode_off")  # input ; detecting state of relay

# float precision
getcontext().prec = 1

# vadc_aux.results = [nan, nan, nan, nan]
# vadc_aux.results = nan
## GPIO's for additional relay hub which switches RELAY LOAD's
GPIOx_list = [0, 1, 2, 3, 4, 5, 6, 7]
PIN_A_ALL = i2c_expander.GPIO(GPIOx_list, DEVICE_ADDRESS=0x20, PORT="A", GPIOtype="OUTPUT",
                              debug_mode="debug_on")


def _averaging_signal(prev_signal_val, current_signal_val):
    a = 0.1
    avg_signal = (prev_signal_val + current_signal_val) / 2
    prev_signal_val = avg_signal
    # robust enviroment will may need some different averaging
    # temp_meas_val = a*u +(1-a)*t_previous
    return prev_signal_val


class WattMeasurementClass(object):
    results_avg = [np.nan, np.nan, np.nan, np.nan]
    results_min = [np.nan, np.nan, np.nan, np.nan]
    results_max = [np.nan, np.nan, np.nan, np.nan]
    measure_is_done = 0
    vadc_measured_val = np.nan

    def __init__(self, measurement_id_label, input_measurement_group):
        self.sum_ratio = 0
        self.ratio = 0
        self.measurement_id_label = measurement_id_label
        try:
            self.watt_meter_id = input_measurement_group[0]
            self.ina = input_measurement_group[1]
            self.vadc_device_label = input_measurement_group[2]
            temp_label_vadc_channel = input_measurement_group[3]
            self.corelated_modbus_port = input_measurement_group[5]
        except:
            print("input_matrix_measurement_group initial data problem")
            print(self.measurement_id_label)
            sys.exit(1)
            return
        ## CONFIGURING INA (WATTMETER) SEGMENT (INA219)
        no_i2c_connection_count = 0
        while not self.ina.begin():
            time.sleep(0.2)
            no_i2c_connection_count += 1
            if no_i2c_connection_count == 3:
                sys.exit(1)
                return
        self.ina.set_steamjet_measurement_parameters()

        ## CONFIGURING VADC SEGMENT
        self.vadc_device = None
        if self.vadc_device_label == "vadc_relays":
            self.vadc_device = vadc_relays
        if self.vadc_device_label == "vadc_aux":
            self.vadc_device = vadc_aux
        if self.vadc_device_label == "None":
            self.vadc_device = 0

        self.vadc_channel = 0
        if temp_label_vadc_channel is not None:
            if "vadc_ch_" in temp_label_vadc_channel and len(temp_label_vadc_channel) == len("vadc_ch_x"):
                self.vadc_channel = int(temp_label_vadc_channel[len("vadc_ch_x") - 1])
        ## CREATING LOG FILE
        suffix = self.measurement_id_label
        cur_path = os.path.dirname(__file__)
        self.file_name_display = 'report_' + suffix + '.csv'
        self.file_name_raw = 'raw_report_' + suffix + '.csv'
        self.report_directory_display = cur_path + "/measurement_reports/" + self.file_name_display
        print(self.report_directory_display)
        self.report_directory_raw = cur_path + "/measurement_reports/" + self.file_name_raw
        open(self.report_directory_display, 'w').write("{0} raw_signal_array\n".format(self.measurement_id_label))
        open(self.report_directory_display, 'a').close()

        open(self.report_directory_raw, 'w').write("{0} raw_signal_array\n".format(self.measurement_id_label))
        open(self.report_directory_raw, 'a').close()

    def measure_val(self, measure_period, debug_mode):
        float_formatter = lambda x: "%.3f" % x
        np.set_printoptions(formatter={'float_kind': float_formatter})

        self.time_stamp = datetime.now()
        self.measure_period = measure_period
        self.t_start = time.perf_counter()
        duration_time = 0
        self.sample_number = 0

        self.prev_signal_val = np.array([np.nan, np.nan, np.nan, np.nan])
        self.measured_val = []
        self.last_measured_val = nan
        _wattmeter_name = self.measurement_id_label

        power = 0  # self.ina.get_power_mW() # for performance it's better to calculate power after measurement
        while duration_time < self.measure_period:
            self.sample_number += 1
            duration_time = time.perf_counter() - self.t_start
            if self.vadc_device is not None:
                vadc_measured_val = self.vadc_device.results[self.vadc_channel]
                i_ma = self.ina.get_current_mA()
                v_v = self.ina.get_bus_voltage_V()
            else:
                vadc_measured_val = np.nan
                i_ma = self.ina.get_current_mA()
                v_v = self.ina.get_bus_voltage_V()

            # raw_signal_array = np.array([I, V, P, vadc_measured_val], )
            # log_raw_signal_array = np.array([self.sample_number][raw_signal_array],)
            self.last_measured_val = [self.sample_number, duration_time, i_ma, v_v, power, vadc_measured_val]
            self.measured_val.append(self.last_measured_val)
            # self.prev_signal_val = _averaging_signal(self.prev_signal_val, raw_signal_array)
            # self.prev_signal_val = raw_signal_array
            if debug_mode == 1:
                czas = np.around(duration_time, 4)
                self.ratio = self.sample_number / duration_time
                print(
                    "\nt={0:.4f} s= {1} s/t={2:.0f} {3}={4} ".format(czas, self.sample_number,
                                                                     self.ratio,
                                                                     _wattmeter_name,
                                                                     self.prev_signal_val), end=' ')
        if debug_mode == 2:
            self.ratio = self.sample_number / duration_time
            print(duration_time, self.sample_number, self.ratio, _wattmeter_name)

        self.results_avg = self.prev_signal_val
        self.measure_is_done = 1
        print('MEASUREMENT COMPLETED', self.measurement_id_label)

    def watt_measurement_make_log(self):
        measured_val = self.measured_val
        # self.prev_signal_val = _averaging_signal(self.prev_signal_val, raw_signal_array)
        open(self.report_directory_display, 'a').write(
            "Test start         :{0}\n"
            "Measurement start  :{1}\n".format(self.time_stamp, datetime.now(), ))
        open(self.report_directory_display, 'a').write(
            "sample\telapsed_time\tcurrent\tvoltage\t\tpower\tvoltage_vadc\n")
        open(self.report_directory_display, 'a').write("[-]\t[s]\t\t[mA]\t[V]\t\t[mW]\t\t[V]\n")
        # vadc_aux_calib
        voltage_temp_tab = []
        for l in range(len(measured_val)):
            voltage_temp_tab.append(measured_val[l][3])
        print("max voltage", max(voltage_temp_tab))

        with open(self.report_directory_display, 'a') as log:
            for l in range(len(measured_val)):
                _temp_power = measured_val[l][2] * measured_val[l][5]
                _temp_vadc_val = measured_val[l][5] * (10.96491 + 1.1042) / 1000
                log.write(
                    "{0:05}\t{1:08.5f}\t{2:+05.0f}\t{3:+08.4f}\t{4:+08.02f}\t{5:+06.03f}\n". \
                        format(measured_val[l][0], measured_val[l][1], measured_val[l][2], \
                               measured_val[l][3], _temp_power, _temp_vadc_val))
        open(self.report_directory_display, 'a').close()
        with open(self.report_directory_raw, 'a') as log:
            for l in range(len(measured_val)):
                measured_val[l][4] = 0
                log.write(
                    "{0:5}\t{1:8.5f}\t{2:5.0f}\t{3:8.4f}\t{4:8.02f}\t{5:6}\n". \
                        format(measured_val[l][0], measured_val[l][1], measured_val[l][2], \
                               measured_val[l][3], measured_val[l][4], measured_val[l][5]))
        open(self.report_directory_raw, 'a').close()
        # if self.sample_number == 1:
        #     for elmnts in range(0, 4):
        #         # min_signal_val[elmnts] = raw_signal_array[elmnts]
        #         # max_signal_val[elmnts] = raw_signal_array[elmnts]
        #         # self.prev_signal_val[elmnts] = raw_signal_array[elmnts]
        #         print('first')

        # *************
        # for elmnts in range(0, 4):
        #     # print(raw_signal_array[elmnts])
        #     if raw_signal_array[elmnts] < min_signal_val[elmnts]: min_signal_val[elmnts] = raw_signal_array[elmnts]
        #     if raw_signal_array[elmnts] > max_signal_val[elmnts]: max_signal_val[elmnts] = raw_signal_array[elmnts]
        # ***************
        # for elements in raw_signal_array:
        #     for i_temp in raw_signal_array:
        #         if raw_signal_array[i_temp] < min_signal_val[i_temp] : min_signal_val[i_temp] = raw_signal_val [i_temp]
        #         elif raw_signal_array[i_temp] > max_signal_val[i_temp] : max_signal_val[i_temp] = raw_signal_val [i_temp]

        # with open(self.file_name, 'a') as log:
        #     log.write("results:\nmeasurement_time:{0}\navg:{1}\nmin:{2}\nmax:{3}\n" \
        #               .format(np.around(duration_time, 3), \
        #                       self.prev_signal_val, \
        #                       min_signal_val, \
        #                       max_signal_val))

        # ***************
        # self.results_min = min_signal_val
        # self.results_max = max_signal_val
        # ***************

    def watt_measure_show_info(self):
        label = self
        if label.vadc_device:
            temp_adress = hex(label.vadc_device.VADC_i2c_address)
            temp_ch = label.vadc_channel
            temp_modbus_port = label.corelated_modbus_port
        else:
            temp_adress = None
            temp_ch = None
            temp_modbus_port = None
        print(label.measurement_id_label)
        print('wattmeter_device_name=', label.ina.name, 'wattmeter_address=', hex(label.ina.i2c_addr))
        print('vadc_device_name=', label.vadc_device_label,
              "vadc_address=", temp_adress,
              'vadc_ch=', temp_ch,
              'modbus_port=', temp_modbus_port)


def watt_meter_aux_test(_object_mmi, _WattMeasurementClass_object, aux_test_measure_period, _debug_mode=1):
    if _debug_mode == 1:    print("start aux_test")
    virtual_limit_switch_output_signal.Pins_set_on()
    if real_limit_switch_input_signal.test_bit(bit=7, echo=0):
        if _debug_mode == 1:    print("virtual_limit_switch_output_signal status set on")
        virtual_limit_switch_output_signal.Pins_set_on()
    else:
        if _debug_mode == 1:    print("virtual_limit_switch_output_signal status set off")
    time.sleep(1)
    # RESETING LOCK BY SETTING 0 ON P7 INPUT (one of two inputs which reflects status of LOCKING)
    if _debug_mode == 1:    print("init process")
    virtual_limit_switch_output_signal.Pins_set_on()  # ON-state means PIN is not closed OFF-state means OUTPUT PIN is closed
    # _object_mmi._instrument.write_register(40, 1)
    # time.sleep(0.2)
    # _object_mmi._instrument.write_register(40, 0)  # reset register state
    if _debug_mode == 1:    print("start measuring aux eletrolock")

    while measurement_time_now < 4:
        time.sleep(0.2)
    _object_mmi._instrument.write_register(40, 2)  # close electrolock

    if _debug_mode == 1:    print("electrolock closing command")

    current_threshold_closed_reed = 100.0  # [mA]
    i = 0
    while _WattMeasurementClass_object.last_measured_val[2] < current_threshold_closed_reed:  ## actual current value
        # !!!brak testu otwarcia poprzez krancowke
        if _debug_mode == 1:    print("electrolock closing... waiting for reed is closed")
        print("current_threshold_closed_reed=",_WattMeasurementClass_object.last_measured_val[2],"expected value=",current_threshold_closed_reed,'[mA]')
        time.sleep(1)
        i += 1
        if i == 10:
            if _debug_mode == 1:    print(
                "!!No confirm of electro-lock closing | measurement incomplete | emergency break")
            # for security reasons if limit switch is not closed but it is possible that electrolock is powered on
            # and starts to heat up after 10 seconds
            virtual_limit_switch_output_signal.Pins_set_off()  # sending signal emulating closed limit switch "krańcówka" ;signal low means closed limit sw
            break

    if _WattMeasurementClass_object.last_measured_val[2] > current_threshold_closed_reed:
        for i in range(0, 10):
            if _debug_mode == 1:    print(_WattMeasurementClass_object.last_measured_val[2])

            time.sleep(0.1)
            if _debug_mode == 1:    print("measurement ok electrolock is closed")
        time.sleep(4)

        virtual_limit_switch_output_signal.Pins_set_off()  # (podaj sygnał emulujący zatrzaśniętą krańcówkę stan niski to zatrzaśnięcie)
        if _debug_mode == 1:    print("sending confirm : 'electrolock closed' ")
        time.sleep(1)

    if _debug_mode == 1:    print("openning electrolock")
    _object_mmi._instrument.write_register(40, 1)  # command OPEN (-12V)
    # !!! brak testu otwarcia
    time.sleep(1)
    if _debug_mode == 1:    print("return to state before measurement process")
    # return to zero state
    virtual_limit_switch_output_signal.Pins_set_on()  # initial status of port is high and this will not activate additional relays

    # sciaga testowanie bitów w expanderze DI/DO
    # print("test bitów", end=' ')
    # virtual_limit_switch_output_signal.test_bit(bit=0, echo=1)
    # real_limit_switch_input_signal.test_bit(bit=7, echo=1)
    # virtual_limit_switch_output_signal.Pins_set_on()
    # virtual_limit_switch_output_signal.test_bit(bit=0, echo=1)
    # real_limit_switch_input_signal.test_bit(bit=7, echo=1)  # shows only specific bit
    # real_limit_switch_input_signal.test_register(echo=1)  # shows whole register

    watt_meter_list = [_WattMeasurementClass_object]
    return watt_meter_list


def _scope_timer(measure_period, _process_thread_list, end_event, object_mmi=None, _debug_mode=0):
    if _debug_mode == 1:
        print("##############STARTING#################SCOPE_TIMER")
    _measure_period = measure_period
    process_thread_list = _process_thread_list

    global measurement_time_now
    measurement_time_now = 0
    t_start_global = np.around(time.perf_counter(), 4)
    while not end_event.is_set():
        measurement_time_now = np.around(time.perf_counter() - t_start_global, 6)
        time.sleep(0.5)

    if _debug_mode == 1:
        print("******************scope timer timeout")


def _additonal_task_2_switching_relays(_WattMeasurementClass_object, _object_mmi=None):
    # SWITCHING RELAYS
    if _WattMeasurementClass_object.corelated_modbus_port != None:
        time.sleep(2)
        _object_mmi._write_register(_WattMeasurementClass_object.corelated_modbus_port, 2)
        time.sleep(2)
        _object_mmi._write_register(_WattMeasurementClass_object.corelated_modbus_port, 1)
        time.sleep(2)
        _object_mmi._write_register(_WattMeasurementClass_object.corelated_modbus_port, 2)


def _additonal_task_1_switching_relays(_WattMeasurementClass_object, _object_mmi=None):
    pass


## TASK_1-EVERY MEASUREMENT STARTS IN SAME TIME
def _scheduler_task_1(_process_thread_list, object_mmi=None):
    process_thread_list = _process_thread_list
    process_thread_list[0].start()
    if process_thread_list[11]:
        process_thread_list[11].start()
    if process_thread_list[12]:
        process_thread_list[12].start()

    started_processes = 0
    number_active_processes = 0
    event_flag_relays_sw_on = False
    relays_sw_time = 4.2
    ## watt_measurement
    for i in range(1, 7):
        if process_thread_list[i]:
            watt_measurement_dict[("msrmnt_set_" + str(i))].watt_measure_show_info()
            process_thread_list[i].start()
            started_processes += 1

    ## additional events during measurements
    for i in range(1, 7):
        if process_thread_list[i] and process_thread_list[20 + i]:
            process_thread_list[20 + i].start()
            print("additional process", i)

    ## testing alive process and exititng VADC processess and scope
    while number_active_processes < started_processes:
        if measurement_time_now > relays_sw_time and event_flag_relays_sw_on == False:
            time.sleep(0.5)
            object_mmi._instrument.write_registers(1523, [1, 1, 1, 1])  # close relays
            event_flag_relays_sw_on = True
        for i in range(1, 7):
            if process_thread_list[i]:
                if not process_thread_list[i].is_alive():
                    number_active_processes += 1
        if number_active_processes < started_processes:
            number_active_processes = 0
        time.sleep(0.001)

    ##?     NIE WIEM SZY FLAGI SA UZYTKOWANE
    vadc_relays_stop_event.set()
    vadc_aux_stop_event.set()
    scope_timer_stop_event.set()
    time.sleep(0.4)
    vadc_relays_stop_event.clear()
    vadc_aux_stop_event.clear()
    scope_timer_stop_event.clear()

    # making logs of each measurement
    for i in range(1, 7):
        if process_thread_list[i]:
            watt_measurement_dict[("msrmnt_set_" + str(i))].watt_measurement_make_log()
    print("##############################END OF TASK 1")


## TASK-2 EVERY MEAUREMENT STARTS AFTER PREVIOUS HAS BEEN FINISHED
def _scheduler_task_2(_process_thread_list, object_mmi=None):
    print("###############MEASUREMENT ALL WATTMETERS ONE AFTER ANOTHER")
    process_thread_list = _process_thread_list

    for h in range(len(process_thread_list)):
        print(h, " : ", process_thread_list[h])
    process_thread_list[0].start()

    for i in range(1, 7):
        if process_thread_list[i]:
            # print(process_thread_list[i])
            print("..................process_thread....")
            watt_measurement_dict[("msrmnt_set_" + str(i))].watt_measure_show_info()
            time.sleep(1)
            if process_thread_list[11]:
                if not process_thread_list[11].is_alive():
                    # every thread aftr stopping must reintialized once more ...
                    if watt_measurement_dict[("msrmnt_set_" + str(i))].vadc_device_label == "vadc_relays":
                        process_thread_list[11] = threading.Thread(target=vadc_relays.measure_continous,
                                                                   name="vadc_relays_thread",
                                                                   args=(0, vadc_relays_stop_event, 0))
                        process_thread_list[11].start()
                        time.sleep(.1)
                        while not process_thread_list[11].is_alive():
                            time.sleep(.1)
                            print("vadc_relay not ready")
            if process_thread_list[12]:
                if not process_thread_list[12].is_alive():
                    if watt_measurement_dict[("msrmnt_set_" + str(i))].vadc_device_label == "vadc_aux":
                        process_thread_list[12] = threading.Thread(target=vadc_aux.measure_continous_single_channel,
                                                                   name="vadc_aux_thread",
                                                                   args=(0, vadc_relays_stop_event, 0))
                        process_thread_list[12].start()
                        time.sleep(.1)
                        while not process_thread_list[12].is_alive():
                            time.sleep(0.1)
                            print("vadc_aux not ready")

            process_thread_list[i].start()
            # additional tasks
            if i <= 5: _additonal_task_2_switching_relays(watt_measurement_dict[("msrmnt_set_" + str(i))],
                                                          object_mmi)
            if i == 6: process_thread_list[16].start()
            # join makes that when first process is running everything after command join() waits until first process ends
            process_thread_list[i].join()
            vadc_relays_stop_event.set()
            vadc_aux_stop_event.set()
            time.sleep(0.1)
            vadc_relays_stop_event.clear()
            vadc_aux_stop_event.clear()


scheduler_task_select_dict = {
    'task_1': _scheduler_task_1,
    'task_2': _scheduler_task_2
}


def _scheduler(_process_thread_list, object_mmi, task_select):
    scheduler_task_select_dict[task_select](_process_thread_list, object_mmi)
    # _scheduler_task_1(_process_thread_list, object_mmi)
    # _scheduler_task_2(_process_thread_list, object_mmi)


## @ADDITIONAL_INFO object_mmi arg  is mmi from hotplug.machine_interface but it cannot
## @ADDITIONAL_INFO be imported from submodule position
## @ADDITIONAL_INFO object_mmi like mmi cant be passed by script from "upper" folder
def watt_meter_relay_test_beta(measure_period, debug_mode_list,
                               enabled_devices_list, object_mmi=None, task_type=None):
    global scope_timer_stop_event
    scope_timer_stop_event = threading.Event()
    global vadc_relays_stop_event
    vadc_relays_stop_event = threading.Event()
    global vadc_aux_stop_event
    vadc_aux_stop_event = threading.Event()
    global additional_task_event
    additional_task_event = []

    _measure_period = measure_period
    measure_period_aux = _measure_period
    process_thread_list = [None for i in range(28)]
    try:
        global vadc_relays
        # vadc_relays = VADC(0x6a)
        vadc_relays = VADC_ADS(0x48)

    except:
        print("PROPABLY CONNECTION ERROR WITH RELAYS VADC (MCP3424) ")
        time.sleep(5)
        sys.exit(1)
    vadc_relays.results = [nan, nan, nan, nan]

    try:
        global vadc_aux
        # vadc_aux = VADC(0x6e)
        vadc_aux = VADC_ADS(0x48)
    except:
        print("PROBABLY CONNECTION ERROR WITH AUX VADC (MCP3424) ")
        time.sleep(5)
        sys.exit(1)
    vadc_aux.results = [nan, nan, nan, nan]

    ## initialization multiple scopes based on WattMeasurementClass class
    for i in range(len(enabled_devices_list)):
        ## choice of VADC
        tmp_string_wattmeter = 'msrmnt_set_' + str(i + 1)
        if enabled_devices_list[i]:  # device enable check
            ## init WattMeasurementClass instances
            watt_measurement_dict[tmp_string_wattmeter] = WattMeasurementClass(tmp_string_wattmeter,
                                                                               input_matrix_measurement_group_dict[
                                                                                   tmp_string_wattmeter])
            ## creating process threads for multi-threading
            ## threading used to run parallel or sequential processes
            tmp_label_thread_name = 'processThread_' + str(i + 1)
            ## creating list of threads
            process_thread_list[i + 1] = threading.Thread(
                target=watt_measurement_dict[tmp_string_wattmeter].measure_val,
                name=tmp_label_thread_name,
                args=(measure_period, debug_mode_list[i]))

            if watt_measurement_dict[tmp_string_wattmeter].vadc_device_label == 'vadc_aux':
                process_thread_list[i + 1] = threading.Thread(
                    target=watt_measurement_dict[tmp_string_wattmeter].measure_val,
                    name=tmp_label_thread_name,
                    args=(measure_period_aux, debug_mode_list[i]))

            # creating additional tasks for each measurement
            if input_matrix_measurement_group_dict[tmp_string_wattmeter][4] is not None:
                # watt_measurement_dict[("msrmnt_set_" + str(i))].corelated_modbus_port is not None:
                process_thread_list[20 + i + 1] = threading.Thread(
                    target=_additonal_task_1_switching_relays,
                    name='additional_task_1_sw_relay_' + str(i),
                    args=(watt_measurement_dict[("msrmnt_set_" + str(i + 1))],
                          object_mmi)
                )
                if i + 1 == 6:
                    aux_test_measure_period = 10  # not used
                    process_thread_list[26] = threading.Thread(
                        target=watt_meter_aux_test,
                        name="aux_test",
                        args=(object_mmi, watt_measurement_dict['msrmnt_set_6'], aux_test_measure_period, 1))
        else:
            process_thread_list.append(None)


    ## ADDITIONAL THREADS
    process_thread_list[0] = threading.Thread(target=_scope_timer,
                                              name="scope_timer_thread",
                                              args=(
                                                  measure_period, process_thread_list, scope_timer_stop_event,
                                                  object_mmi, 1),
                                              daemon=True)
    process_thread_list[11] = threading.Thread(target=vadc_relays.measure_continous,
                                               name="vadc_relays_thread",
                                               args=(0, vadc_relays_stop_event, 0))
    # dodawanie tego procesu wtedy jest realizowany pomiar aux
    # process_thread_list[12] = threading.Thread(target=vadc_aux.measure_continous,
    #                                            name="vadc_aux_thread",
    #                                            args=(0, vadc_aux_stop_event, 0))

    ## init gpio expander with relays expander
    _precharging_relays_expander(output_pins=PIN_A_ALL, time_length=0.5)
    time.sleep(1)
    PIN_A_ALL.Pins_set_off()

    ## main measurement method
    _scheduler(process_thread_list, object_mmi, task_type)

    ## EXITING MEASUREMENT
    PIN_A_ALL.Pins_set_on()  # switching off GPIO EXPANDER relays
    ## setting steamjet's relays
    if object_mmi != None:
        print("#### SWITCHING OFF ALL RELAYS 1519-1527")
        for n in range(1519, 1527):
            object_mmi._instrument.write_register(n, 2)  ## set off relays
    print("#### MEASUREMENTS ARE COMPLETED ")
    return watt_measurement_dict.items()


print("sprawdzenie instancji klasy")

if __name__ == '__main__':
    # from DFRobot_INA219 import INA219
    # import i2c_stm as i2c_expander
    #
    # NOT WORKING !!!!!
    #
    #
    measure_period = 10
    enabled_debug_mode_list = [1, 1, 1, 1, 1, 1]
    enabled_devices_list = [1, 1, 1, 1, 1, 1]
    # !!! trzeba dodac funckje bez użycia mmi
    # results = watt_meter_relay_test(20,enabled_debug_mode_list,enabled_devices_list)
    # object_mmi = mmi
    # results = watt_meter_relay_test_beta(measure_period, debug_mode_list, enabled_devices_list, object_mmi)


def _precharging_relays_expander(output_pins, time_length):
    # test of relays expander (! known problem without precharging some output ports sometimes
    # are not stable)
    # it happends only at the beginning after powering-on whole system
    # switching on and off couple times resolves this issue
    output_pins.Pins_set_off()
    time.sleep(time_length)
    output_pins.Pins_set_on()
    time.sleep(time_length)
    output_pins.Pins_set_off()
    time.sleep(time_length)
    output_pins.Pins_set_on()  # ON-output means no current flows by the output port (inverted logic)
    time.sleep(time_length)
