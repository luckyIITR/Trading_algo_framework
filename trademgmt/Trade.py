import logging
from utils.Utils import Utils
from models.ProductType import ProductType
from ordermgmt.KiteConstants import KiteConstants
from trademgmt.TradeState import TradeState
from datetime import datetime

class Trade:
    def __init__(self, trading_symbol):
        self.exchange = "NSE"
        self.trade_id = Utils.generate_trade_id()
        self.trading_symbol = trading_symbol
        self.strategy = None
        self.direction = None
        self.product_type = ProductType.MIS
        self.is_futures = False  # Futures trade
        self.is_options = False  # Options trade
        self.option_type = None  # CE/PE. Applicable only if isOptions is True
        self.requested_order_entry_type = KiteConstants.ORDER_TYPE_MARKET
        self.requested_price = None
        self.trigger_price = None
        self.entry_price = None
        self.qty = 0
        self.stop_loss = None  # This is the current stop loss.
        self.target = None

        self.trade_state = TradeState.CREATED
        self.createTimestamp = datetime.now()  # Timestamp when the trade is created (Not triggered)
        self.trade_active_time = None # Timestamp when the trade gets triggered and order placed
        self.trade_close_time = None # Timestamp when the trade ended
        self.exit_price = 0
        self.exit_reason = None # SL/Target/SquareOff/Any Other

        self.entry_order = None # Object of Type ordermgmt.Order
        self.sl_order = None # Object of Type ordermgmt.Order
        self.target_order = None # Object of Type ordermgmt.Order

    def __str__(self):
        """Provide a readable string representation of the Trade object."""
        return (
            f"Trade(trade_id={self.trade_id}, trading_symbol={self.trading_symbol}, strategy={self.strategy}, "
            f"direction={self.direction}, product_type={self.product_type}, is_futures={self.is_futures}, "
            f"is_options={self.is_options}, option_type={self.option_type}, requested_order_entry_type={self.requested_order_entry_type}, "
            f"requested_price={self.requested_price}, entry_price={self.entry_price}, qty={self.qty}, trade_state={self.trade_state}, "
            f"createTimestamp={self.createTimestamp}, trade_active_time={self.trade_active_time}, trade_close_time={self.trade_close_time}, "
            f"exit_price={self.exit_price}, exit_reason={self.exit_reason}, entry_order={self.entry_order}, "
            f"sl_order={self.sl_order}, target_order={self.target_order})"
        )