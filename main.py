import aioble
import asyncio

import gc

import time

from machine import Pin, PWM

duration_ms = 30000  # set to 0 for continuous
duration_ms = 0

beacon_name = "BCPro_204880"
beacon_addr = "dd:88:00:00:08:52"

backoff_interval = 2  # units is seconds


class Servo:
    # these defaults work for the standard TowerPro SG90
    __servo_pwm_freq = 50
    __min_u10_duty = 26 - 0 # offset for correction
    __max_u10_duty = 123- 0  # offset for correction
    min_angle = 0
    max_angle = 180
    current_angle = 0.001


    def __init__(self, pin):
        self.__initialise(pin)


    def update_settings(self, servo_pwm_freq, min_u10_duty, max_u10_duty, min_angle, max_angle, pin):
        self.__servo_pwm_freq = servo_pwm_freq
        self.__min_u10_duty = min_u10_duty
        self.__max_u10_duty = max_u10_duty
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.__initialise(pin)


    def move(self, angle):
        print("we have been told to move...")
        # round to 2 decimal places, so we have a chance of reducing unwanted servo adjustments
        angle = round(angle, 2)
        # do we need to move?
        if angle == self.current_angle:
            return
        self.current_angle = angle
        # calculate the new duty cycle and move the motor
        duty_u10 = self.__angle_to_u10_duty(angle)
        self.__motor.duty(duty_u10)

    def __angle_to_u10_duty(self, angle):
        return int((angle - self.min_angle) * self.__angle_conversion_factor) + self.__min_u10_duty


    def __initialise(self, pin):
        self.current_angle = -0.001
        self.__angle_conversion_factor = (self.__max_u10_duty - self.__min_u10_duty) / (self.max_angle - self.min_angle)
        self.__motor = PWM(Pin(pin))
        self.__motor.freq(self.__servo_pwm_freq)
        print("we have been told to __initialise")
        


async def scan():
    wait_until = 0
    state = False
    
    
    motor=Servo(pin=22)
    print("Scan:", motor)
    motor.move(0)

    try:
        async with aioble.scan(duration_ms, interval_us=30000, window_us=30000, active=True) as scanner:
        # async with aioble.scan(duration_ms=5000, interval_us=30000, window_us=30000, active=True) as scanner:
            async for result in scanner:
                # print("Free memory:", gc.mem_free())
                if result.device.addr_hex() == beacon_addr:
                    # print(result, result.name(), result.rssi, result.services(), type(result.device.addr_hex()))
                    if time.time() > wait_until:
                        state = not state
                        if state:
                            print("Turn faucet ON")
                            motor.move(90)
                        else:
                            print("Turn faucet OFF")
                            motor.move(0)
                        print(result.name(), result.device.addr_hex(), result.rssi, wait_until)
                        wait_until = time.time() + backoff_interval

    except Exception as e:
        print('!!!!! Exception in aioble scan')
        print(e)
      
asyncio.run(scan())

