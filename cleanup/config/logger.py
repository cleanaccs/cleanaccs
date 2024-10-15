import os
import logging
from datetime import datetime


def setup_logger():
    os.makedirs("logs", exist_ok=True)

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/app_{current_time}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
