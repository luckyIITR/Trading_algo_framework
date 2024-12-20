from ticker.BaseTicker import BaseTicker
from models.BrokerAppDetails import BrokerAppDetails
class ZerodhaTicker(BaseTicker):
    
    def __init__(self):
        super().__init__()
    
    def startTicker(self):
        accessToken = BrokerAppDetails.access_token
        api_key = BrokerAppDetails.api_key
        if accessToken == None:
            logging.error('ZerodhaTicker startTicker: Cannot start ticker as accessToken is empty')
        return
        
        ticker = KiteTicker(api_key, accessToken)
        ticker.on_connect = self.on_connect
        ticker.on_close = self.on_close
        ticker.on_error = self.on_error
        ticker.on_reconnect = self.on_reconnect
        ticker.on_noreconnect = self.on_noreconnect
        ticker.on_ticks = self.on_ticks
        ticker.on_order_update = self.on_order_update

        logging.info('ZerodhaTicker: Going to connect..')
        self.ticker = ticker
        self.ticker.connect(threaded=True)