import logging
from core.Controller import Controller

class BaseTicker:
    def __init__(self):
        self.broker_login = Controller.get_broker_login()
        self.ticker = None
        self.tick_listener = []
        self.order_update_listener = []

    def start_ticker(self):
        pass

    def stop_ticker(self):
        pass

    def register_listeners(self, listener):
    # All registered tick listeners will be notified on new ticks
        self.tick_listener.append(listener)

    def register_order_update_listener(self, listener):
        self.order_update_listener.append(listener)

    def register_symbol(self, symbols):
        pass

    def unregister_symbol(self, symbols):
        pass

    def on_new_ticks(self, ticks):
        # logging.info('New ticks received %s', ticks)
        for listener in self.tick_listener:
            try:
                listener(ticks)
            except Exception as e:
                logging.error('BaseTicker: Exception from listener callback function. Error => %s', str(e))

    def _on_order_update(self, data):
        # logging.info(f'on_order_update : {data}')
        for listener in self.order_update_listener:
            try:
                listener(data)
            except Exception as e:
                logging.error('BaseTicker: Exception from order update listener callback function. Error => %s', str(e))
