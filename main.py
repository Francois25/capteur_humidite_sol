# CAPTEUR HUMIDITE SOL CONNECTE
from machine import ADC, Pin, UART, RTC, lightsleep, WDT

import mailing_config
import wificonfig
import wificonnect
import capteur_temp_humi
import picoweb
import umail
import utime as time
import uasyncio as asyncio
import random # for test only


# ------------------- SET UP -------------------------
# Pin used on ESP 32
RESTART_LOOP = 10 #1 * 3600 
DEFAULT_CAPTOR_LED = Pin(14, Pin.OUT, 0)
NOT_ENOUGH_WATER_LED = Pin(2, Pin.OUT, 0)  # ESP32 motherboard LED
SENSOR_HUMIDITY_PIN = Pin(32, Pin.IN)  # analogic PIN on ESP
RELAIS_PIN = Pin(15, Pin.OUT, 0) # analogic PIN on ESP
MANUAL_WATERING_BUTTON = Pin(4, Pin.IN, Pin.PULL_UP)  # Bouton branché entre GPIO12 et GND
MANUAL_WATERING_BUTTON_OFF = Pin(17, Pin.IN, Pin.PULL_UP)  # Bouton branché entre GPIO12 et GND
DHC22_PIN = Pin(16, Pin.IN) # analogic PIN on ESP

# Generic Variables
HUMIDITE_MIN = 2640
HUMIDITE_MAX = 1230
WATERING_TIME = 60 * 1  # watering time : 60 * number of minutes
EMAIL_INTERVAL = 43200  # 12h en secondes

# Initial variables
ipaddress = " "
watering_interrupted = False
is_watering = False


# --------------------- WIFI ------------------------
#connection Wifi si perte et clignotement de la led de board tant qu'il n'y a pas de wifi
async def wifi_monitor(ssid, password):
    """Wifi connection
    
    Connexion and reconnexion if there is no WiFi, during this time 

    Args:
        ssid (str): ssid of the user wifi passerel
        password (str): password of the user wifi passerel
    """
    while True:
        if not wificonnect.is_connected():
            print("Pas de connexion WiFi")
            for _ in range(5):
                NOT_ENOUGH_WATER_LED.value(1)
                await asyncio.sleep(0.5)
                NOT_ENOUGH_WATER_LED.value(0)
                await asyncio.sleep(0.5)
            ipaddress = wificonnect.connect(ssid=wificonfig.ssid, password=wificonfig.password)
            await asyncio.sleep(0.1)
            return ipaddress
            
        else:
            await asyncio.sleep(60)  # Vérifie la connexion toutes les 60 secondes      
    
    
async def wait_wifi_connection():
    """Waiting wifi connection

    Waiting wifi connection statu ok before continue

    Returns:
        str: Ip adress of the server
    """
    print(" * Connexion au Wi-Fi en cours...")
    while not wificonnect.connect(ssid=wificonfig.ssid, password=wificonfig.password):
        await asyncio.sleep(1)
    print(" * Connexion Wi-Fi établie :", wificonnect.get_ip())
    return wificonnect.get_ip()


# ------------------- MAIN ----------------------
async def temperature_humidity_measurement(pin):
    try:
        temperature_humidity=capteur_temp_humi.sensor(pin)
        temp = round(temperature_humidity[0], 2)
        print(' ' + 30*'-', f"\n * Temperature de l'air : {temp}°")
        hum = round(temperature_humidity[1], 2)
        print(f" * Taux d'humidité dans l'air : {hum}%\n", 30*'-')
    except Exception as e:
        temp = -1
        hum = -1
        print("*** Problème de capteur DHT22 ***", e)

    await asyncio.sleep(0.1)
    return temp, hum

       
