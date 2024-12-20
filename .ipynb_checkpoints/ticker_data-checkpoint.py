import logging
from kiteconnect import KiteTicker
import os
from dotenv import load_dotenv
import json
logging.basicConfig(level=logging.DEBUG)

# Load .env file
load_dotenv()

with open("config.json", "r") as file:
    config = json.load(file)
    
api_key = os.getenv("api_key")
access_token = config['access_token']

# Initialise
kws = KiteTicker(api_key, access_token)

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    logging.debug("Ticks: {}".format(ticks))

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([738561])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [738561])

def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    print("Connect is closing......")
    ws.stop()

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
try:
    kws.connect()
except KeyboardInterrupt:
    logging.info("WebSocket connection interrupted by user.")
    kws.stop()