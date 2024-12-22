import logging
from Test import Test
from instruments.Instruments import Instruments
from strategies.ShortStraddle import ShortStraddle
from strategies.params.NiftyShortStraddleParams import NiftyShortStraddleParams

class Algo:
    @staticmethod
    def start_algo():
        logging.info("Starting Algo...")

        # login Functionality
        Test.broker_login_api()

        # Fetch Instruments and create map
        Instruments.fetch_instruments_from_server()
        Test.test_instrument_mapping()

        # Ticker testing
        # Test.test_ticker()

        # order testing
        # Test.test_orders()

        straddle_params = NiftyShortStraddleParams()
        straddle_nifty = ShortStraddle(straddle_params)
        straddle_nifty.process()

        # Test Historical data API working
        # Test.test_historical_data()