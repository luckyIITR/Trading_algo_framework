
class BaseLogin:
    def __init__(self, broker_app_details):
        self.broker_app_details = broker_app_details
        self.broker_handle = None
        self.access_token = None
        self.refresh_token = None

    def login(self):
        pass

    # Setter function
    def set_broker_handle(self, broker_handle):
        self.broker_handle = broker_handle
    def set_access_token(self, access_token):
        self.access_token = access_token
    def set_refresh_token(self, refresh_token):
        self.refresh_token = refresh_token

    # Getter function
    def get_broker_app_details(self):
        return self.broker_app_details
    def get_broker_handle(self):
        return self.broker_handle
    def get_access_token(self):
        return self.access_token
    def get_refresh_token(self):
        return self.refresh_token