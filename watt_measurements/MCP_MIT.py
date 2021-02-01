#!/usr/bin/env python

import logging
import time

import glob
import smbus
from MCP342x import MCP342x

__author__ = 'Steve Marple'
__version__ = '0.3.4'
__license__ = 'MIT'


# ten skrypt dziala i nie ruszam
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
        return smbus.SMBus(candidates[0])
    elif len(candidates) == 0:
        raise Exception("Could not find an I2C bus")
    else:
        raise Exception("Multiple I2C busses found")


class __MCP342x():
    def __init__(self, addr, CH_select):
        self.addr = addr
        self.CH_select = CH_select
        self.adcs = []
        for i in range(len(self.CH_select)):
            tmp_str = 'CH' + str(i)
            if CH_select[i] == 'CH' + str(i + 1):
                string = "var" + str(i)
                self.adcs.append(MCP342x(bus, address=self.addr, channel=i, resolution=12))
            else:
                print("error in initialization of MCP342x (VADC)", i, CH_select[i], tmp_str, addr)

    def read(self, samples=1, sleep=0.1, period=10):
        t_start = time.time()
        local_adcs = self.adcs
        print("adres MCP3424 =", hex(self.addr))
        if period == 0:
            while True:
                r = MCP342x.convert_and_read_many(local_adcs, samples=1)
                # print("{} {0:.2f} {}".format(samples, time.time() - t_start, r))
                print('')
                samples += 1
                time.sleep(sleep)
        else:
            while time.time() - t_start < period:
                r = MCP342x.convert_and_read_many(local_adcs, samples=1)
                print('{} {:.2f} {}'.format(samples, time.time() - t_start, r))
                # print('{0:.2f}'.format(time.time()-t_start))
                # print('{}'.format(r))
                # print('')
                samples += 1
                time.sleep(sleep)


logging.basicConfig(level='WARNING')  # DEBUG

logger = logging.getLogger(__name__)

bus = get_smbus()
# reset is important to set i2c address same as configuration of hardware dip switches
MCP342x.general_call_reset(bus)
print(bus)
# bus = smbus.SMBus(1)

# address = 0x68  # Off offf
# addr68_ch0 = MCP342x(bus, address=0x68, channel=0, resolution=12)
# addr68_ch1 = MCP342x(bus, address=0x68, channel=1, resolution=12)
# addr68_ch2 = MCP342x(bus, address=0x68, channel=2, resolution=12)
# addr68_ch3 = MCP342x(bus, address=0x68, channel=3, resolution=12)
# address = 0x6a  # on off
# addr68_ch0 = MCP342x(bus, address=0x6a, channel=0, resolution=12)
# addr68_ch1 = MCP342x(bus, address=0x6a, channel=1, resolution=12)
# addr68_ch2 = MCP342x(bus, address=0x6a, channel=2, resolution=12)
# addr68_ch3 = MCP342x(bus, address=0x6a, channel=3, resolution=12)
# # Create objects for each signal to be sampled
# address = 0x6c  # off on
# addr6c_ch0 = MCP342x(bus, address=0x6c, channel=0, resolution=12)
# addr6c_ch1 = MCP342x(bus, address=0x6c, channel=1, resolution=12)
# addr6c_ch2 = MCP342x(bus, address=0x6c, channel=2, resolution=12)
# addr6c_ch3 = MCP342x(bus, address=0x6c, channel=3, resolution=12)
# address = 0x6e  # on on z tym adresem sa problemy
# addr6e_ch0 = MCP342x(bus, address=0x6e, channel=0, resolution=12)
# addr6e_ch1 = MCP342x(bus, address=0x6e, channel=1, resolution=12)
# addr6e_ch2 = MCP342x(bus, address=0x6e, channel=2, resolution=12)
# addr6e_ch3 = MCP342x(bus, address=0x6e, channel=3, resolution=12)

# addr69_ch0 = MCP342x(bus, 0x69, channel=0, resolution=18)
# addr69_ch1 = MCP342x(bus, 0x69, channel=1, resolution=18)
# addr69_ch2 = MCP342x(bus, 0x69, channel=2, resolution=18)

# Create a list of all the objects. They will be sampled in this
# order, unless any later objects can be sampled can be moved earlier
# for simultaneous sampling.
# adcs = [addr69_ch
# 0, addr69_ch1, addr69_ch2, addr69_ch3]# addr68_ch3]

# adcs = [addr6e_ch1]
#         addr69_ch0, addr69_ch1, addr69_ch2]
# adcs = [addr68_ch0, addr68_ch1, addr68_ch2, addr68_ch3]
# adcs = [addr68_ch0]  # , addr68_ch1, addr68_ch2, addr68_ch3]
# r = MCP342x.convert_and_read_many(adcs, samples=2)
# print('return values: ')
# print(r)


voltage_divider = 1000 / 11000
divider = 1 / voltage_divider
# , scale_factor=2.448579823702253
# addr68_ch0.convert()
# print(addr68_ch3.convert_and_read())
#
# print( addr68_ch2.get_scale_factor(),addr68_ch2.get_offset(),addr68_ch2.get_resolution(),addr68_ch2.get_gain())
# print( addr68_ch3.get_scale_factor(),addr68_ch3.get_offset(),addr68_ch3.get_resolution(),addr68_ch3.get_gain())
if __name__ == "__main__":
    print("direct execution")
    # class init
    ADC_0x6a = __MCP342x(addr=0x6a, CH_select=['CH1', 'CH2', 'CH3', 'CH4'])
    ADC_0x6a.read(samples=1, sleep=0.1, period=100)

    ADC_0x6e = __MCP342x(addr=0x6e, CH_select=['CH1', 'CH2', 'CH3', 'CH4'])

    ADC_0x6e.read()

    # while True:
    #     #    i=i+1
    #     # print(end='\n')
    #     # print(x.get_config())
    #     # ch2_vol=addr68_ch2.convert_and_read()
    #     # ch2_vol_scaled=11.1*ch2_vol
    #     # ch3_vol=addr68_ch3.convert_and_read()
    #     # ch3_vol_scaled=11.1*ch3_vol
    #     # print("ch2",ch2_vol,ch2_vol_scaled,"ch3",ch3_vol,ch3_vol_scaled)
    #     # print(addr68_ch2.raw_read())
    #     # print(adcs)
    #     time.sleep(0.05)
    #     r = MCP342x.convert_and_read_many(adcs, samples=1)
    #     print('')
    #     time.sleep(0.1)
    #     # _ = system('clear') #czyszczenie ekranu
    #     # print(r[0])
    #     # print(r[3])
    #     # print(type(r[3][0]))
    #     # z = np.round(r)
    #     for n in r:
    #         # print(type(n))
    #         # print(round(n,2))
    #         #
    #         print("{0:.3f} ".format(11 * n[0]), end='')
    #     print("")
    #     # print("{0:.2f}".format(round(a, 2)))
    #     # print(r)
