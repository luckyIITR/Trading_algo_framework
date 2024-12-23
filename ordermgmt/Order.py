class Order:
    def __init__(self, variety, exchange, trading_symbol, transaction_type, quantity, product, order_type, price=None, trigger_price=None):
        self.variety=variety
        self.exchange=exchange
        self.trading_symbol=trading_symbol
        self.transaction_type=transaction_type
        self.quantity=quantity
        self.product=product
        self.order_type=order_type
        self.price=price
        self.trigger_price=trigger_price
        self.average_price=None # Average price at which the order is filled
        self.order_id=None
        self.order_status=None
        self.filled_qty = 0 # Filled quantity
        self.pending_qty = 0 # Pending qty
        self.order_place_timestamp = None # Not using now
        self.order_timestamp = None # Broker timestamp
        self.exchange_timestamp = None #Exchange timestamp
        self.last_order_update_timestamp = None # Applicable if you modify the order Ex: Trailing SL
        self.message = None # In case any order rejection or any other error save the response from broker in this field
    
    def set_average_price(self, average_price):
        self.average_price = average_price
    def set_order_id(self, order_id):
        self.order_id = order_id
    def change_order_status(self, order_status):
        self.order_status = order_status
    def set_filled_qty(self, filled_qty):
        self.filled_qty = filled_qty
    def set_pending_qty(self, pending_qty):
        self.pending_qty = pending_qty
    def set_order_timestamp(self, order_timestamp):
        self.order_timestamp = order_timestamp
    def set_exchange_timestamp(self, exchange_timestamp):
        self.exchange_timestamp = exchange_timestamp
    def set_message(self, message):
        self.message = message
    def set_last_order_update_timestamp(self, time):
        self.last_order_update_timestamp = time

    def __str__(self):
        return (
            f"Order(trading_symbol={self.trading_symbol}, "
            f"order_id={self.order_id}, "
            f"transaction_type={self.transaction_type}, "
            f"quantity={self.quantity}, "
            f"product={self.product}, "
            f"order_type={self.order_type}, "
            f"price={self.price}, "
            f"order_place_timestamp={self.order_place_timestamp})"
        )