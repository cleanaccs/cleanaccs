import os
from datetime import datetime, timedelta, timezone, date
import logging

from cleanup.docextract.scan_data import load_scan_data
from cleanup.main_tg import TelegramScanner
from config.scan_config import load_config
from config.logger import setup_logger

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    setup_logger()
    now = datetime.now(timezone.utc)
    logging.info("Starting at %s", now.isoformat())

    config, config_exists = load_config("config.yaml")
    if not config_exists:
        logging.warning("Config file config.yaml not found, using default configuration.")
    logging.info("Running scan with config:\n%s", config)

    scan_data = load_scan_data(config)

    if len(scan_data) == 0:
        logging.warning("No scan data found, exiting.")
        exit()

    os.makedirs(config.paths.cache_dir, exist_ok=True)

    if config.telegram.enabled:
        telegram_scanner = TelegramScanner(config, scan_data)
        telegram_scanner.scan()
