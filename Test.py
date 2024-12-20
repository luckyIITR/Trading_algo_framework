import time

from core.Controller import Controller
import logging
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
from ordermgmt.Order import Order
from ordermgmt.KiteConstants import KiteConstants
from ordermgmt.OrderModifyParams import OrderModifyParams

class Test:
    @staticmethod
    def broker_login_api():
        logging.info("Testing Broker Login API")
        Controller.handle_broker_login()

    @staticmethod
    def test_orders():
        logging.info("Testing Orders API")
        order_manager = ZerodhaOrderManager()

        # create order and place it
        # logging.info("Placing Market Order")
        # test_order = Order(variety=KiteConstants.VARIETY_REGULAR, exchange=KiteConstants.EXCHANGE_NSE,
        #                   trading_symbol="ITC", transaction_type=KiteConstants.TRANSACTION_TYPE_BUY, quantity=1,
        #                   product=KiteConstants.PRODUCT_MIS, order_type=KiteConstants.ORDER_TYPE_MARKET)
        # # place market order
        # order_manager.place_order(test_order)

        # time.sleep(5)
        # # Place limit order
        # logging.info("Placing Limit Order")
        # test_order_limit = Order(variety=KiteConstants.VARIETY_REGULAR, exchange=KiteConstants.EXCHANGE_NSE,
        #                    trading_symbol="ITC", transaction_type=KiteConstants.TRANSACTION_TYPE_BUY, quantity=1,
        #                    product=KiteConstants.PRODUCT_MIS, order_type=KiteConstants.ORDER_TYPE_LIMIT, price=460)
        # order_manager.place_order(test_order_limit)
        # time.sleep(10)
        # # Modify limit order
        # logging.info("Modifying Limit Order")
        # new_params = OrderModifyParams(new_price=459, new_qty=2)
        # order_manager.modify_order(test_order_limit, new_params)

        # time.sleep(10)
        # Place SL order
        logging.info("Placing SL Order")
        test_order_sl = Order(variety=KiteConstants.VARIETY_REGULAR, exchange=KiteConstants.EXCHANGE_NSE,
                                 trading_symbol="ITC", transaction_type=KiteConstants.TRANSACTION_TYPE_SELL, quantity=1,
                                 product=KiteConstants.PRODUCT_MIS, order_type=KiteConstants.ORDER_TYPE_SLM,
                                 trigger_price=450)
        order_manager.place_order(test_order_sl)
        time.sleep(10)

        # Place Target Order
        logging.info("Placing Target Order")
        test_order_target = Order(variety=KiteConstants.VARIETY_REGULAR, exchange=KiteConstants.EXCHANGE_NSE,
                              trading_symbol="ITC", transaction_type=KiteConstants.TRANSACTION_TYPE_SELL, quantity=1,
                              product=KiteConstants.PRODUCT_MIS, order_type=KiteConstants.ORDER_TYPE_LIMIT,
                              price=470)
        order_manager.place_order(test_order_target)
        time.sleep(10)

        # Cancel Both SL and target orders
        logging.info("Canceling Both SL and Target Order")
        order_manager.cancel_order(test_order_target)
        order_manager.cancel_order(test_order_sl)

        logging.info("Algo done executing all orders. Check ur orders and positions in broker terminal.")