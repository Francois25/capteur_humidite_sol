import uasyncio as asyncio
import utime as time
import main
import esp
import gc

esp.osdebug(None)
gc.enable()
gc.collect()

time.sleep(1)
# start program
asyncio.run(main.start())