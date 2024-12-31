import logging
import time
from datetime import timedelta
from core.Controller import Controller
from ordermgmt.OrderModifyParams import OrderModifyParams
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
import pickle
from instruments.Instruments import Instruments
# Set a threshold for timeout in seconds
TIMEOUT_THRESHOLD = 10  # e.g., 10 seconds

LOG_WIDTH = 80
def log_heading(msg):
    logging.info("\n" +
                 "###########################################".center(LOG_WIDTH) + "\n" +
                 f"{msg}".center(LOG_WIDTH) + "\n" +
                 "###########################################".center(LOG_WIDTH) + "\n"
                 )

def run_in_threads(*functions):
    threads = []
    for func in functions:
        thread = threading.Thread(target=func, name=f"{func.__name__}_thread")
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

class ShortStraddleTrade:
    def __init__(self):
        self.ce_option_symbol = None
        self.pe_option_symbol = None
        self.ce_token = None
        self.pe_token = None

        self.ce_entry_order = None
        self.pe_entry_order = None

        self.ce_sl_order = None
        self.pe_sl_order = None

        self.ce_target_order = None
        self.pe_target_order = None

        self.ce_square_off_order = None
        self.pe_square_off_order = None

        self.total_sold_points = None # sum of call average price and put average price
        self.total_loss_points = None
        self.total_target_points = None

        self.pe_sl_price = None
        self.ce_sl_price = None

        self.lot_size = None
        self.quantity = None
        self.order_id_mapping = {}
        self.latest_ticks = {}

