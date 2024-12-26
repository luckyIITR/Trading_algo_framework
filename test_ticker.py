import logging
from ticker.ZerodhaTicker import ZerodhaTicker
import time

class TickerTest:
    def __init__(self, msg):
        self.state = None
        self.msg = msg

    def test_ticker(self):
        logging.info("Testing Ticker API")
        ticker = ZerodhaTicker()
        ticker.start_ticker()

        # Register Listener
        ticker.register_listeners(self.tick_listner)

        # sleep for 5 seconds and register trading symbols to receive ticks
        time.sleep(5)
        ticker.register_symbol(['NIFTY24DEC23750CE'])
        ticker.register_order_update_listener(self.order_update)
        # wait for 10 seconds and stop ticker service
        time.sleep(500)
        logging.info('Going to stop ticker')
        ticker.stop_ticker()
        print(self.state)

    def tick_listner(self, data):
        logging.info(data)
        self.state = self.msg

    def order_update(self, data):
        logging.info(f"Order Update: {data}")
