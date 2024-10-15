from datetime import datetime, timedelta, timezone, date
import logging

from config.scan_config import load_config
from config.logger import setup_logger

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    setup_logger()
    now = datetime.now(timezone.utc)
    logging.info("Starting at %s", now.isoformat())

    config, config_exists = load_config("config.json")
    if not config_exists:
        logging.error("Config file config.yaml not found, using default configuration.")
    logging.info("Running scan with config:\n%s", config)