class ShortStraddle(BaseStrategy):
    def __init__(self, params):
        super().__init__("Short Straddle")

        self.today_date = datetime.datetime.now().date()
        self.day = datetime.datetime.now().strftime("%A")

        # Load Strategy Parameters
        self.square_off_time = params.auto_exit_times[self.day]
        self.atr_window = params.atr_window
        self.instrument = params.instrument
        self.spot_symbol = params.spot_symbol
        self.start_datetime = datetime.datetime.combine(self.today_date, params.straddle_start_times[self.day])
        self.stop_datetime = datetime.datetime.combine(self.today_date, params.auto_exit_times[self.day])
        self.expiry_rule = params.expiry_rules[self.day]
        self.sl_atr_rule = params.sl_atr_rule[self.day]
        self.rr = params.rrs[self.day]
        self.pre_market_datetime = datetime.datetime.combine(self.today_date, params.pre_market_time)
        self.options_gap = params.options_gap
        self.expiry_day = params.expiry_day
        self.fyers_spot_symbol = params.fyers_spot_symbol

        self.isFnO = True
        self.broker_handler = Controller.get_broker_login().get_broker_handle()
        self.atr_range = self.get_atr_range()
        self.order_manager = ZerodhaOrderManager()

        # Start ticker
        self.ticker = ZerodhaTicker()
        self.ticker.start_ticker()
        # Register listener
        self.ticker.register_order_update_listener(self.order_update_listener)

        self.strategy_state = ShortStraddleState.STRADDLE_STARTED
        # Create a shared event for signaling
        self.stop_event = threading.Event()
        self.target_achieved = threading.Event()
        # Trade object
        self.trade = ShortStraddleTrade()
        self.last_tick_time = time.time()

    def save_state(self, filepath=f"states_log_files/short_straddle_state_{datetime.datetime.now().date()}.pkl"):
        state = {"trade": self.trade,
                 "strategy_state" : self.strategy_state,
                 "stop_event": True if self.stop_event.is_set() else False,
                 "target_achieved": True if self.target_achieved.is_set() else False
                 }

        with open(filepath, "wb") as f:
            pickle.dump(state, f)
        logging.info("State saved successfully.")

    def load_state(self, filepath=f"states_log_files/short_straddle_state_{datetime.datetime.now().date()}.pkl"):
        try:
            with open(filepath, "rb") as f:
                state = pickle.load(f)
            self.trade = state["trade"]
            self.strategy_state = state["strategy_state"]
            if state.get("stop_event"):
                self.stop_event.set()
            if state.get("target_achieved"):
                self.target_achieved.set()

            logging.info("State loaded successfully.")
        except FileNotFoundError:
            logging.warning("State file not found. Starting fresh.")


    def wait_for_key(self, order_id, timeout=60):
        logging.info("Waiting for an order to update")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if order_id in self.trade.order_id_mapping:
                return True
        return False

    def order_update_listener(self, data):
        logging.info(f"order update: {data}")
        # Wait for key
        if not self.wait_for_key(data['order_id']):
            logging.info("Order update failed.")
            return

        order = self.trade.order_id_mapping[data['order_id']]
        order.order_status = data['status']
        order.average_price = data['average_price']
        order.filled_qty = data['filled_quantity']
        order.pending_qty = data['pending_quantity']
        order.order_timestamp = data['order_timestamp']
        order.exchange_timestamp = data['exchange_timestamp']
        order.message = data['status_message']
        logging.info("Order updated successfully.")

    def _wait_for_start_time(self):
        if datetime.datetime.now() < self.start_time:
            wait_time = Utils.get_epoch(self.start_time) - Utils.get_epoch(datetime.datetime.now())
            if wait_time >= 50:
                wait_time -= 20
                logging.info(f"Waiting for {wait_time} seconds to reach Start time...")
                time.sleep(wait_time)

    def process(self):
        try:
            log_heading(f"Short Straddle in {self.instrument} starting...")
            # Load previous state if available
            self.load_state()
            time.sleep(1)

            if self.strategy_state == ShortStraddleState.STRADDLE_STARTED:
                self._wait_for_start_time()

                # Entry Order Stage
                self.prepare_entry_orders()
                self.entry_order_placement_stage()
                self.validate_entry_orders()

            if self.strategy_state == ShortStraddleState.ENTRY_ORDER_PLACED:
                # Place SL Order Stage
                self.sl_order_placement_stage()
                self.validate_sl_orders()

            if self.strategy_state == ShortStraddleState.SL_ORDER_PLACED:
                log_heading("Starting Parallel Target and SL Phase")
                # Run the chase_target_phase and wait_for_sl_to_hit in parallel
                run_in_threads(self.chase_target_phase, self.wait_for_sl_to_hit, self.monitor_ticks)

            # Check state and proceed
            if (self.strategy_state == ShortStraddleState.CE_SL_HIT) or (self.strategy_state == ShortStraddleState.PE_SL_HIT):
                # Set target for other
                self.set_target_for_remaining_position()
                self.wait_for_sl_or_target_to_hit()

            if (self.strategy_state != ShortStraddleState.BOTH_SL_HIT) and (self.strategy_state != ShortStraddleState.TARGET_HIT):
                # Means some position is open
                self.auto_square_off()

            logging.info("Stopping Short Straddle.")
            time.sleep(10)
            self.save_state()
            self.ticker.stop_ticker()
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt detected. Saving state before exiting...")
            self.save_state()  # Save state before exiting
            logging.info("State saved successfully. Exiting...")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            self.save_state()  # Save state even for other exceptions

    def auto_square_off(self):
        # Cancel open position:
        # Possibility: Both position Open ->
        # Single Position Open -> CE_SL_HIT, PE_SL_HIT
        # No position Open -> Both SL hit, or Target HIT
        log_heading("Auto Square Off Phase")
        ce_order = self.create_market_order(self.trade.ce_option_symbol, KiteConstants.TRANSACTION_TYPE_BUY)
        pe_order = self.create_market_order(self.trade.pe_option_symbol, KiteConstants.TRANSACTION_TYPE_BUY)

        ce_order_id = None
        pe_order_id = None
        if self.strategy_state == ShortStraddleState.SL_ORDER_PLACED:
            # Both orders are still running
            logging.info("Since both CE and PE positions are active, proceeding to square off both!")
            ce_order_id = self.order_manager.place_order(ce_order)
            pe_order_id = self.order_manager.place_order(pe_order)
        elif self.strategy_state == ShortStraddleState.CE_SL_HIT:
            logging.info("Since only PE position is active, proceeding to square off.")
            pe_order_id = self.order_manager.place_order(pe_order)
        elif self.strategy_state == ShortStraddleState.PE_SL_HIT:
            logging.info("Since only CE position is active, proceeding to square off.")
            ce_order_id = self.order_manager.place_order(ce_order)

        if ce_order_id is not None:
            self.trade.order_id_mapping[ce_order_id] = ce_order
            self.trade.ce_square_off_order = ce_order
        if pe_order_id is not None:
            self.trade.order_id_mapping[pe_order_id] = pe_order
            self.trade.pe_square_off_order = pe_order

    def create_limit_order(self, symbol, side, price):
        return Order(variety=KiteConstants.VARIETY_REGULAR,
                      exchange=KiteConstants.EXCHANGE_NFO,
                      trading_symbol=symbol,
                      transaction_type=side,
                      quantity=self.trade.quantity,
                      product=KiteConstants.PRODUCT_MIS,
                      order_type=KiteConstants.ORDER_TYPE_LIMIT,
                      price=price,
                      )

    def create_market_order(self, symbol, side):
        return Order(variety=KiteConstants.VARIETY_REGULAR,
                      exchange=KiteConstants.EXCHANGE_NFO,
                      trading_symbol=symbol,
                      transaction_type=side,
                      quantity=self.trade.quantity,
                      product=KiteConstants.PRODUCT_MIS,
                      order_type=KiteConstants.ORDER_TYPE_MARKET,
                      )

    def wait_for_sl_or_target_to_hit(self):
        """
        case: 2. State: CE SL HIT (PE trade running, with SL and Target) -> Cancel SL/Target of PE, and square off PE
        case: 3. State: PE SL HIT (CE trade running, with SL and Target) -> Cancel SL/Target of CE, and square off CE
        """
        log_heading("Waiting for SL or Target To hit")
        if self.strategy_state == ShortStraddleState.CE_SL_HIT:
            # PE trade is running with SL and Target
            sl_order = self.trade.pe_sl_order
            target_order = self.trade.pe_target_order
        else:
            # CE trade is running with SL and Target
            sl_order = self.trade.ce_sl_order
            target_order = self.trade.ce_target_order

        while (datetime.datetime.now() <= self.stop_datetime) and (sl_order.order_status != OrderStatus.COMPLETE) and (target_order.order_status != OrderStatus.COMPLETE):
            continue

        # Three possibility: Stop time reached, SL HIT, Target Hit.
        if datetime.datetime.now() > self.stop_datetime:
            # Stop Time reached, Cancel Target, SL, and running position
            logging.info("Stop time reached. Exiting...")
            self.order_manager.cancel_order(sl_order)
            self.order_manager.cancel_order(target_order)
        else:
            # Target or SL hit
            if sl_order.order_status == OrderStatus.COMPLETE:
                logging.info("SL order Hit!, Cancelling Target Order.")
                self.order_manager.cancel_order(target_order)
                self.strategy_state = ShortStraddleState.BOTH_SL_HIT
            else:
                logging.info("Target Hit!, Cancelling SL Order.")
                self.order_manager.cancel_order(sl_order)
                self.strategy_state = ShortStraddleState.TARGET_HIT


    def set_target_for_remaining_position(self):
        """
            Sets the target order for the remaining position.
        """
        log_heading("Setting target order for the running position")
        if self.strategy_state == ShortStraddleState.CE_SL_HIT:
            target_price = Utils.round_to_exchange_price(
                max(0.05, self.trade.total_sold_points - self.trade.total_target_points - self.trade.ce_sl_price)
            )
            self.trade.pe_target_order = self.create_limit_order(self.trade.pe_option_symbol, KiteConstants.TRANSACTION_TYPE_BUY, target_price)
            order_id =  self.order_manager.place_order(self.trade.pe_target_order)
            self.trade.order_id_mapping[order_id] = self.trade.pe_target_order
        else:
            target_price = Utils.round_to_exchange_price(
                max(0.05, self.trade.total_sold_points - self.trade.total_target_points - self.trade.pe_sl_price)
            )
            self.trade.ce_target_order = self.create_limit_order(self.trade.ce_option_symbol, KiteConstants.TRANSACTION_TYPE_BUY, target_price)
            order_id = self.order_manager.place_order(self.trade.ce_target_order)
            self.trade.order_id_mapping[order_id] = self.trade.ce_target_order

    def monitor_ticks(self):
        """
        Monitor function to check if ticks are being received within the timeout threshold.
        """
        logging.info("Monitor ticks started.")
        while (not self.stop_event.is_set()) and (datetime.datetime.now() <= self.stop_datetime):
            time.sleep(1)  # Check every second
            if time.time() - self.last_tick_time > TIMEOUT_THRESHOLD:
                logging.warning("No ticks received for a while!")
        logging.info("Monitor ticks stopping.")

    def chase_target_phase(self):
        log_heading("Starting Target Chasing Phase...")
        # Keep your target orders ready.
        ce_target_order = self.create_market_order(self.trade.ce_option_symbol, KiteConstants.TRANSACTION_TYPE_BUY)
        pe_target_order = self.create_market_order(self.trade.pe_option_symbol, KiteConstants.TRANSACTION_TYPE_BUY)

        # Register callback function
        self.ticker.register_listeners(self.target_check_callback)
        # Register symbols
        self.ticker.register_symbol([self.trade.ce_option_symbol, self.trade.pe_option_symbol])

        # Chase for target until stop event is set
        while (not self.stop_event.is_set()) and (datetime.datetime.now() <= self.stop_datetime):
            if self.target_achieved.is_set():
                self.stop_event.set()  # Signal other threads to stop

                logging.info("Chase Target Phase: Target Achieved Signal Received!, Firing Target Orders")
                # Fire the orders
                ce_order_id = self.order_manager.place_order(ce_target_order)
                pe_order_id = self.order_manager.place_order(pe_target_order)
                self.trade.order_id_mapping[ce_order_id] = ce_target_order
                self.trade.order_id_mapping[pe_order_id] = pe_target_order

                # unregister the symbols
                self.ticker.unregister_symbol([self.trade.ce_option_symbol, self.trade.pe_option_symbol])
                # Change state to Target Hit
                self.strategy_state = ShortStraddleState.TARGET_HIT
                return
        logging.info("Chase Target Phase: Stopping Target Chasing, Unregistering Symbols")
        # unregister the symbols
        self.ticker.unregister_symbol([self.trade.ce_option_symbol, self.trade.pe_option_symbol])

    def target_check_callback(self, tick):
        # Update latest ticks
        self.trade.latest_ticks[tick['instrument_token']] = tick['last_price']
        self.last_tick_time = time.time()
        ltp_sum = self.trade.latest_ticks[self.trade.ce_token] + self.trade.latest_ticks[self.trade.pe_token]

        if (self.trade.total_sold_points - ltp_sum) >= self.trade.total_target_points:
            self.target_achieved.set()

    def wait_for_sl_to_hit(self):
        """
            Monitors the stop-loss (SL) orders and updates the strategy state when an SL is hit.
        """
        log_heading("Waiting for an SL order to be hit...")

        while (not self.stop_event.is_set()) and (datetime.datetime.now() <= self.stop_datetime):
            # Check if either CE or PE SL order is complete
            if (self.trade.ce_sl_order.order_status == OrderStatus.COMPLETE) or (self.trade.pe_sl_order.order_status == OrderStatus.COMPLETE):
                # if true meaning SL hit
                if self.trade.ce_sl_order.order_status == OrderStatus.COMPLETE:
                    logging.info("CE SL Hit!")
                    # Modify SL of PE
                    order_modification_params = OrderModifyParams(
                        Utils.round_to_exchange_price(self.trade.pe_entry_order.average_price + 10),
                        Utils.round_to_exchange_price(self.trade.pe_entry_order.average_price))
                    self.order_manager.modify_order(self.trade.pe_sl_order, order_modification_params)
                    self.strategy_state = ShortStraddleState.CE_SL_HIT
                else :
                    logging.info("PE SL Hit!")
                    # Modify SL of CE
                    order_modification_params = OrderModifyParams(
                        Utils.round_to_exchange_price(self.trade.ce_entry_order.average_price + 10),
                        Utils.round_to_exchange_price(self.trade.ce_entry_order.average_price))
                    self.order_manager.modify_order(self.trade.ce_sl_order, order_modification_params)
                    self.strategy_state = ShortStraddleState.PE_SL_HIT
                self.stop_event.set()  # Signal other threads to stop
                return
        # Stop event is set, cancel Stop loss orders
        logging.info("Wait for SL to hit: Stopping Waiting for SL to hit, Canceling SL order...")
        self.order_manager.cancel_order(self.trade.ce_sl_order)
        self.order_manager.cancel_order(self.trade.pe_sl_order)

    def sl_order_placement_stage(self):
        log_heading("SL Order Placement Stage")

        # Get entry prices
        ce_sold_price = self.trade.ce_entry_order.average_price
        pe_sold_price =  self.trade.pe_entry_order.average_price
        logging.info(f"CE SOLD PRICE: {ce_sold_price}, PE SOLD PRICE: {pe_sold_price}")

        # Calculate SL points
        sl_prices = self.calculate_sl_prices(ce_sold_price, pe_sold_price, self.trade.total_loss_points)
        self.trade.ce_sl_price = sl_prices["ce"]
        self.trade.pe_sl_price = sl_prices["pe"]

        # Create SL orders
        self.trade.ce_sl_order = self.create_sl_orders(self.trade.ce_option_symbol, self.trade.ce_sl_price)
        self.trade.pe_sl_order = self.create_sl_orders(self.trade.pe_option_symbol, self.trade.pe_sl_price)

        # Place orders
        pe_order_id = self.order_manager.place_order(self.trade.pe_sl_order)
        ce_order_id = self.order_manager.place_order(self.trade.ce_sl_order)
        if (pe_order_id is None) or (ce_order_id is None):
            raise ValueError("SL Order Placement Stage Failed")
        self.trade.order_id_mapping[ce_order_id] = self.trade.ce_sl_order
        self.trade.order_id_mapping[pe_order_id] = self.trade.pe_sl_order
        # Change state to SL order placed
        self.strategy_state = ShortStraddleState.SL_ORDER_PLACED

    @staticmethod
    def calculate_sl_prices(ce_price, pe_price, total_loss_points):
        """Calculate the SL prices for CE and PE options."""
        total_price = ce_price + pe_price
        ce_sl_points = ce_price / total_price * total_loss_points
        pe_sl_points = pe_price / total_price * total_loss_points
        return {
            "ce": Utils.round_to_exchange_price(ce_price + ce_sl_points),
            "pe": Utils.round_to_exchange_price(pe_price + pe_sl_points),
        }

    def create_sl_orders(self, symbol, sl_price):
        """Create an SL order with the given parameters."""
        return Order(
            variety=KiteConstants.VARIETY_REGULAR,
            exchange=KiteConstants.EXCHANGE_NFO,
            trading_symbol=symbol,
            transaction_type=KiteConstants.TRANSACTION_TYPE_BUY,
            quantity=self.trade.quantity,
            product=KiteConstants.PRODUCT_MIS,
            order_type=KiteConstants.ORDER_TYPE_SL,
            price=Utils.round_to_exchange_price(sl_price + 10),
            trigger_price=sl_price,
        )

    def prepare_entry_orders(self):
        log_heading("Preparing Entry Orders")
        self.trade.ce_option_symbol, self.trade.pe_option_symbol = self.get_atm_options_symbols()

        # Calculate total loss points
        self.trade.total_loss_points = self.sl_atr_rule * self.atr_range
        logging.info(f"Total Loss Points: {self.trade.total_loss_points}")

        # calculate lot_size
        self.trade.lot_size = self.get_lot_size("NFO", self.trade.ce_option_symbol)
        logging.info(f"Lot Size: {self.trade.lot_size}")

        # Calculate quantity to be traded
        self.trade.quantity = self.calculate_quantity()
        logging.info(f"Quantity: {self.trade.quantity}")

        # Calculate Total Target Points
        self.trade.total_target_points = self.rr * self.trade.total_loss_points
        logging.info(f"Total Target Points: {self.trade.total_target_points}")

        self.trade.ce_token = Instruments.symbol_to_token_map[self.trade.ce_option_symbol]
        self.trade.pe_token = Instruments.symbol_to_token_map[self.trade.pe_option_symbol]
        self.trade.latest_ticks[self.trade.ce_token] = 10000  # infinite
        self.trade.latest_ticks[self.trade.pe_token] = 10000  # infinite

        self.trade.ce_entry_order = self.create_market_order(self.trade.ce_option_symbol, KiteConstants.TRANSACTION_TYPE_SELL)
        self.trade.pe_entry_order = self.create_market_order(self.trade.pe_option_symbol, KiteConstants.TRANSACTION_TYPE_SELL)

    def entry_order_placement_stage(self):
        log_heading("Entry Order Placement Stage")

        logging.info("Waiting for Start time.")
        while datetime.datetime.now() <= self.start_datetime:
            continue
        #  Fire the orders and store in a dict
        ce_order_id = self.order_manager.place_order(self.trade.ce_entry_order)
        pe_order_id = self.order_manager.place_order(self.trade.pe_entry_order)

        if (ce_order_id is None) or (pe_order_id is None):
            raise ValueError("Entry Order Placement Stage Failed")
        # Map the orders
        self.trade.order_id_mapping[ce_order_id] = self.trade.ce_entry_order
        self.trade.order_id_mapping[pe_order_id] = self.trade.pe_entry_order

    # noinspection PyUnresolvedReferences
    def validate_entry_orders(self):
        log_heading("Validating Entry Orders")
        logging.info("Waiting for orders to get updated...")
        # start timeout to get orders updated
        orders_updated = False
        timeout = 120
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ((self.trade.ce_entry_order.average_price != 0) and (self.trade.pe_entry_order.average_price != 0)) and (self.trade.ce_entry_order.average_price is not None) and (self.trade.pe_entry_order.average_price is not None) and (self.trade.ce_entry_order.average_price is not None):
                orders_updated = True
                break
        if not orders_updated:
            raise ValueError("Entry Order Validation Failed, orders not updated")

        logging.info("Validation Successful")
        # Now Assign total points sold
        self.trade.total_sold_points = self.trade.ce_entry_order.average_price + self.trade.pe_entry_order.average_price
        # Change state to Entry Order Placed
        self.strategy_state = ShortStraddleState.ENTRY_ORDER_PLACED

    def validate_sl_orders(self):
        log_heading("Validating Stop Loss Orders")
        logging.info("Waiting for orders to get updated...")
        # Start timeout to get orders updated
        orders_updated = False
        timeout = 120
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ((self.trade.ce_sl_order.order_status == OrderStatus.TRIGGER_PENDING) or (self.trade.ce_sl_order.order_status == OrderStatus.COMPLETE)) and ((self.trade.pe_sl_order.order_status == OrderStatus.TRIGGER_PENDING) or (self.trade.pe_sl_order.order_status == OrderStatus.COMPLETE)):
                orders_updated = True
                break
        if not orders_updated:
            raise ValueError("Stop Loss Order Validation Failed, orders not updated")
        logging.info("Validation Successful")

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

    def calculate_quantity(self):
        if self.trade.lot_size == 25:
            return int(self.trade.lot_size * 3)
        elif self.trade.lot_size == 75:
            return int(self.trade.lot_size * 1)

    def get_lot_size(self, exchange, ce_option_symbol):
        data = self.broker_handler.instruments(exchange)
        for instr in data:
            if instr['tradingsymbol'] == ce_option_symbol:
                return instr['lot_size']
        raise ValueError("Unable to get lot size")

    def get_atm_options_symbols(self):
        # Now fetch Nifty Opening price, calculate strike price and create trade
        open_price = self.broker_handler.ohlc(self.spot_symbol)[self.spot_symbol]['last_price']
        # # get strike price and expiry_date
        atm_strike_price = Utils.nearest_strike_price(open_price, self.options_gap)
        expiry_date = Utils.get_weekly_expiry(self.today_date, self.expiry_day, self.expiry_rule)
        # # form symbols for both ce and pe
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

        return ce_option_symbol, pe_option_symbol