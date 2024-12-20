import logging
from Test import Test

class Algo:
    @staticmethod
    def start_algo():
        logging.info("Starting Algo...")

        logging.info("Testing Login Functionality")
        Test.broker_login_api()

        Test.test_orders()