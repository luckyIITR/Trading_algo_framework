import logging
import time
from datetime import timedelta
from core.Controller import Controller
from strategies.BaseStrategy import BaseStrategy
import datetime
from utils.Utils import Utils
from ordermgmt.KiteConstants import KiteConstants
from ta.volatility import AverageTrueRange
from ticker.ZerodhaTicker import ZerodhaTicker
from ordermgmt.OrderStatus import OrderStatus
from ordermgmt.Order import Order
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
import threading
from strategies.StrategyState.ShortStraddleState import ShortStraddleState

class ShortStraddle(BaseStrategy):
    orders_id_map = {}
    total_points_sold = None
    target_points = None
    target_achieved = False
    strategy_state = None

    def __init__(self, params):
        super().__init__("Short Straddle")

        self.lot_size = None
        self.square_off_time = params.square_off_time
        self.isFnO = True
        self.atr_window = params.atr_window
        self.instrument = params.instrument
        self.spot_symbol = params.spot_symbol
        # self.today_date = datetime.datetime.now().date()
        # self.day = datetime.datetime.now().strftime("%A")
        self.today_date = datetime.date(2024, 12, 20)
        self.day = self.today_date.strftime("%A")

        self.start_datetime = datetime.datetime.combine(self.today_date, params.start_time)
        self.stop_datetime = datetime.datetime.combine(self.today_date, params.stop_time)
        self.expiry_rule = params.expiry_rules[self.day]
        self.sl_atr_rule = params.sl_atr_rule[self.day]
        self.rr = params.rr
        self.pre_market_datetime = datetime.datetime.combine(self.today_date, params.pre_market_time)
        self.broker_handler = Controller.get_broker_login().get_broker_handle()
        self.options_gap = params.options_gap
        self.expiry_day = params.expiry_day
        self.fyers_spot_symbol = params.fyers_spot_symbol
        self.atr_range = self.get_atr_range()

        self.order_manager = ZerodhaOrderManager()

        # Start ticker
        self.ticker = ZerodhaTicker()
        self.ticker.start_ticker()
        # Register listners
        self.ticker.register_order_update_listener(ShortStraddle.order_update_listner)

        self.ce_option_symbol = None
        self.pe_option_symbol = None
        self.ce_entry_order = None
        self.pe_entry_order = None
        self.ce_sl_order = None
        self.pe_sl_order = None
        self.target_order = None

        self.target_points = None
        self.pe_sl_price = None
        self.ce_sl_price = None
        ShortStraddle.strategy_state = ShortStraddleState.STRADDLE_STARTED
        # Create a shared event for signaling
        self.stop_event = threading.Event()
    @staticmethod
    def tick_listner(tick):
        pass

    @staticmethod
    def wait_for_key(order_id, timeout=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if order_id in ShortStraddle.orders_id_map:
                return True
            time.sleep(0.1)  # Check every 0.1 second
        return False

    @staticmethod
    def order_update_listner(data):
        logging.info(f"order update: {data}")
        # Wait for key
        ShortStraddle.wait_for_key(data['order_id'], timeout=5)

        order = ShortStraddle.orders_id_map[data['order_id']]
        order.order_status = data['status']
        order.average_price = data['average_price']
        order.filled_qty = data['filled_quantity']
        order.pending_qty = data['pending_quantity']
        order.order_timestamp = data['order_timestamp']
        order.exchange_timestamp = data['exchange_timestamp']
        order.message = data['status_message']

    def process(self):
        logging.info(f"Short Straddle in {self.instrument} starting...")
        if datetime.datetime.now() < self.pre_market_datetime:
            wait_time = Utils.get_epoch(self.pre_market_datetime) - Utils.get_epoch(datetime.datetime.now())
            logging.info(f"Waiting for {wait_time} seconds to finish pre-market...")
            time.sleep(wait_time+10)

        self.ce_option_symbol, self.pe_option_symbol = self.get_atm_options_symbols_n_laod_lot_size()

        # Entry Order Stage
        self.entry_order_placement_stage()

        # Place SL Order Stage
        self.sl_order_placement_stage()

        # run two parallel functions: Chase_target_phase and waiting_for_sl_to_hit_phase
        logging.info("Starting Parallel Target and SL Phase")
        thread1 = threading.Thread(target=self.chase_target_phase)
        thread2 = threading.Thread(target=self.waiting_for_sl_to_hit_phase)
        thread1.start()
        thread2.start()

        # Check state and proceed
        if (ShortStraddle.strategy_state == ShortStraddleState.CE_SL_HIT) or (ShortStraddle.strategy_state == ShortStraddleState.PE_SL_HIT):
            # Set target for other
            self.set_target_for_other_phase()
            self.wait_for_target_sl_stop_time_phase()

        time.sleep(10)
        self.ticker.stop_ticker()

    def wait_for_target_sl_stop_time_phase(self):
        logging.info("Waiting for Target or SL to hit or Stop time Phase...")
        while (datetime.datetime.now() <= self.stop_datetime) and (self.target_order.order_status != OrderStatus.COMPLETE):
            continue
        if self.target_order.order_status != OrderStatus.COMPLETE:
            logging.info("Stop Time achieved!")
            logging.info("Canceling Target Order")
            self.order_manager.cancel_order(self.target_order)
            order = Order(variety=KiteConstants.VARIETY_REGULAR,
                      exchange=KiteConstants.EXCHANGE_NFO,
                      trading_symbol=self.target_order.trading_symbol,
                      transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
                      quantity=self.lot_size * self.get_num_lots(),
                      product=KiteConstants.PRODUCT_MIS,
                      order_type=KiteConstants.ORDER_TYPE_MARKET
                      )
            logging.info("Squaring off Open Positions")
            ShortStraddle.orders_id_map[self.order_manager.place_order(order)] = order

    def set_target_for_other_phase(self):
        logging.info("Setting target Order for running order phase...")
        if ShortStraddle.strategy_state == ShortStraddleState.CE_SL_HIT:
            self.target_order = Order(variety=KiteConstants.VARIETY_REGULAR,
                                  exchange=KiteConstants.EXCHANGE_NFO,
                                  trading_symbol=self.pe_option_symbol,
                                  transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
                                  quantity=self.lot_size * self.get_num_lots(),
                                  product=KiteConstants.PRODUCT_MIS,
                                  order_type=KiteConstants.ORDER_TYPE_LIMIT,
                                  price= Utils.round_to_exchange_price(self.total_points_sold - self.target_points - self.ce_sl_price)
                                  )
        else :
            self.target_order = Order(variety=KiteConstants.VARIETY_REGULAR,
                                  exchange=KiteConstants.EXCHANGE_NFO,
                                  trading_symbol=self.ce_option_symbol,
                                  transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
                                  quantity=self.lot_size * self.get_num_lots(),
                                  product=KiteConstants.PRODUCT_MIS,
                                  order_type=KiteConstants.ORDER_TYPE_LIMIT,
                                  price = Utils.round_to_exchange_price(self.total_points_sold - self.target_points - self.pe_sl_price)
                                  )
        ShortStraddle.orders_id_map[self.order_manager.place_order(self.target_order)] = self.target_order

    def chase_target_phase(self):
        logging.info("Starting Target Chasing Phase...")
        # Keep your target orders ready.
        pe_target_order = Order(variety=KiteConstants.VARIETY_REGULAR,
                                  exchange=KiteConstants.EXCHANGE_NFO,
                                  trading_symbol=self.pe_option_symbol,
                                  transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
                                  quantity=self.lot_size * self.get_num_lots(),
                                  product=KiteConstants.PRODUCT_MIS,
                                  order_type=KiteConstants.ORDER_TYPE_MARKET
                                  )
        ce_target_order = Order(variety=KiteConstants.VARIETY_REGULAR,
                                exchange=KiteConstants.EXCHANGE_NFO,
                                trading_symbol=self.ce_option_symbol,
                                transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
                                quantity=self.lot_size * self.get_num_lots(),
                                product=KiteConstants.PRODUCT_MIS,
                                order_type=KiteConstants.ORDER_TYPE_MARKET
                                )

        ShortStraddle.target_points = self.rr * self.sl_atr_rule * self.atr_range
        logging.info(f"Chasing Target Points: {ShortStraddle.target_points}")

        # Register callback function
        self.ticker.register_listeners(ShortStraddle.target_check_callback)

        # Register symbols
        self.ticker.register_symbol([self.ce_option_symbol, self.pe_option_symbol])

        # Chase for target until stop event is set
        while not self.stop_event.is_set():
            if ShortStraddle.target_achieved:
                # Fire the orders
                ShortStraddle.orders_id_map[self.order_manager.place_order(ce_target_order)] = ce_target_order
                ShortStraddle.orders_id_map[self.order_manager.place_order(pe_target_order)] = pe_target_order
                logging.info("Target Hit!")

                self.stop_event.set()  # Signal other threads to stop

                # unregister the symbols
                self.ticker.unregister_symbol([self.ce_option_symbol, self.pe_option_symbol])

                # Change state to Target Hit
                ShortStraddle.strategy_state = ShortStraddleState.TARGET_HIT
                return

        logging.info("Since SL is Hit!, Unregistering Symbols")
        # unregister the symbols
        self.ticker.unregister_symbol([self.ce_option_symbol, self.pe_option_symbol])

    @staticmethod
    def target_check_callback(ticks):
        # check it should have length of two
        if len(ticks) < 2:
            return

        current_ltp_sum = 0
        for tick in ticks:
            current_ltp_sum += tick['last_price']

        if (ShortStraddle.total_points_sold - current_ltp_sum) >= ShortStraddle.target_points:
            ShortStraddle.target_achieved = True

    def waiting_for_sl_to_hit_phase(self):
        logging.info("Waiting for Either SL order to hit...")

        while not self.stop_event.is_set():
            if (self.ce_sl_order.order_status == OrderStatus.COMPLETE) or (self.pe_sl_order.order_status == OrderStatus.COMPLETE):
                # if true meaning SL hit
                if self.ce_sl_order.order_status == OrderStatus.COMPLETE:
                    logging.info("CE SL Hit!")
                    ShortStraddle.strategy_state = ShortStraddleState.CE_SL_HIT
                    self.order_manager.cancel_order(self.pe_sl_order)
                else :
                    logging.info("PE SL Hit!")
                    ShortStraddle.strategy_state = ShortStraddleState.PE_SL_HIT
                    self.order_manager.cancel_order(self.ce_sl_order)
                self.stop_event.set()  # Signal other threads to stop
                return

        # Since stop even is set means target is hit
        logging.info("Since Target hit, Canceling SL order...")
        self.order_manager.cancel_order(self.ce_sl_order)
        self.order_manager.cancel_order(self.pe_sl_order)

    def sl_order_placement_stage(self):
        logging.info("SL Order Placement Stage...")
        total_loss_points = self.sl_atr_rule * self.atr_range
        logging.info(f"total_loss_points: {total_loss_points}")

        ce_selling_price = 0
        pe_selling_price = 0
        for order in ShortStraddle.orders_id_map.values():
            if order.trading_symbol == self.ce_option_symbol:
                ce_selling_price = order.average_price
            if order.trading_symbol == self.pe_option_symbol:
                pe_selling_price = order.average_price
        logging.info(f"ce_selling_price: {ce_selling_price}, pe_selling_price: {pe_selling_price}")
        if ce_selling_price == 0 or pe_selling_price == 0:
            logging.info("Not Placing SL order (not able to get ce/pe selling price")
            return

        sl_points_for_ce = ce_selling_price / (ce_selling_price + pe_selling_price) * total_loss_points
        sl_points_for_pe = pe_selling_price / (ce_selling_price + pe_selling_price) * total_loss_points
        self.ce_sl_price = Utils.round_to_exchange_price(ce_selling_price + sl_points_for_ce)
        self.pe_sl_price = Utils.round_to_exchange_price(pe_selling_price + sl_points_for_pe)
        self.ce_sl_order = Order(variety=KiteConstants.VARIETY_REGULAR,
                      exchange=KiteConstants.EXCHANGE_NFO,
                      trading_symbol=self.ce_option_symbol,
                      transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
                      quantity=self.lot_size * self.get_num_lots(),
                      product=KiteConstants.PRODUCT_MIS,
                      order_type=KiteConstants.ORDER_TYPE_SLM,
                      trigger_price=self.ce_sl_price
                      )

        self.pe_sl_order = Order(variety=KiteConstants.VARIETY_REGULAR,
                      exchange=KiteConstants.EXCHANGE_NFO,
                      trading_symbol=self.pe_option_symbol,
                      transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
                      quantity=self.lot_size * self.get_num_lots(),
                      product=KiteConstants.PRODUCT_MIS,
                      order_type=KiteConstants.ORDER_TYPE_SLM,
                      trigger_price=self.pe_sl_price
                      )
        # Place the orders
        ShortStraddle.orders_id_map[self.order_manager.place_order(self.ce_sl_order)] = self.ce_sl_order
        ShortStraddle.orders_id_map[self.order_manager.place_order(self.pe_sl_order)] = self.pe_sl_order

        # Change state to SL order placed
        ShortStraddle.strategy_state = ShortStraddleState.SL_ORDER_PLACED

    def entry_order_placement_stage(self):
        logging.info("Entry Order Placement Stage...")

        order_ce = self.create_entry_order(self.ce_option_symbol)
        order_pe = self.create_entry_order(self.pe_option_symbol)

        logging.info("Waiting for market to open")
        while datetime.datetime.now() <= self.start_datetime:
            continue
        #  Fire the orders and store to dict
        ShortStraddle.orders_id_map[self.order_manager.place_order(order_ce)] = order_ce
        ShortStraddle.orders_id_map[self.order_manager.place_order(order_pe)] = order_pe

        ShortStraddle.total_points_sold = order_ce.average_price + order_pe.average_price
        # Change state to Entry Order Placed
        ShortStraddle.strategy_state = ShortStraddleState.ENTRY_ORDER_PLACED

    def create_entry_order(self, option_symbol):
        order = Order(variety=KiteConstants.VARIETY_REGULAR,
                      exchange=KiteConstants.EXCHANGE_NFO,
                      trading_symbol=option_symbol,
                      transaction_type=KiteConstants.TRANSACTION_TYPE_SELL,
                      quantity=self.lot_size * self.get_num_lots(),
                      product=KiteConstants.PRODUCT_MIS,
                      order_type=KiteConstants.ORDER_TYPE_MARKET,
                      )
        return order


    def get_atr_range(self):
        # get historic data and calculate atr
        fyers_handle = Controller.get_fyers_login()
        df_daily = fyers_handle.get_data(symbol=self.fyers_spot_symbol, resolution="1D", range_from=self.today_date-timedelta(days=50), range_to=self.today_date-timedelta(days=1))
        atr = AverageTrueRange(df_daily['High'], df_daily['Low'], df_daily['Close'],
                               window=self.atr_window).average_true_range()
        df_daily['ATR'] = atr
        df_daily.set_index("Datetime", inplace=True)
        atr_data = df_daily['ATR']
        logging.info(f"Calculated ATR: {float(atr_data.values[-1])}")
        return float(atr_data.values[-1])

    def get_num_lots(self):
        return 1

    def get_lot_size(self, exchange, ce_option_symbol):
        data = self.broker_handler.instruments(exchange)
        for instr in data:
            if instr['tradingsymbol'] == ce_option_symbol:
                return instr['lot_size']
        return None

    def get_atm_options_symbols_n_laod_lot_size(self):
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
        logging.info(self.broker_handler.ohlc("NFO:"+ce_option_symbol))
        logging.info(self.broker_handler.ohlc("NFO:"+pe_option_symbol))
        # calculate lot_size
        self.lot_size = self.get_lot_size("NFO", ce_option_symbol)
        logging.info(f"Lot Size: {self.lot_size}")

        return ce_option_symbol, pe_option_symbol