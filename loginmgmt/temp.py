import logging
from kiteconnect import KiteConnect
from dotenv import load_dotenv
import os
import json
from models import BrokerAppDetails

# logging.basicConfig(level=logging.DEBUG)

# Load .env file
load_dotenv("config/.env")

with open("config/zerodha.json", "r") as file:
    config = json.load(file)


class Login:
    def __init__(self):
        self.api_key = os.getenv("api_key")
        self.api_secret = os.getenv("api_secret")
        self.access_token = config['access_token']
        self.kite = KiteConnect(api_key=self.api_key)
        self.kite.set_access_token(self.access_token)

        # try to see if token is still valid
        try:
            profile_data = self.kite.profile()
            logging.info(f"User ID: {profile_data['user_id']}, {profile_data['user_name']} Connected!")
        except Exception as e:
            logging.error(f"{e}, Getting new token...")
            self.get_new_token()

    def get_new_token(self):
        url = self.kite.login_url()
        print(url)
        request_token = input("Enter Request token: ")
        new_session_data = self.kite.generate_session(request_token=request_token, api_secret=self.api_secret)
        logging.info(f"User ID: {new_session_data['user_id']}, {new_session_data['user_name']} Connected!")
        self.access_token = new_session_data["access_token"]
        self.kite.set_access_token(self.access_token)
        config_data = {
            'access_token': self.access_token
        }
        with open('config/zerodha.json', 'w') as jsonfile:
            json.dump(config_data, jsonfile, indent=4)

    def get_kite(self):
        return self.kite

    def set_broker_details(self):
        BrokerAppDetails.api_key = self.api_key
        BrokerAppDetails.api_secret = self.api_secret
        BrokerAppDetails.access_token = self.access_token
        BrokerAppDetails.broker_handler = self.kite

# if __name__ == '__main__' :
#     Login()