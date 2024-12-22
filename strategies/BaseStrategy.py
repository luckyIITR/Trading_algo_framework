import logging
from models.ProductType import ProductType

class BaseStrategy:
    def __init__(self, name):
        self.name = name
        self.enabled= True # Strategy will be run only when it is enabled
        self.product_type = ProductType.MIS # MIS/NRML/CNC etc
        self.symbols = [] # List of symbols to be traded in this strategy
        self.start_time = None # strategy datetime
        self.stop_time = None # This is not square off timestamp. This is the timestamp after which no new trades will be placed under this strategy but existing trades continue to be active.
        self.square_off_time = None # Square off time
        self.isFnO = False # Does this strategy trade in FnO or not
        self.trades = [] # A strategy can have multiple trades

    def process(self):
        # Implementation is specific to each strategy - To be defined in derived class
        pass