import datetime

class NiftyShortStraddleParams:
    # Parameters
    instrument = 'NIFTY'
    spot_symbol = "NSE:NIFTY 50"
    fyers_spot_symbol = "NSE:NIFTY50-INDEX"
    expiry_day = "Thursday"
    options_gap = 50
    pre_market_time = datetime.time(9, 8)
    start_time = datetime.time(9, 15)
    square_off_time = datetime.time(15, 0)
    atr_window = 9
    expiry_rules = {  # choose expiry day which expiry to pick
        'Friday': 'nearest',
        'Monday': 'nearest',
        'Tuesday': 'nearest',
        'Wednesday': 'nearest',
        'Thursday': 'next_nearest'
    }
    sl_atr_rule = {
        'Friday': 0.15,
        'Monday': 0.15,
        'Tuesday': 0.15,
        'Wednesday': 0.15,
        'Thursday': 0.15
    }
    rr = 1  # Risk reward ratio