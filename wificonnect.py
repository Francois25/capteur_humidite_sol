import network

def connectSTA(ssid, password, name='MicroPython'):
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)
        if not wlan.isconnected():
            wlan.config(reconnects = 5)
    wlan.config(dhcp_hostname = name)
    print('network config:', wlan.ifconfig())
    print("station.config(dhcp_hostname) =", wlan.config('dhcp_hostname'))
    return wlan.ifconfig()[0]
  
def is_connected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.isconnected()

def reconnect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Tentative de reconnexion...')
        wlan.connect(ssid, password)
        for _ in range(10):  # 10 tentatives, espacées d'une seconde
            if wlan.isconnected():
                print('Reconnecté au Wi-Fi')
                break
            time.sleep(1)
        else:
            print('Échec de reconnexion Wi-Fi')