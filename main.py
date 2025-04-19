# CAPTEUR HUMIDITE SOL CONNECTE
from machine import ADC, Pin, UART, RTC, lightsleep, WDT

import mailing_config
import wificonfig
import wificonnect
import picoweb
import umail
import utime as time
import uasyncio as asyncio
import random


# --------------------- WIFI ------------------------
# enter your wifi ssid and your password in wificonfig file
ipaddress = wificonnect.connectSTA(ssid=wificonfig.ssid, password=wificonfig.password)

# ------------------- SET UP -------------------------
# Configuration de la durée de la veille profonde en microsecondes
last_mail = 0
watchdog_timer = WDT(timeout=10000)  # Timeout en millisecondes (ici 10s)

# Setup Pin ESP32
default_led_captor = Pin(14, Pin.OUT, 0)
led_not_enough_water = Pin(2, Pin.OUT)  # board LED
sensor_humidity_pin = Pin(32)  # choisir un pin analogique sur l'ESP
relais_pin = Pin(33, Pin.OUT) # choisir un pin analogique sur l'ESP
manual_watering_button = Pin(12, Pin.IN, Pin.PULL_UP)  # Bouton branché entre GPIO12 et GND


# Variables générique
HUMIDITE_MINI = 4095
HUMIDITE_MAX = 1170
WATERING_TIME = 10 # temps d'arrosage en seconde


# ------------------- PROG MAIN ----------------------
# Reconnection Wifi si perte et clignotement de la led de board tant qu'il n'y a pas de wifi          
async def wifi_monitor(ssid, password):
    import wificonnect
    while True:
        if not wificonnect.is_connected():
            print("Connexion Wi-Fi perdue")
            # Fait clignoter la LED pendant 5 secondes
            for _ in range(10):
                led_not_enough_water.value(1)
                await asyncio.sleep(0.5)
                led_not_enough_water.value(0)
                await asyncio.sleep(0.5)
            wificonnect.reconnect(ssid, password)
        else:
            await asyncio.sleep(10)  # Vérifie la connexion toutes les 10 secondes            
            
# fonction lire le taux d'humidité
def get_taux(pin=sensor_humidity_pin, humidity=0):
    adc = ADC(pin)
    adc.atten(ADC.ATTN_11DB)  # Adapter en fonction de la plage de tension du capteur
    adc.width(ADC.WIDTH_12BIT)  # Plage de 0-4095
    try:
        value = adc.read()
        print(('-' * 11), '\n', f"valeur lue: {value}")

        # -------------- ACTIVE 2 NEXTS LIGNES FOR TEST ------------------
        # humidity = 9
        # humidity = random.choice([7, 9, 20])

        # -------------- DEACTIVE NEXT LIGNE FOR TEST ------------------
        humidity = (1 - (value - HUMIDITE_MAX) / (HUMIDITE_MINI - HUMIDITE_MAX)) * 100

        if (humidity > 100) or (humidity < 0):
            print("Le taux d'humidité est anormal, contrôle du capteur nécessaire")
            default_led_captor.value(1)

        else:
            default_led_captor.value(0)
            print(('-' * 11), '\n', f"Le taux d'humidité est de {humidity:.0f}%")
            
    except:
        print("Echec de la lecture du capteur")
    
    return float(round(humidity, 2))


def send_mail(to_address, subject, body):
    global last_mail
    last_mail = time.ticks_ms()
    
    if not wificonnect.is_connected():
        print("Pas de connexion Wi-Fi !")    
        
    print("Envoie d'e-mail")
    smtp = umail.SMTP('smtp.gmail.com', 587)  # Remplacer par votre serveur SMTP et port
    smtp.login(wificonfig.smtp_login, wificonfig.smtp_password)  # Info login dans fichier wificonfig.py
    smtp.to(to_address)
    smtp.write("From: mail_automatic@Esp32_micropython\r\n")
    smtp.write("To: {}\r\n".format(to_address))
    smtp.write("Subject: {}\r\n".format(subject))
    smtp.write("\r\n")  # Fin des en-têtes, début du corps du message
    smtp.write(body)
    smtp.send()
    smtp.quit()
    time.sleep(0.1)                
    print(('-' * 11), '\nE-mail info arrosage nécessaire envoyé')
    last_mail = time.ticks_ms()
    return last_mail


