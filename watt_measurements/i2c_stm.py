#!/usr/bin/python

import smbus
import time

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

DEVICE_ADDRESS = 0x20  # 0x0a      #7 bit address (will be left shifted to add the read write bit)
DEVICE_REG_MODE1 = 0x00


def __read_all():
    n = 0

    while (n < 31):
        # response=bus.read_i2c_block_data(DEVICE_ADDRESS,0,31)
        response_byte = bus.read_byte_data(DEVICE_ADDRESS, n)
        print(n, "response=", response_byte)
        n = n + 1
        time.sleep(0.01)


def read_all_test():
    n = 0

    while (n < 31):
        # response=bus.read_i2c_block_data(DEVICE_ADDRESS,0,31)
        response_byte = bus.read_byte_data(DEVICE_ADDRESS, n)
        print(n, "response=", response_byte)
        n = n + 1
        time.sleep(0.01)


def __byte_read(n, refresh_rate):
    while 1:
        response_byte = bus.read_byte_data(DEVICE_ADDRESS, n)
        print(n, "response=", response_byte, end='\r', flush=True)

        time.sleep(refresh_rate)


def __byte_read_single(n):
    response_byte = bus.read_byte_data(DEVICE_ADDRESS, n)
    print(n, "response=", response_byte)


def __byte_write(DEVICE_REG_MODE1, value):
    bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG_MODE1, value)


def __set_out_123A():
    bus.write_byte_data(DEVICE_ADDRESS, 0, 248)
    bus.write_byte_data(DEVICE_ADDRESS, 18, 0)
    time.sleep(50)
    bus.write_byte_data(DEVICE_ADDRESS, 18, 7)
    time.sleep(0.5)
    byte_read_single(18, 0.1)
    byte_read_single(20, 0.1)


def init_gpio_expander(GPIOx, PORT="A", GPIOtype="OUTPUT"):
    if PORT == "A":
        i2c_address = 0
    else:
        if PORT == "B":
            i2c_address = 1
    Register = bus.read_byte_data(DEVICE_ADDRESS, i2c_address)
    temp = Register

    if GPIOtype == "INPUT":
        for x in range(0, len(GPIOx)):
            temp |= 1 << (GPIOx[x])
    else:
        if GPIOtype == "OUTPUT":
            for x in range(0, len(GPIOx)):
                temp &= ~(1 << GPIOx[x])

    bus.write_byte_data(DEVICE_ADDRESS, i2c_address, temp)


def reset_gpio_expander():
    bus.write_byte_data(DEVICE_ADDRESS, 0, 255)
    bus.write_byte_data(DEVICE_ADDRESS, 1, 255)
    bus.write_byte_data(DEVICE_ADDRESS, 18, 0)
    bus.write_byte_data(DEVICE_ADDRESS, 19, 0)


def set_output_expander(setonoff, PORT, *GPIOx):
    if PORT == "A":
        i2c_address = 18
    else:
        if PORT == "B":
            i2c_address = 19
    register = bus.read_byte_data(DEVICE_ADDRESS, i2c_address)
    if setonoff == 1:
        for x in range(0, len(GPIOx)):
            register |= 1 << (GPIOx[x])
    else:
        for x in range(0, len(GPIOx)):
            register &= ~(1 << (GPIOx[x]))

    bus.write_byte_data(DEVICE_ADDRESS, i2c_address, register)


# def __init_gpio_expander_out(PORT, *GPIOx):
#     reset_gpio_expander()
#     time.sleep(1)
#     init_gpio_expander(GPIOx, PORT="A", GPIOtype="OUTPUT")


class GPIO:
    def __init__(self, GPIOx, DEVICE_ADDRESS, PORT, GPIOtype, debug_mode="debug_off"):
        self.DEVICE_ADDRESS = DEVICE_ADDRESS
        self.PORT = PORT
        self.GPIOx = GPIOx
        self.GPIOtype = GPIOtype
        self.debug_mode = debug_mode
        init_gpio_expander(self.GPIOx, self.PORT, self.GPIOtype)

    def Pins_set_on(self):
        set_output_expander(1, self.PORT, *self.GPIOx)
        if self.debug_mode == "debug_on":
            print("SET ON")

    def Pins_set_off(self):
        set_output_expander(0, self.PORT, *self.GPIOx)
        if self.debug_mode == "debug_on":
            print("SET OFF")

    def read_all(self):
        n = 0
        while (n < 31):
            # response=bus.read_i2c_block_data(DEVICE_ADDRESS,0,31)
            response_byte = bus.read_byte_data(DEVICE_ADDRESS, n)
            print(n, hex(n), "   response=", response_byte)
            n = n + 1
            time.sleep(0.01)

    def test_register(self, echo=0):
        if self.PORT == 'B':
            status_register = 19
        else:
            status_register = 18
        response_byte = bus.read_byte_data(DEVICE_ADDRESS, status_register)
        if echo == 1: print('PORT=', self.PORT, 'register', status_register, ' response = ', response_byte)

    def test_bit(self, bit, echo=0):
        n = bit
        if self.PORT == 'B':
            status_register = 19
        else:
            status_register = 18
        response_byte = bus.read_byte_data(DEVICE_ADDRESS, status_register)
        x = (response_byte >> n) & 1
        if echo == 1: print('bit=', n, ' bit status=', x)
        return x

    def reset_expander(self):
        init_gpio_expander()

if __name__ == '__main__':
# PINS_345 = GPIO(3, 4, 5, DEVICE_ADDRESS=0x20, PORT="A", GPIOtype="OUTPUT")
# PINS_345.Pins_set_on()
# PINS_345.Pins_set_off()


# __init_gpio_expander_out("A", 3, 4, 5)
# time.sleep(1)
# __set_output_expander(1, "A", 3, 4, 5)
# time.sleep(1)
# __set_output_expander(0, "A", 3, 4, 5)
# __read_all()

    PIN_B7 = GPIO([7], DEVICE_ADDRESS=0x20, PORT="B", GPIOtype="INPUT",
                  debug_mode="debug_off")  # input ; detecting state of relay
    while True:
        PIN_B7.test_bit(7, echo=1)
