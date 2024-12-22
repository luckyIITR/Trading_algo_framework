import time
from core.Controller import Controller
import logging
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
from ordermgmt.Order import Order
from ordermgmt.KiteConstants import KiteConstants
from ordermgmt.OrderModifyParams import OrderModifyParams
from instruments.Instruments import Instruments
from ticker.ZerodhaTicker import ZerodhaTicker
import datetime

class Test:
    @staticmethod
    def broker_login_api():
        logging.info("Testing Broker Login API")
        Controller.handle_broker_login()

    @staticmethod
    def test_historical_data():
        logging.info("Testing Historical Data")
        fyers_broker_login = Controller.get_fyers_login()
        df = fyers_broker_login.get_data(symbol="NSE:NIFTY50-INDEX", resolution="1D", range_from=datetime.date(2024, 11, 25), range_to=datetime.date(2024, 12, 10))
        print(df)

    @staticmethod
    def test_ticker():
        logging.info("Testing Ticker API")
        ticker = ZerodhaTicker()
        ticker.start_ticker()

        # Register Listener
        ticker.register_listeners(Test.ticker_listener)

        # sleep for 5 seconds and register trading symbols to receive ticks
        time.sleep(5)
        ticker.register_symbol(['SBIN', 'RELIANCE'])

        # wait for 10 seconds and stop ticker service
        time.sleep(10)
        logging.info('Going to stop ticker')
        ticker.stop_ticker()

    @staticmethod
    def ticker_listener(tick):
        logging.info(tick)

    @staticmethod
    def test_instrument_mapping():
        logging.info("Testing Instruments Mapping")
        symbol = "NIFTY 50"
        token = Instruments.get_symbol_to_token(symbol)
        logging.info(f"{symbol} -> {token}")

        symbol_2 = Instruments.get_token_to_symbol(token)
        logging.info(f"{token} -> {symbol_2}")

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

        time.sleep(5)
        # Place limit order
        logging.info("Placing Limit Order")
        test_order_limit = Order(variety=KiteConstants.VARIETY_REGULAR, exchange=KiteConstants.EXCHANGE_NSE,
                           trading_symbol="ITC", transaction_type=KiteConstants.TRANSACTION_TYPE_BUY, quantity=1,
                           product=KiteConstants.PRODUCT_MIS, order_type=KiteConstants.ORDER_TYPE_LIMIT, price=460)
        order_manager.place_order(test_order_limit)
        time.sleep(10)
        # Modify limit order
        logging.info("Modifying Limit Order")
        new_params = OrderModifyParams(new_price=459, new_qty=2)
        order_manager.modify_order(test_order_limit, new_params)

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