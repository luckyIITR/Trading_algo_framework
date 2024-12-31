import logging
from Test import Test
from instruments.Instruments import Instruments
from strategies.ShortStraddle import ShortStraddle
from strategies.params.NiftyShortStraddleParams import NiftyShortStraddleParams
import datetime
import time
from utils.Utils import Utils

# from test_ticker import TickerTest
# import threading
LOG_WIDTH = 80
def log_heading(msg):
    logging.info("\n" +
                 "###########################################".center(LOG_WIDTH) + "\n" +
                 f"{msg}".center(LOG_WIDTH) + "\n" +
                 "###########################################".center(LOG_WIDTH) + "\n"
                 )

class Algo:
    @staticmethod
    def start_algo():
        logging.info("Starting Algo...")

        # login Functionality
        # Test.broker_login_api()
        Algo.wait_till_premarket()
        # Fetch Instruments and create map
        Instruments.fetch_instruments_from_server()
        Test.test_instrument_mapping()

        # Test.test_symbol()

        # log_heading("Ticker Testing")

        # Ticker testing
        # Test.test_ticker()
        # obj1 = TickerTest("This is one object of ticker")
        # obj1.test_ticker()
        # obj2 = TickerTest("This is Second object of ticker")
        #
        # th1 = threading.Thread(target=obj1.test_ticker)
        # th2 = threading.Thread(target=obj2.test_ticker)
        # th1.start()
        # th2.start()
        # th1.join()
        # th2.join()

        # order testing
        # Test.test_orders()


        straddle_params = NiftyShortStraddleParams()
        straddle_nifty = ShortStraddle(straddle_params)
        straddle_nifty.process()

        # Test Historical data API working
        # Test.test_historical_data()

    @staticmethod
    def wait_till_premarket():
        pre_market_datetime = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(10, 59))
        if datetime.datetime.now() < pre_market_datetime:
            logging.info("Waiting for premarket...")
            wait_time = Utils.get_epoch(pre_market_datetime) - Utils.get_epoch(datetime.datetime.now())
            logging.info(f"Waiting for {wait_time} seconds to finish pre-market...")
            time.sleep(wait_time + 10)
