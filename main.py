import logging
from core.Controller import Controller
import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum level of messages to capture
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format of log messages
    handlers=[
        logging.FileHandler(f"logs/{datetime.datetime.now().date()}_logs_temp.log", mode="a"),  # Log to a file named 'app.log'
        logging.StreamHandler()         # Also log to the terminal
    ],
    force=True
)
Controller.handle_broker_login()

from core.Algo import Algo
Algo.start_algo()