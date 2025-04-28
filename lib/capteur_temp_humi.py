# Prise de mesure du capteur de température et d'humidité
#--------------------------------------------------------
from machine import Pin
import dht

def sensor(pin):
    sensor = dht.DHT22(pin)
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        if temp and hum:
            # uncomment for Fahrenheit
            #temp = temp * (9/5) + 32.0
            return temp, hum
        else:
            print('Invalid temperature sensor reading')
            print('Temp value use : 15°C')
            return None
    except:
        print("EXCEPT ERROR: Failed to return temperature sensor information")
        print("EXCEPT ERROR : temp value use : 15°C")
        return None
