import logging

from core.Controller import Controller

class BaseTicker:
    def __init__(self):
        self.ticker = None
        self.tick_listener = []

    def start_ticker(self):
        pass

    def stop_ticker(self):
        pass

    def register_listeners(self, listener):
    # All registered tick listeners will be notified on new ticks
        self.tick_listener.append(listener)

    def register_symbol(self, symbols):
        pass

    def unregister_symbol(self, symbols):
        pass

    def on_new_ticks(self, ticks):
    # logging.info('New ticks received %s', ticks)
        for tick in ticks:
            for listener in self.tick_listener:
            try:
                listener(tick)
            except Exception as e:
                logging.error('BaseTicker: Exception from listener callback function. Error => %s', str(e))

    def on_connect(self):
        logging.info('Ticker connection successful.')

    def on_disconnect(self, code, reason):
        logging.error('Ticker got disconnected. code = %d, reason = %s', code, reason)

    def on_error(self, code, reason):
        logging.error('Ticker errored out. code = %d, reason = %s', code, reason)

    def on_reconnect(self, attemptsCount):
        logging.warn('Ticker reconnecting.. attemptsCount = %d', attemptsCount)

    def onMaxReconnectsAttempt(self):
        logging.error('Ticker max auto reconnects attempted and giving up..')

    def on_order_update(self, data):
        #logging.info('Ticker: order update %s', data)
        pass
