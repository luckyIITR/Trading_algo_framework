from loginmgmt.BaseLogin import BaseLogin
from fyers_apiv3 import fyersModel
import json
import logging
import pandas as pd

with open("config/fyers.json", "r") as file:
    config = json.load(file)

class FyersLogin(BaseLogin):
    def __init__(self, broker_app_details):
        super().__init__(broker_app_details)

    def login(self):
        self.client_id = self.broker_app_details.api_key
        self.secret_key =  self.broker_app_details.api_secret
        self.redirect_uri = "https://iamlucky.co.in/login/fyers_callback"
        self.grant_type = "authorization_code"
        self.response_type = "code"
        self.state = "sample_state"
        self.auth_code = config['auth_code']
        self.access_token = config['access_token']

        if (not (self.start_session())):
            self.gen_auth_code()
            self.gen_access_token()
            self.save_config()
            self.start_session()

        # set broker handle and access token to the instance
        self.set_access_token(self.access_token)
        self.set_broker_handle(self.fyers)

    def gen_auth_code(self):
        # Create a session model with the provided credentials
        session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_uri,
            response_type=self.response_type
        )
        # Generate the auth code using the session model
        response = session.generate_authcode()
        # Print the auth code received in the response
        print(response)
        self.auth_code = input("Enter auth Code : ")

    def gen_access_token(self):
        # Create a session object to handle the Fyers API authentication and token generation
        session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_uri,
            response_type=self.response_type,
            grant_type=self.grant_type
        )

        # Set the authorization code in the session object
        session.set_token(self.auth_code)

        # Generate the access token using the authorization code
        response = session.generate_token()

        # Print the response, which should contain the access token and other details
        # print(response)
        self.access_token = response['access_token']

    def save_config(self):
        config_data = {
            'auth_code': self.auth_code,
            'access_token': self.access_token
        }
        with open('config/fyers.json', 'w') as jsonfile:
            json.dump(config_data, jsonfile, indent=4)

    def start_session(self):
        self.session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_uri,
            response_type=self.response_type,
            grant_type=self.grant_type
        )
        # Set the authorization code in the session object
        self.session.set_token(self.auth_code)

        self.fyers = fyersModel.FyersModel(client_id=self.client_id, is_async=False, token=self.access_token,
                                           log_path="")
        # Make a request to get the user profile information
        response = self.fyers.get_profile()

        if (response['code'] == 200):
            logging.info(f"Client ID: {response['data']['fy_id']}, Name: {response['data']['name']} Connected!")
        else:
            logging.warning(response['message'])
            return False
        # Print the response received from the Fyers API
        return True

    def get_data(self, symbol, resolution, range_from, range_to):
        df = pd.DataFrame()
        data = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": "1",
            "range_from": range_from,
            "range_to": range_to,
            "cont_flag": "1",
            "oi_flag": "1"
        }
        response = self.fyers.history(data=data)
        # print(response)
        # Pre processing
        df1 = pd.DataFrame(response['candles'])
        df = pd.concat([df, df1], axis=0)
        df.rename(columns={0: 'Datetime', 1: 'Open', 2: 'High', 3: 'Low', 4: 'Close', 5: 'Volume'}, inplace=True)
        df['Datetime'] = pd.to_datetime(df['Datetime'], unit='s')
        df['Datetime'] = df['Datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        return df