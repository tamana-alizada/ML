"""
scheduler.py
Runs the batch prediction pipeline on a fixed schedule.

Default: every 5 minutes.
Override via environment variable:
    PREDICT_INTERVAL_MINUTES=10 python scheduler.py

Alternative: use the system cron (see README.md for crontab snippet).
"""

import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler

from predict import run_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

INTERVAL_MINUTES = int(os.getenv("PREDICT_INTERVAL_MINUTES", 5))


def main():
    log.info("Scheduler starting — interval: every %d minute(s).", INTERVAL_MINUTES)

    # Run once immediately on startup
    log.info("Running initial prediction pass...")
    run_batch()

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_batch,
        trigger="interval",
        minutes=INTERVAL_MINUTES,
        id="batch_predict",
        name="Lung Cancer Batch Prediction",
    )

    log.info("Scheduler active. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
