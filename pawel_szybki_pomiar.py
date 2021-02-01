# import watt_measurements.final_pomiary_class as fpc
#from watt_measurements.final_pomiary_class import WattMeasurementClass
from hotplug.machine_interface import *
from com_ports import serial_ports
import math
import random
import sys



def get_stjets_com_ports():
    # com_ports= ["/dev/ttyACM1"]
    com_ports = serial_ports()
    return com_ports


def set_show_test(bit=-1):
    # wylacz zawory
    if bit > -1:
        for _ in range(0, 8):
            mmi.change_relay_state(_, bit)
            print(_, end=" ")
            time.sleep(.1)
        print("")
    if bit == -1: print("test po uruchomieniu")
    if bit == 1: print("test wlaczenia")
    if bit == 2: print("test wylaczenia")
    if bit == 0: print("powrot do default")
    results = fpc.watt_meter_relay_test(0.5)
    min_min_val = -1.0
    min_val = 2.0
    max_val = 10
    max_max_val = 14
    print(results[0].results_avg)
    print(results[0].results_avg[3])
    if bit == 2:
        if min_min_val < results[0].results_avg[3] < min_val:
            print("passed")
        else:
            print("not passed")
    if bit == 1:
        if max_max_val > results[0].results_avg[3] > max_val:
            print("passed")
        else:
            print("not passed")


def temp_test(bit):
    for _ in range(0, 8):
        mmi.change_relay_state(_, bit)
        print(_, end=" ")
        print("")
        results = fpc.watt_meter_relay_test(0.5)

        print(results[0].results_avg[3])
        print(results[1].results_avg[3])
        print(results[2].results_avg[3])
        print(results[3].results_avg[3])
        time.sleep(2)
        t, s = mmi._get_process_type_and_DO_state()
        print("DO-state{0:b},{1}".format(s, s))

    print("")


def _all_relays_to(mmi, value):
    for relay in RelayAddressesEnum:
        mmi.change_relay_state(relay.value, value)
        sleep(1)


def scenariusz():
    # test na start
    set_show_test(-1)
    # wlacz zawory polecenie 2
    set_show_test(2)
    # wylacz zawory polecenie 0
    set_show_test(1)
    # p powrot default
    set_show_test(0)


com_ports = get_stjets_com_ports()
print(com_ports) # default ['/dev/ttyACM0']
mmi = ModbusMachineInterface(com_ports[0])
# mmi = ModbusMachineInterface('/dev/ttyACM0')


def set(value):
    print(value, end='')
    print(mmi._instrument.read_registers(40, 1), end='')
    time.sleep(0.2)
    mmi._instrument.write_register(40, value)
    time.sleep(0.2)
    print(mmi._instrument.read_registers(40, 1))


def losuj():
    n = 0
    while n < 200:
        set(random.randint(0, 3))
        # print(n,_mmi.get_process_running_name()," :",end="")
        time.sleep(0.1)
        n += 1


def scan(address, len):
    while 1:
        print(mmi._instrument.read_registers(address, len))
        time.sleep(0.1)


def scan_global(start, len):
    for n in range(start, start + len):
        try:
            print(n, mmi._instrument.read_registers(n, 1))
            time.sleep(0.01)
        except Exception as e:
            print(n, e)
            pass


def scan_active(start, len):
    tab = [0] * 2000
    tab2 = [0] * 2000
    for n in range(start, start + len):
        try:
            # print(n,mmi._instrument.read_registers(n,1))
            tab[n] = mmi._instrument.read_registers(n, 1)
            time.sleep(0.01)
        except Exception as e:
            print(n, e)
            pass
    print("koniecpierwszego pom")
    time.sleep(5)
    for n in range(start, start + len):
        try:
            # print(n,mmi._instrument.read_registers(n,1))
            tab2[n] = mmi._instrument.read_registers(n, 1)
            time.sleep(0.01)
            if tab2[n] != tab[n]:
                print(n, tab[n], tab2[n])
        except Exception as e:
            print(n, e)
            pass


