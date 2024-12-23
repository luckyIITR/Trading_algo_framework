from instruments.Instruments import Instruments
from ticker.BaseTicker import BaseTicker
from models.BrokerAppDetails import BrokerAppDetails
import logging
from kiteconnect import KiteTicker

class ZerodhaTicker(BaseTicker):
    def __init__(self):
        super().__init__()
    
    def start_ticker(self):
        broker_app_details = self.broker_login.get_broker_app_details()
        access_token = self.broker_login.get_access_token()
        if access_token is None:
            logging.error('ZerodhaTicker startTicker: Cannot start ticker as accessToken is empty')
            return

        ticker = KiteTicker(broker_app_details.get_api_key(), access_token)
        ticker.on_connect = self.on_connect
        ticker.on_close = self.on_close
        ticker.on_error = self.on_error
        ticker.on_reconnect = self.on_reconnect
        ticker.on_noreconnect = self.on_noreconnect
        ticker.on_ticks = self.on_ticks
        ticker.on_order_update = self.on_order_update

        logging.info('ZerodhaTicker: Going to connect..')
        self.ticker = ticker
        self.ticker.connect(threaded=True)

    def stop_ticker(self):
        logging.info('ZerodhaTicker: stopping..')
        self.ticker.close(1000, "Manual close")

    def register_symbol(self, symbols):
        tokens = []
        for symbol in symbols:
            token = Instruments.get_symbol_to_token(symbol)
            logging.info('ZerodhaTicker registerSymbol: %s token = %s', symbol, token)
            tokens.append(token)
        logging.info('ZerodhaTicker Subscribing tokens %s', tokens)
        self.ticker.subscribe(tokens)
        self.ticker.set_mode(self.ticker.MODE_LTP, tokens)

    def unregister_symbol(self, symbols):
        tokens = []
        for symbol in symbols:
            token = Instruments.get_symbol_to_token(symbol)
            logging.info('ZerodhaTicker unregisterSymbol: %s token = %s', symbol, token)
            tokens.append(token)
        logging.info('ZerodhaTicker Unregistering tokens %s', tokens)
        self.ticker.unsubscribe(tokens)

    def on_ticks(self, ws, ticks):
        # list containing ticks
        self.on_new_ticks(ticks)

    def on_connect(self, ws, response):
        logging.info('Ticker connection successful.')

    def on_close(self, ws, code, reason):
        logging.error('Ticker got disconnected. code = %d, reason = %s', code, reason)

    def on_error(self, ws, code, reason):
        logging.error('Ticker errored out. code = %d, reason = %s', code, reason)

    def on_reconnect(self, ws, attemptsCount):
        logging.warning('Ticker reconnecting.. attemptsCount = %d', attemptsCount)

    def on_noreconnect(self, ws):
        logging.error('Ticker max auto reconnects attempted and giving up..')

    def on_order_update(self, ws, data):
        self._on_order_update(data)

