from config.config import get_fyers_broker_app_config, get_kite_broker_app_config
from loginmgmt.ZerodhaLogin import ZerodhaLogin
from loginmgmt.FyersLogin import FyersLogin
from models.BrokerAppDetails import BrokerAppDetails
import logging

class Controller:
    broker_login = None
    fyers_login = None
    main_broker_name = None

    @staticmethod
    def handle_broker_login():
        logging.info("handle_broker_login function called")
        # create instance of BrokerAppDetails
        kite_app_details = BrokerAppDetails()
        fyers_app_details = BrokerAppDetails()
        # read from config file and set all details to above instance
        kite_app_config = get_kite_broker_app_config()
        fyers_app_config = get_fyers_broker_app_config()

        kite_app_details.set_broker_name(kite_app_config['broker_name'])
        kite_app_details.set_api_key(kite_app_config['api_key'])
        kite_app_details.set_api_secret(kite_app_config['api_secret'])

        fyers_app_details.set_broker_name(fyers_app_config['broker_name'])
        fyers_app_details.set_api_key(fyers_app_config['api_key'])
        fyers_app_details.set_api_secret(fyers_app_config['api_secret'])

        logging.info(f'loaded broker data of: {kite_app_details.get_broker_name()}')
        logging.info(f'loaded broker data of: {fyers_app_details.get_broker_name()}')
        Controller.main_broker_name = kite_app_details.get_broker_name()

        if Controller.main_broker_name == 'Zerodha':
            logging.info("Zerodha Login is being used")
            Controller.broker_login = ZerodhaLogin(kite_app_details)
        # can implement other broker in future

        # Temprory fyers broker handle to get histroical data
        Controller.fyers_login = FyersLogin(fyers_app_details)

        # Proceed to login by assigned broker login
        Controller.broker_login.login()
        Controller.fyers_login.login()

    @staticmethod
    def get_broker_name():
        return Controller.broker_name

    @staticmethod
    def get_broker_login():
        return Controller.broker_login

    @staticmethod
    def get_fyers_login():
        return Controller.fyers_login
