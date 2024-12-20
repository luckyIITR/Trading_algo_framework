from config.config import get_broker_app_config
from loginmgmt.ZerodhaLogin import ZerodhaLogin
from models.BrokerAppDetails import BrokerAppDetails
import logging

class Controller:
    broker_login = None
    broker_name = None

    @staticmethod
    def handle_broker_login():
        logging.info("handle_broker_login function called")
        # create instance of BrokerAppDetails
        broker_app_details = BrokerAppDetails()
        # read from config file and set all details to above instance
        broker_app_config = get_broker_app_config()

        broker_app_details.set_broker_name(broker_app_config['broker_name'])
        broker_app_details.set_api_key(broker_app_config['api_key'])
        broker_app_details.set_api_secret(broker_app_config['api_secret'])

        logging.info(f'loaded broker data of: {broker_app_details.get_broker_name()}')
        Controller.broker_name = broker_app_details.get_broker_name()

        if Controller.broker_name == 'Zerodha':
            logging.info("Zerodha Login is being used")
            Controller.broker_login = ZerodhaLogin(broker_app_details)
        # can implement other broker in future

        # Proceed to login by assigned broker login
        Controller.broker_login.login()

    @staticmethod
    def get_broker_name():
        return Controller.broker_name

    @staticmethod
    def get_broker_login():
        return Controller.broker_login