def watering(watering_time = WATERING_TIME):
    chrono_watering = time.ticks_ms()

    while True:
        diff_chrono_watering = (time.ticks_diff(time.ticks_ms(), chrono_watering)) / 1000
        
        if diff_chrono_watering < watering_time:
            print("Allumée depuis", diff_chrono_watering, "s")
            relais_pin.value(1)
        else:
            print(f"Arrosage éteint après {watering_time} s")
            relais_pin.value(0)
            break
        
        time.sleep(0.1)
    
        
# ---------------------------------------------------------
# --------------------- START PROGRAMME -------------------
async def infinite_loop():
    global level_humidity
    watchdog_timer.feed()
    
    if manual_watering_button.value() == 0:  # Si bouton pressé lancement de l'arrosage
        print("Bouton pressé, arrosage forcé")
        watering()
        
    while True:        
        diff_between_mail_chrono = time.ticks_diff(time.ticks_ms(), last_mail) / 1000
        level_humidity = get_taux()
            
        if level_humidity <= 10.0:
            led_not_enough_water.value(1)
            watering()
            
            if diff_between_mail_chrono > 24 * 3600: # 1 jour d'écart
                send_mail(mailing_config.mail_send_to, mailing_config.mail_object, mailing_config.mail_body)  # envoie d'un e-mail de demande d'arrosage
            
        else:
            led_not_enough_water.value(0)
            
        # Attendre avant de recommencer la boucle - une heure => 3600 secondes
        await asyncio.sleep(4 * 3600)  # Attente non bloquante relance toutes les 4h


# ---------------------------------------------------------
# ---- Routing Picoweb ------------------------------------
async def start_picoweb():
    global level_humidity
    app = picoweb.WebApp(__name__)

    @app.route("/")
    def index(req, resp):
        yield from picoweb.start_response(resp)
        yield from app.sendfile(resp, '/web/index.html')

    @app.route("/style.css")
    def css(req, resp):
        print("Send style.css")
        yield from picoweb.start_response(resp)
        yield from app.sendfile(resp, '/web/style.css')

    @app.route("/get_data")
    def get_volume(req, resp):
        yield from picoweb.jsonify(resp, {'humidite': level_humidity})

    @app.route("/goutte_eau.jpg")
    def index(req, resp):
        yield from picoweb.start_response(resp)
        try:
            with open("web/goutte_eau.jpg", 'rb') as img_binary:
                img = img_binary.read()
            yield from resp.awrite(img)
            print("Send JPG")
        except Exception:
            print("Image file not found.")
            
    @app.route("/force_watering")
    def force_watering(req, resp):
        print("Arrosage déclenché depuis l'interface web")
        watering()
        yield from picoweb.jsonify(resp, {"status": "ok"})
                
    @app.route("/wifi_status")
    def wifi_status(req, resp):
        import wificonnect
        connected = wificonnect.is_connected()
        yield from picoweb.jsonify(resp, {'connected': connected})

    app.run(debug=True, host=ipaddress, port=80)


async def main():
    # Créez les tâches pour la boucle infinie et le serveur Picoweb
    loop_task = asyncio.create_task(infinite_loop())
    picoweb_task = asyncio.create_task(start_picoweb())
    wifi_task = asyncio.create_task(wifi_monitor(wificonfig.ssid, wificonfig.password))
    
    
    # Attendez que les deux tâches se terminent (elles ne se termineront jamais en réalité)
    await asyncio.gather(loop_task, get_taux_task, watering_task, mailing_task, wifi_task, picoweb_task)


# Démarrez la boucle d'événements asyncio
asyncio.run(main())
