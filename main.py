# CAPTEUR HUMIDITE SOL CONNECTE
from machine import ADC, Pin, UART, RTC

import mailing_config
import wificonfig
import wificonnect
import picoweb
import prog_led
import network
import ulogging
import umail
import utime as time
import uasyncio as asyncio
import random

# --------------------- WIFI ------------------------
#
# enter your wifi ssid and your password in wificonfig file

ipaddress = wificonnect.connectSTA(ssid=wificonfig.ssid, password=wificonfig.password)

# ------------------- SET UP -------------------------

PIN_ANALOG = Pin(32)  # choisir un pin analogique sur l'ESP
HUMIDITE_MINI = 4095
HUMIDITE_MAX = 1170
CAPTOR_LED_DEFAUT = Pin(14, Pin.OUT, 0)
NOT_ENOUGH_WATER_LED = Pin(2, Pin.OUT)  # board LED
start_chrono = 0


# ------------------- PROG MAIN ----------------------
# fonction lire le taux d'humidité
def get_taux(pin=PIN_ANALOG, humidity=0):
    adc = ADC(pin)
    adc.atten(ADC.ATTN_11DB)  # Adapter en fonction de la plage de tension de votre capteur
    adc.width(ADC.WIDTH_12BIT)  # Plage de 0-4095
    while True:
        try:
            value = adc.read()
            print(('-' * 11), '\n', f"valeur lue: {value}")

            # -------------- ACTIVE 2 NEXTS LIGNES FOR TEST ------------------
            # humidity = 9
            # humidity = random.choice([7, 9, 20])

            # -------------- DEACTIVE NEXT LIGNE FOR TEST ------------------
            humidity = (1 - (value - HUMIDITE_MAX) / (HUMIDITE_MINI - HUMIDITE_MAX)) * 100

            if (humidity > 100) or (humidity < 0):
                print("Le taux d'humidité est anormal, contrôl du capteur nécessaire")
                CAPTOR_LED_DEFAUT.value(1)
            else:
                CAPTOR_LED_DEFAUT.value(0)
                prog_led.led_init()
                print(('-' * 11), '\n', f"Le taux d'humidité est de {humidity:.0f}%")
        except:
            print("Echec de la lecture du capteur.")

        return float(round(humidity, 2))


def send_mail(to_address, subject, body):
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
    print(('-' * 11), '\nENVOIE MAIL')
    start_chrono_mail = time.ticks_ms()
    return start_chrono_mail


# ---------------------------------------------------------
# --------------------- START PROGRAMME -------------------
async def infinite_loop(start_chrono=0):
    global level_humidity
    while True:
        chrono = time.ticks_ms()
        diff_chrono = time.ticks_diff(chrono, start_chrono) / 1000
        print(('-' * 11), '\n', f"différence chrono = {diff_chrono}")
        level_humidity = get_taux()
        if (diff_chrono > 24 * 3600) and (level_humidity <= 10.0):
            start_chrono = send_mail(mailing_config.mail_send_to, mailing_config.mail_object, mailing_config.mail_body)  # envoie d'un message demande d'arrosage
        else:
            NOT_ENOUGH_WATER_LED.value(0)

        if level_humidity <= 10.0:
            NOT_ENOUGH_WATER_LED.value(1)
        else:
            NOT_ENOUGH_WATER_LED.value(0)
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

    app.run(debug=True, host=ipaddress, port=80)


async def main():
    global level_humidity
    # Créez les tâches pour la boucle infinie et le serveur Picoweb
    loop_task = asyncio.create_task(infinite_loop(start_chrono))
    picoweb_task = asyncio.create_task(start_picoweb())

    # Attendez que les deux tâches se terminent (elles ne se termineront jamais en réalité)
    await asyncio.gather(loop_task, picoweb_task)


# Démarrez la boucle d'événements asyncio
asyncio.run(main())
