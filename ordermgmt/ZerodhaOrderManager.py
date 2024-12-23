from ordermgmt.BaseOrderManager import  BaseOrderManager
import logging
from datetime import datetime

class ZerodhaOrderManager(BaseOrderManager):
    def __init__(self):
        super().__init__()

    def place_order(self, order):
        logging.info(f"Going to place order with params: {order}")
        kite = self.broker_handle
        try:
            order_id = kite.place_order(
                variety=kite.VARIETY_REGULAR,
                exchange=order.exchange,
                tradingsymbol=order.trading_symbol,
                transaction_type=order.transaction_type,
                quantity=order.quantity,
                price=order.price,
                trigger_price=order.trigger_price,
                product=order.product,
                order_type=order.order_type)
            logging.info(f'Order placed successfully, order_id = {order_id}')
            order.set_order_id(order_id)
            return order_id
        except Exception as e:
            logging.info(f"Order placement failed: {e}")
            # raise Exception(str(e))

    def modify_order(self, order, order_modify_params):
        logging.info(f"Going to modify order with params: {order_modify_params}")
        kite = self.broker_handle
        try:
            order_id = kite.modify_order(
                variety=kite.VARIETY_REGULAR,
                order_id=order.order_id,
                quantity=order_modify_params.new_qty if order_modify_params.new_qty > 0 else None,
                price=order_modify_params.new_price if order_modify_params.new_price > 0 else None,
                trigger_price=order_modify_params.new_trigger_price if order_modify_params.new_trigger_price > 0 else None,
                order_type=order_modify_params.new_order_type if order_modify_params.new_order_type != None else None
            )
            logging.info(f'Order modified successfully, order_id = {order_id}')
            order.set_last_order_update_timestamp(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as e:
            logging.info(f'Order modify failed: {e}')
            # raise Exception(str(e))

    def cancel_order(self, order):
        logging.info(f'Going to cancel order {order.order_id}')
        kite = self.broker_handle
        try:
            order_id = kite.cancel_order(
                variety=kite.VARIETY_REGULAR,
                order_id=order.order_id)

            logging.info(f'Order cancelled successfully, order_id = {order_id}')
            order.set_last_order_update_timestamp(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return order
        except Exception as e:
            logging.info(f'Order cancel failed: {e}')
            # raise Exception(str(e))