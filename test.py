import machine
import utime as time

START_CHRONO = 0
relais_pin=Pin(2, Pin.OUT)

# # Configuration de la durée de la veille profonde en millisecondes
# deep_sleep_duration = 10 * 60 * 1000  # 10 minutes en millisecondes

# print("Entrée en veille profonde pour {} millisecondes".format(deep_sleep_duration))
# machine.deepsleep(deep_sleep_duration)

# # Ce code ne sera pas atteint car l'ESP32 entre en veille profonde
# print("Ce message ne devrait pas apparaître")

while True:
    chrono_watering = time.ticks_ms()
    diff_chrono_watering = time.ticks_diff(chrono_watering, START_CHRONO / 1000)
    while diff_chrono_watering < 10:
        print(diff_chrono_watering)
        relais_pin.value(1)
    relais_pin.value(0)