async def get_taux(pin=SENSOR_HUMIDITY_PIN, humidity=0):
    """Get humidity value

    Get the humidity value of the place by using the sensor

    Args:
        pin (int, optional): Pin of ESP32 to use for the sensor. Defaults to SENSOR_HUMIDITY_PIN variable.
        humidity (int, optional): value of humidity. Defaults variable to 0.

    Returns:
        float: value of humidity
    """
    adc = ADC(pin)
    adc.atten(ADC.ATTN_11DB)  # Adapt to sensor range
    adc.width(ADC.WIDTH_12BIT)  # 0 to 4095
    try:
        value = adc.read()
        print(' ' + 30*'-', f"\n * Valeur reçue : {value}")

        # -------------- ACTIVE 2 NEXTS LIGNES FOR TEST ------------------
        #humidity = 14
        #humidity = random.choice([7, 12, 20])

        # -------------- DEACTIVE NEXT LIGNE FOR TEST ------------------
        humidity = (1 - (value - HUMIDITE_MAX) / (HUMIDITE_MIN - HUMIDITE_MAX)) * 100

        if (humidity > 100) or (humidity < 0):
            print(' ' + 30*'-', "\n*** Le taux d'hygrométrie est anormal, contrôle du capteur nécessaire ***\n", 30*'-')
            DEFAULT_CAPTOR_LED.value(1)

        else:
            DEFAULT_CAPTOR_LED.value(0)
            print(f" * Le taux d'hygrométrie est de {humidity:.0f}%\n", 30*'-')
            
    except Exception as e:
        print(' ' + 30*'-', "*** Echec de la lecture du capteur ***\n", 30*"-", e)
    
    await asyncio.sleep(0.1)
    return float(round(humidity, 2))
    

async def send_mail(to_address, subject, body):
    """send mail for user

    Send a mail for imform user that he need to add water

    Args:
        to_address (_text_): user mail adress to use for send the mail
        subject (_text_): subject of the mail
        body (_text_): text of the body of the mail

    Returns:
        int: value of the last moment id that a mail whas send before
    """
    
    if not wificonnect.is_connected():
        print("Pas de connexion Wi-Fi !")
        return
    
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
    await asyncio.sleep(0.1)                
    print(('-' * 11), '\nE-mail info arrosage nécessaire envoyé')



async def watering():
    """Watering

    Switch on watering device since Web app or manualy

    Args:
        watering_time (int, optional): Time of watering before switch off. Defaults to WATERING_TIME.
    """
    global watering_interrupted
    global is_watering
    watering_interrupted = False
    is_watering = True
    print("Arrosage en cours")
    chrono_watering = time.ticks_ms()
    while True:
        if watering_interrupted:
            print("Arrosage interrompu manuellement")
            break
        
        elif MANUAL_WATERING_BUTTON_OFF.value() == 0:
            print(' ' + 30*'-', "\n * Bouton pressé, arrosage stoppé\n", 30*'-')
            await no_watering()

        RELAIS_PIN.value(1)
        elapsed_time = (time.ticks_diff(time.ticks_ms(), chrono_watering)) / 1000
        if elapsed_time >= WATERING_TIME:
            print("Arrosage terminé")
            break

        await asyncio.sleep(0.1)
        
    RELAIS_PIN.value(0)
    NOT_ENOUGH_WATER_LED.value(0)
    is_watering = False



async def no_watering():
    global watering_interrupted
    global is_watering
    watering_interrupted = True
    is_watering = False
    RELAIS_PIN.value(0)
    NOT_ENOUGH_WATER_LED.value(0)
    print("Arrosage stoppé")
    await asyncio.sleep(0.1)
    

# --------------------- ROUTING PROGRAMME -------------------
async def infinite_loop():
    global hum
    global temp
    last_email_time = 0  # initialisé à 0 au démarrage    
       
    while True:
        temp, hum = await temperature_humidity_measurement(DHC22_PIN)
        global level_humidity
        level_humidity = await get_taux()
            
        if level_humidity <= 10:
            NOT_ENOUGH_WATER_LED.value(1)
            current_time = time.time()
                        
            if current_time - last_email_time >= EMAIL_INTERVAL:
                print(">> Niveau d'eau faible. Envoi de l'e-mail...")
                try:
                    await send_mail(mailing_config.mail_send_to, mailing_config.mail_object, mailing_config.mail_body)  # send e-mail watering needeed
                    last_email_time = current_time
                except Exception as e:
                    print("Erreur lors de l'envoi de l'e-mail :", e)
                
            await watering()
            
        else:
            NOT_ENOUGH_WATER_LED.value(0)
            
        for _ in range(RESTART_LOOP):  # RESTART_LOOP = 3600 → 3600 * 1s = 1h
            if MANUAL_WATERING_BUTTON.value() == 0:
                print(' ' + 30*'-', "\n * Bouton pressé, arrosage forcé\n", 30*'-')
                await watering()
                
            elif MANUAL_WATERING_BUTTON_OFF.value() == 0:
                print(' ' + 30*'-', "\n * Bouton pressé, arrosage stoppé\n", 30*'-')
                await no_watering()
                
            await asyncio.sleep(1)
        

