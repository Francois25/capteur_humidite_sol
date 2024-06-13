# CAPTEUR HUMIDITE SOL CONNECTE
from machine import ADC, Pin, UART, RTC
import wificonfig
import wificonnect
import picoweb
import prog_led
import network
import ulogging
import umail
import utime as time
import uasyncio as asyncio

# --------------------- WIFI ------------------------
#
# enter your wifi ssid and your password in wificonfig file

ipaddress = wificonnect.connectSTA(ssid=wificonfig.ssid, password=wificonfig.password)

# ------------------- SET UP -------------------------
PIN_ANALOG = Pin(32)  # choisir un pin analogique sur l'ESP
HUMIDITE_MINI = 4095
HUMIDITE_MAX = 850
CAPTOR_LED_DEFAUT = Pin(14, Pin.OUT, 0)
NOT_ENOUGH_WATER_LED = Pin(27, Pin.OUT)  # led rouge


# ------------------- PROG MAIN ----------------------
# fonction lire le taux d'humidité
def get_taux(pin=PIN_ANALOG, humidity=0):
    adc = ADC(pin)
    while True:
        try:
            value = adc.read()
            humidity = (1 - (value - HUMIDITE_MAX) / (HUMIDITE_MINI - HUMIDITE_MAX)) * 100
            if (humidity > 100) or (humidity < 0):
                print("Le taux d'humidité est anormal, contrôl du capteur nécessaire")
                CAPTOR_LED_DEFAUT.value(1)
            else:
                CAPTOR_LED_DEFAUT.value(0)
                prog_led.led_init()
                print(f"Le taux d'humidité est de {humidity:.0f}%")
        except:
            print("Echec de la lecture du capteur.")
            prog_led.led_blink()

        return float(round(humidity, 2))


def send_mail(to_address, subject, body):
    smtp = umail.SMTP('smtp.gmail.com', 587)  # Remplacer par votre serveur SMTP et port
    smtp.login(wificonfig.smtp_login, wificonfig.smtp_password)  # Remplacer par votre adresse email et mot de passe

    smtp.to(to_address)
    smtp.write("From: mail_automatic@Esp32_micropython\r\n")
    smtp.write("To: {}\r\n".format(to_address))
    smtp.write("Subject: {}\r\n".format(subject))
    smtp.write("\r\n")  # Fin des en-têtes, début du corps du message
    smtp.write(body)

    smtp.send()
    smtp.quit()


# ---------------------------------------------------------
# --------------------- START PROGRAMME -------------------
async def infinite_loop():
    global level_humidity
    while True:
        level_humidity = get_taux()
        if level_humidity <= 10.0:
            NOT_ENOUGH_WATER_LED.value(1)
            send_mail(wificonfig.mail_send_to, wificonfig.mail_object, wificonfig.mail_body)  # envoie d'un message demande d'arrosage
        else:
            NOT_ENOUGH_WATER_LED.value(0)

        # Attendre une heure (3600 secondes) avant de recommencer la boucle
        await asyncio.sleep(43200)  # Attente non bloquante 12h


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
    loop_task = asyncio.create_task(infinite_loop())
    picoweb_task = asyncio.create_task(start_picoweb())

    # Attendez que les deux tâches se terminent (elles ne se termineront jamais en réalité)
    await asyncio.gather(loop_task, picoweb_task)


# Démarrez la boucle d'événements asyncio
asyncio.run(main())
