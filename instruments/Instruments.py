from core.Controller import Controller
import logging

class Instruments:
    symbol_to_token_map = {}
    token_to_symbol_map = {}

    @staticmethod
    def fetch_instruments_from_server():
        try:
            broker_handle = Controller.get_broker_login().get_broker_handle()
            logging.info('Going to fetch instruments from server...')
            instruments_list = broker_handle.instruments('NSE')
            instruments_list_fno = broker_handle.instruments('NFO')
            # Add FnO instrument list to the main list
            instruments_list.extend(instruments_list_fno)
            logging.info('Fetched %d instruments from server.', len(instruments_list))
            Instruments.create_maps(instruments_list)
        except Exception as e:
            logging.exception("Exception while fetching instruments from server")

    @staticmethod
    def create_maps(instruments_list):
        # Creating the map
        Instruments.symbol_to_token_map = {item['tradingsymbol']: item['instrument_token'] for item in instruments_list}
        Instruments.token_to_symbol_map = {item['instrument_token']: item['tradingsymbol'] for item in instruments_list}

    @staticmethod
    def get_symbol_to_token(tradingsymbol):
        return Instruments.symbol_to_token_map.get(tradingsymbol)

    @staticmethod
    def get_token_to_symbol(instrument_token):
        return Instruments.token_to_symbol_map.get(instrument_token)
