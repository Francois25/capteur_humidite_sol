from machine import Pin
import time

LED_BLINK = Pin(2, Pin.OUT)

def led_init():
    LED_BLINK.value(0)

def led_blink():
    led = LED_BLINK
    led.value(1)
    time.sleep(1)
    led.value(0)
    time.sleep(1)