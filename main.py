import logging

import datetime
from fastapi import FastAPI, BackgroundTasks
from starlette.responses import RedirectResponse

from routes import login


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum level of messages to capture
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format of log messages
    handlers=[
        logging.FileHandler(f"logs/{datetime.datetime.now().date()}_logs_test.log", mode="a"),  # Log to a file named 'app.log'
        logging.StreamHandler()         # Also log to the terminal
    ],
    force=True
)
LOG_WIDTH = 80
def log_heading(msg):
    logging.info("\n" +
                 "###########################################".center(LOG_WIDTH) + "\n" +
                 f"{msg}".center(LOG_WIDTH) + "\n" +
                 "###########################################".center(LOG_WIDTH) + "\n"
                 )

app = FastAPI()
app.include_router(login.router)

@app.get("/")
async def root(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_algo)
    return RedirectResponse(url="/login")

async def run_algo():
    from core.Controller import Controller
    from core.Algo import Algo
    log_heading("Starting Algo...")
    Controller.handle_broker_login()
    Algo.start_algo()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=7000)