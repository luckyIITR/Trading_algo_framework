import logging
import time
from core.Controller import Controller
from strategies.BaseStrategy import BaseStrategy
import datetime
from models.Direction import Direction
from trademgmt.Trade import Trade
from utils.Utils import Utils
from ordermgmt.KiteConstants import KiteConstants
from models.ProductType import ProductType

class ShortStraddle(BaseStrategy):
    def __init__(self, params):
        super().__init__("Short Straddle")
        self.lot_size = None
        self.start_time = params.start_time
        self.square_off_time = params.square_off_time
        self.isFnO = True
        self.atr_window = params.atr_window
        self.instrument = params.instrument
        self.spot_symbol = params.spot_symbol
        # self.today_date = datetime.datetime.now().date()
        # self.day = datetime.datetime.now().strftime("%A")
        self.today_date = datetime.date(2024, 12, 20)
        self.day = self.today_date.strftime("%A")
        self.expiry_rule = params.expiry_rules[self.day]
        self.sl_atr_rule = params.sl_atr_rule[self.day]
        self.rr = params.rr
        self.pre_market_datetime = datetime.datetime.combine(self.today_date, params.pre_market_time)
        self.broker_handler = Controller.get_broker_login().get_broker_handle()
        self.options_gap = params.options_gap
        self.expiry_day = params.expiry_day

    def process(self):
        logging.info(f"Short Straddle in {self.instrument} starting...")

        if datetime.datetime.now() < self.pre_market_datetime:
            wait_time = Utils.get_epoch(self.pre_market_datetime) - Utils.get_epoch(datetime.now())
            logging.info(f"Waiting for {wait_time} seconds to finish pre-market...")
            time.sleep(wait_time+10)

        ce_option_symbol, pe_option_symbol = self.get_atm_options_symbols()
        # calculate lot_size
        self.lot_size = self.get_lot_size("NFO", ce_option_symbol)
        logging.info(f"Lot Size: {self.lot_size}")

        self.generate_trade(ce_option_symbol)
        self.generate_trade(pe_option_symbol)

    def generate_trade(self, option_symbol):
        trade = Trade(option_symbol)
        trade.exchange = "NFO"
        trade.strategy = "Short Straddle"
        trade.direction = Direction.SELL
        trade.product_type = ProductType.MIS
        trade.is_options = True  # Options trade
        trade.requested_order_entry_type = KiteConstants.ORDER_TYPE_MARKET
        trade.qty = self.lot_size * self.get_num_lots()
        

    def get_num_lots(self):
        return 1

    def get_lot_size(self, exchange, ce_option_symbol):
        data = self.broker_handler.instruments(exchange)
        for instr in data:
            if instr['tradingsymbol'] == ce_option_symbol[4:]:
                return instr['lot_size']
        return None

    def get_atm_options_symbols(self):
        # Now fetch Nifty Opening price, calculate strike price and create trade
        open_price = self.broker_handler.ohlc(self.spot_symbol)[self.spot_symbol]['last_price']
        # get strike price and expiry_date
        atm_strike_price = Utils.nearest_strike_price(open_price, self.options_gap)
        expiry_date = Utils.get_weekly_expiry(self.today_date, self.expiry_day)
        # form symbols for both ce and pe
        ce_option_symbol = Utils.create_options_symbol("NFO", self.instrument, atm_strike_price, "CE", self.today_date,
                                                       expiry_date, self.expiry_day)
        pe_option_symbol = Utils.create_options_symbol("NFO", self.instrument, atm_strike_price, "PE", self.today_date,
                                                       expiry_date, self.expiry_day)

        logging.info(
            f"{self.instrument} Open Price: {open_price}, ATM Strike Price: {atm_strike_price}, expiry date: {expiry_date}")
        logging.info(f"CE Option Symbol: {ce_option_symbol}, PE Option Symbol: {pe_option_symbol}")
        logging.info("Checking options symbol validity...")
        # get quotes just to check if options symbols are valid or not
        logging.info(self.broker_handler.ohlc(ce_option_symbol))
        logging.info(self.broker_handler.ohlc(pe_option_symbol))
        return ce_option_symbol, pe_option_symbol