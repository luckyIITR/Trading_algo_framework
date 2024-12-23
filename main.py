import logging
from core.Controller import Controller


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
Controller.handle_broker_login()

from core.Algo import Algo
Algo.start_algo()