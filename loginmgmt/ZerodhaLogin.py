from loginmgmt.BaseLogin import BaseLogin
from kiteconnect import KiteConnect
from dotenv import load_dotenv
import json
import logging

with open("config/zerodha.json", "r") as file:
    config = json.load(file)

class ZerodhaLogin(BaseLogin):
    def __init__(self, broker_app_details):
        super().__init__(broker_app_details)
        self.kite = None

    def login(self):
        api_key = self.broker_app_details.api_key
        api_secret = self.broker_app_details.api_secret
        access_token = config['access_token']
        refresh_token = config['refresh_token']

        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

        # try to see if token is still valid
        try:
            profile_data = self.kite.profile()
            logging.info(f"User ID: {profile_data['user_id']}, {profile_data['user_name']} Connected!")
        except Exception as e:
            logging.error(f"{e}, Getting new token...")
            self.get_new_token()

        # set broker handle and access token to the instance
        self.set_refresh_token(refresh_token)
        self.set_access_token(access_token)
        self.set_broker_handle(self.kite)

    def get_new_token(self):
        api_secret = self.broker_app_details.api_secret
        url = self.kite.login_url()
        print(url)
        request_token = input("Enter Request token: ")
        new_session_data = self.kite.generate_session(request_token=request_token, api_secret=api_secret)
        logging.info(f"User ID: {new_session_data['user_id']}, {new_session_data['user_name']} Connected!")
        access_token = new_session_data["access_token"]
        refresh_token = new_session_data["refresh_token"]
        self.kite.set_access_token(access_token)
        config_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
        }
        with open('config/zerodha.json', 'w') as jsonfile:
            json.dump(config_data, jsonfile, indent=4)