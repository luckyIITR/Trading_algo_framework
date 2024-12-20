class BrokerAppDetails:
    def __init__(self):
        self.broker_name = None
        self.api_key = None
        self.api_secret = None
    # setter functions
    def set_broker_name(self, broker_name):
        self.broker_name = broker_name
    def set_api_key(self, api_key):
        self.api_key = api_key
    def set_api_secret(self, api_secret):
        self.api_secret = api_secret

    # getter functions
    def get_broker_name(self):
        return self.broker_name
    def get_api_key(self):
        return self.api_key
    def get_api_secret(self):
        return self.api_secret