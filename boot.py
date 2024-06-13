# This file is executed on every boot (including wake-boot from deepsleep)
import esp
import gc

esp.osdebug(None)
gc.enable()
gc.collect()

#import webrepl
#webrepl.start()