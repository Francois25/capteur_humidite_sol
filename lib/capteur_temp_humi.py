# Prise de mesure du capteur de température et d'humidité
#--------------------------------------------------------
from machine import Pin
import dht

def sensor(Pin_number):
    sensor = dht.DHT22(Pin_number)
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        if temp and hum:
            # uncomment for Fahrenheit
            #temp = temp * (9/5) + 32.0
            return temp, hum
        else:
            return None
    except Exception as e:
        print("EXCEPT ERROR: Failed to return temperature sensor information", e)
        return None
