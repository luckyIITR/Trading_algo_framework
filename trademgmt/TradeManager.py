from ordermgmt.Order import Order
from ordermgmt.KiteConstants import KiteConstants
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
import logging
from trademgmt.TradeState import TradeState

class TradeManager:
    order_manager = ZerodhaOrderManager()
    @staticmethod
    def execute_trade(trade):
        order = Order(variety=KiteConstants.VARIETY_REGULAR,
                      exchange=trade.exchange,
                      trading_symbol=trade.trading_symbol,
                      transaction_type=trade.direction,
                      quantity=trade.qty,
                      product=trade.product_type,
                      order_type=trade.requested_order_entry_type,
                      price=trade.requested_price,
                      trigger_price=trade.trigger_price)
        try:
            TradeManager.order_manager.place_order(order)
            return order
        except Exception as e:
            logging.error(f"Error in Trade Execution: {e}")

