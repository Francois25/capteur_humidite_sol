import network


def connect(ssid, password, name='MicroPython'):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Tentative de reconnexion...')
        wlan.connect(ssid, password)
        for _ in range(10):  # 10 tentatives, espacées d'une seconde
            if wlan.isconnected():
                print('Reconnecté au Wi-Fi')
                break
        else:
            print('Échec de reconnexion Wi-Fi')
    wlan.config(dhcp_hostname = name)
    print('network config:', wlan.ifconfig())
    print("station.config(dhcp_hostname) =", wlan.config('dhcp_hostname'))
    return wlan.ifconfig()[0]


def is_connected():
    wlan = network.WLAN(network.STA_IF)
    print(wlan.ifconfig())
    return wlan.isconnected()


def get_ip():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return wlan.ifconfig()[0] if wlan.isconnected() else None