if __name__ == "__main__":
    print("direct execution")
    # # wylacz zawory polecenie 0
    # set_show_test(1)
    # temp_test(0.1)
    # t,s = mmi._get_process_type_and_DO_state()
    # print("{0:b}".format(s))

    # start_add = 0
    # length_add = 50
    # for n in range (start_add, length_add) :
    #     print(n,mmi._instrument.read_registers(n,1))
    #
    # print("0")
    # mmi._instrument.write_register(40, 0)
    # mmi._instrument.read_registers(40, 1)
    # time.sleep(2)
    # print("1")
    # mmi._instrument.write_register(40,1)
    # mmi._instrument.read_registers(40, 1)
    # time.sleep(2)
    # print("2")
    # mmi._instrument.write_register(40, 2)
    # mmi._instrument.read_registers(40, 1)
    # time.sleep(2)
    # print("3")
    # mmi._instrument.write_register(40, 3)
    # mmi._instrument.read_registers(40, 1)
    # time.sleep(2)
    # print("0")
    # mmi._instrument.write_register(40, 0)
    # mmi._instrument.read_registers(40, 1)
    # # time.sleep(2)
    # losuj(mmi)
    # print("stop proces")
    # mmi.stop_process()
    # losuj(mmi)

    # scan_global(0,100)
    # scan_active(0,100)
    #  scenariusz()

    # mmi.start_process(ProcessType.P_134)
    # losuj()
    # mmi.stop_process()
    # losuj()
    # # n= 0
    # while n<100 :
    #     try:
    #         n += 1
    #         set (n-50)
    #         # print(n,_mmi.get_process_running_name()," :",end="")
    #         time.sleep(0.1)
    #
    #     except Exception as e :
    #         print(e)
    #         pass
    #

    # PIN_B0 = fpc.i2c_expander.GPIO(0, DEVICE_ADDRESS=0x20, PORT="B", GPIOtype="OUTPUT", debug="debug_off")
    # PIN_B0.Pins_set_off()
    # time.sleep(1)
    # PIN_B0.Pins_set_on()
    # time.sleep(1)
    # PIN_B0.Pins_set_off()
    # time.sleep(1)
    # PIN_B0.Pins_set_on()

    measure_period = 100
    # watt_meter_5 = fpc.WattMeter("watt_meter_5")
    # print(fpc.mcp_v_aux)
    # while 1:
    # print(fpc.mcp_v_aux.results[0])
    # print(fpc.mcp_v_aux.results[1])
    # print(fpc.mcp_v_aux.results[2])
    # print(fpc.mcp_v_aux.results[3])
    # fpc.mcp_v_aux.measure_continous(10,1)
    # watt_meter_5.measure_val(measure_period,"vadc_ch0",fpc.mcp_v_aux, "debug_on")
    # fpc.watt_meter_relay_test(measure_period=20)
    #####x=fpc.watt_meter_aux_test(object = mmi, measure_period=10)
    # for n in range(1519, 1527):
    #     mmi._instrument.write_register(n, 2)
    #     print(n)
    # sleep(3)


    # enabled_debug_mode_list = \
    #     [2,2, 2, 2, 2, 2]
    # enabled_devices_list = \
    #     [1,1, 1, 1, 1, 1]
    enabled_debug_mode_list = \
        [0, 0, 0, 0, 0, 2]
    enabled_devices_list = \
        [0, 0, 0, 0, 0, 1]


    # y = fpc.watt_meter_relay_test_beta(15, enabled_debug_mode_list, enabled_devices_list, mmi, "task_1")
    # sleep(3)
    # for n in range(1519, 1527):
    #   mmi._instrument.write_register(n, 1)
    #  print(n)
    # sleep(3)

    # sleep(3)
    # y = fpc.watt_meter_relay_test(5, enabled_debug_mode_list, enabled_devices_list)
    # sleep(3)

    #swieze
    import watt_measurements.final_pomiary_class as fpc
    y = fpc.watt_meter_relay_test_beta(20, enabled_debug_mode_list, enabled_devices_list, mmi,'task_1')
    #

    # sleep(5)
    # y = fpc.watt_meter_relay_test_beta(20, enabled_debug_mode_list, enabled_devices_list, mmi, 'task_1')
    # sleep(5)
    # y = fpc.watt_meter_relay_test_beta(20, enabled_debug_mode_list, enabled_devices_list, mmi, 'task_1')
    ## bezpieczne wyłączenie wszystki zaworów może ustawienie na 0 będzie lepsze



    ###
    # testowanie
    ###
    # import sys
    # import time
    # print("#### SWITCHING OFF ALL RELAYS 1519-1527")
    # bit = 0
    # while True:
    #     time.sleep(2)
    #     if bit == 1 : bit =0
    #     else : bit = 1
    #     for n in range(1519, 1527):
    #         mmi._instrument.write_register(n, bit, )
    #         # read_result=mmi._instrument.read_register(n, bit, )
    #         # print(read_result)
    ###
