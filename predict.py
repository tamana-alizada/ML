"""
predict.py
Batch prediction script:
  1. Connects to the SQLite database
  2. Reads all input_data rows that don't yet have a prediction
  3. Loads the trained Pipeline (SimpleImputer + LogisticRegression)
  4. Generates predictions (0 = No Risk, 1 = At Risk)
  5. Writes results to the predictions table with a UTC timestamp
"""

import sqlite3
import logging
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "lung_cancer.db")
MODEL_PATH = os.path.join(BASE_DIR, "model.joblib")

FEATURES = [
    "age",
    "gender",
    "pack_years",
    "radon_exposure",
    "asbestos_exposure",
    "secondhand_smoke_exposure",
    "copd_diagnosis",
    "alcohol_consumption",
    "family_history",
]

LABELS = {0: "No Risk ✅", 1: "At Risk ⚠️"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_model():
    log.info("Loading model from %s", MODEL_PATH)
    model = joblib.load(MODEL_PATH)
    log.info("Model loaded: %s", type(model).__name__)
    return model


def fetch_unpredicted(cur):
    """Return rows from input_data that have no entry in predictions yet."""
    feature_cols = ", ".join(f"i.{f}" for f in FEATURES)
    cur.execute(f"""
        SELECT i.id, {feature_cols}
        FROM   input_data i
        LEFT JOIN predictions p ON p.id = i.id
        WHERE  p.id IS NULL
    """)
    return cur.fetchall()


# ── Main batch routine ────────────────────────────────────────────────────────

def run_batch():
    log.info("=" * 60)
    log.info("Batch prediction started")

    if not os.path.exists(DB_PATH):
        log.error("Database not found: %s — run init_db.py first.", DB_PATH)
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    rows = fetch_unpredicted(cur)
    if not rows:
        log.info("No new rows to predict. Exiting.")
        con.close()
        return

    log.info("Found %d unpredicted row(s).", len(rows))

    model = load_model()

    ids      = [row[0] for row in rows]
    features = pd.DataFrame([list(row[1:]) for row in rows], columns=FEATURES)

    predictions = model.predict(features)          # 0 or 1
    timestamp   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    records = [
        (int(row_id), int(pred), LABELS[int(pred)], timestamp)
        for row_id, pred in zip(ids, predictions)
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO predictions (id, prediction, prediction_label, prediction_timestamp) VALUES (?, ?, ?, ?)",
        records,
    )
    con.commit()

    log.info("Stored %d prediction(s) at %s.", len(records), timestamp)
    for row_id, pred in zip(ids, predictions):
        log.info("  patient_id=%d → %d (%s)", row_id, int(pred), LABELS[int(pred)])

    con.close()
    log.info("Batch prediction finished.")
    log.info("=" * 60)


if __name__ == "__main__":
    run_batch()
