import logging
import datetime
from core.Algo import Algo

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum level of messages to capture
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format of log messages
    handlers=[
        logging.FileHandler(f"logs/{datetime.datetime.now().date()}_logs.log", mode="a"),  # Log to a file named 'app.log'
        logging.StreamHandler()         # Also log to the terminal
    ],
    force=True
)

Algo.start_algo()