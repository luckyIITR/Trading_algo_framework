from core.Controller import Controller

class BaseOrderManager:
    def __init__(self):
        # Get the broker handle to manage orders
        self.broker_handle = Controller.get_broker_login().get_broker_handle()

    def place_order(self, orderInputParams):
        pass

    def modify_order(self, order, orderModifyParams):
        pass

    def cancel_order(self, order):
        pass