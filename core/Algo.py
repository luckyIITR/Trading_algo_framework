import logging
from Test import Test
from instruments.Instruments import Instruments
from strategies.ShortStraddle import ShortStraddle
from strategies.params.NiftyShortStraddleParams import NiftyShortStraddleParams
from test_ticker import TickerTest
import threading
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

        # Fetch Instruments and create map
        Instruments.fetch_instruments_from_server()
        Test.test_instrument_mapping()

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