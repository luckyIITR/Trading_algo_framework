import logging
from Test import Test
from instruments.Instruments import Instruments
from strategies.ShortStraddle import ShortStraddle
import datetime
import time
from utils.Utils import Utils
# from test_ticker import TickerTest
# import threading
from core.Controller import Controller
from strategies.params.NiftyShortStraddleParams import NiftyShortStraddleParams
from utils.notification import send_notification

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
        log_heading("Starting Algo...")
        send_notification("Starting Algo")
        # login Functionality
        # # Test.broker_login_api()
        Algo.wait_for_start_time()
        
        Controller.handle_broker_login()
        # # Fetch Instruments and create map
        Instruments.fetch_instruments_from_server()
        Test.test_instrument_mapping()
        
        # Test.test_symbol()

        # log_heading("Ticker Testing")

        # Ticker testing
        # Test.test_ticker()
        # obj1 = TickerTest("This is one object of ticker")
        # obj1.test_ticker()
        # obj2 = TickerTest("This is Second object of ticker")
        
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
    def wait_for_start_time():
        start_datetime = datetime.datetime.combine(datetime.datetime.now().date(), NiftyShortStraddleParams.straddle_start_times[datetime.datetime.now().strftime("%A")])
        send_notification(f"Start Time: {start_datetime}")
        if datetime.datetime.now() < start_datetime:
            wait_time = Utils.get_epoch(start_datetime) - Utils.get_epoch(datetime.datetime.now())
            if wait_time > 15*60:
                wait_time -= int(9*60)
                logging.info(f"Waiting for {wait_time} seconds to reach starttime.")
                time.sleep(wait_time)