# ---------------------------------------------------------
# ---- ROUTING PICOWEB ------------------------------------
async def start_picoweb():
    global level_humidity
    global temp
    global hum

    app = picoweb.WebApp(__name__)

    @app.route("/")
    def index(req, resp):
        yield from picoweb.start_response(resp, content_type="text/html")
        try:
            with open("/web/index.html", "r") as f:
                while True:
                    data = f.read(512)
                    if not data:
                        break
                    yield from resp.awrite(data)
            print("Page index.html servie")
        except Exception as e:
            print("Erreur chargement index.html :", e)

    @app.route("/style.css")
    def css(req, resp):
        yield from picoweb.start_response(resp, content_type="text/css")
        try:
            with open("/web/style.css", "r") as f:
                while True:
                    data = f.read(512)
                    if not data:
                        break
                    yield from resp.awrite(data)
            print("Feuille CSS servie")
        except Exception as e:
            print("Erreur chargement style.css :", e)

    @app.route("/serre.webp")
    def background(req, resp):
        yield from picoweb.start_response(resp, content_type="image/webp")
        try:
            with open("/web/serre.webp", "rb") as f:
                while True:
                    data = f.read(512)
                    if not data:
                        break
                    yield from resp.awrite(data)
            print("Arrière-plan webp servi")
        except Exception as e:
            print('Erreur chargement serre_hq_redim.webp:', e)

    @app.route("/goutte_ico.png")
    def icon(req, resp):
        yield from picoweb.start_response(resp, content_type="image/png")
        try:
            with open("/web/goutte_ico.png", "rb") as f:
                while True:
                    data = f.read(512)
                    if not data:
                        break
                    yield from resp.awrite(data)
            print("Icône servie")
        except Exception as e:
            print('Erreur chargement goutte_ico.png:', e)

    @app.route("/get_data")
    def get_data(req, resp):
        yield from picoweb.jsonify(resp, {
            'hygrometrie': level_humidity,
            'temperature': temp,
            'humidite': hum
        })

    @app.route("/force_watering")
    async def force_watering(req, resp):
        print("Arrosage déclenché depuis l'interface web")
        await watering()
        yield from picoweb.jsonify(resp, {"status": "ok"})

    @app.route("/stop_watering")
    async def stop_watering(req, resp):
        print("Arrosage stoppé depuis l'interface web")
        await no_watering()
        yield from picoweb.jsonify(resp, {"status": "ok"})

    @app.route("/watering_status")
    def watering_status(req, resp):
        yield from picoweb.jsonify(resp, {'watering': is_watering})

    @app.route("/wifi_status")
    def wifi_status(req, resp):
        import wificonnect
        connected = wificonnect.is_connected()
        yield from picoweb.jsonify(resp, {'connected': connected})

    print("Serveur PicoWeb démarré")
    app.run(debug=True, host=ipaddress, port=80)


async def main():
    global ipaddress

    ipaddress = await wait_wifi_connection()

    try:
        loop_task = asyncio.create_task(infinite_loop())
        wifi_task = asyncio.create_task(wifi_monitor(wificonfig.ssid, wificonfig.password))
        picoweb_task = asyncio.create_task(start_picoweb())

        await asyncio.gather(loop_task, wifi_task, picoweb_task)

    except Exception as e:
        print("Erreur dans les tâches principales :", e)


async def start():
    await main()

    
asyncio.run(start())