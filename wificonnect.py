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
  
#
# def connectAP(name, password=''):
#     global ap
#     print('connecting the Access Point...')
#     ap = network.WLAN(network.AP_IF)
#     ap.active(True)
#     ap.config(ssid=name, password=password)
#     ap.config(max_clients=3)
#     while ap.active() == False:
#         pass
#     print('Acces Point config:', ap.ifconfig())
#     return ap.ifconfig()[0]