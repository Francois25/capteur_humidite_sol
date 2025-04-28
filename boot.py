# This file is executed on every boot (including wake-boot from deepsleep)
import esp
import gc
import uasyncio as asyncio

esp.osdebug(None)
gc.enable()
gc.collect()

# start program
asyncio.run(main.start())