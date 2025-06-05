import network
import utime as time


def is_connected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.isconnected()

def connect(ssid, password, name='MicroPython'):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Tentative de connexion...')
        wlan.connect(ssid, password)
        attempts = 0
        while attempts < 10:  # 10 tentatives, espacées d'une seconde
            print('.')
            if wlan.isconnected():
                print('Connecté au Wi-Fi')
                break
            time.sleep(1)
            attempts += 1
        else:
            print('Échec de connexion Wi-Fi après 10 tentatives')
            start_ap()
            return None  # Retourner None si la connexion échoue
    wlan.config(dhcp_hostname=name)
    print("station.config(dhcp_hostname) =", wlan.config('dhcp_hostname'))
    return wlan.ifconfig()[0] if wlan.isconnected() else None  # Retourner l'IP ou None


def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='Hygro_serre', password='12345678', authmode=network.AUTH_WPA_WPA2_PSK)
    print('🔧 Point d\'accès actif : ESP32_Config (mdp: 12345678)')
    print('Adresse IP AP :', ap.ifconfig())
    return ap


def get_ip():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan.ifconfig()[0]  # Retourne l'IP si connecté
    else:
        return '192.168.4.1'  # Retourner None si non connecté
    