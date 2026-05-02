"""
init_db.py
Initializes the SQLite database with input_data and predictions tables,
and seeds input_data with realistic sample patient rows.

Features:
    age                         (years, e.g. 45–80)
    gender                      (0 = Female, 1 = Male)
    pack_years                  (cigarette pack-years, e.g. 0–60)
    radon_exposure              (0 = No, 1 = Yes)
    asbestos_exposure           (0 = No, 1 = Yes)
    secondhand_smoke_exposure   (0 = No, 1 = Yes)
    copd_diagnosis              (0 = No, 1 = Yes)
    alcohol_consumption         (drinks/week, e.g. 0–20)
    family_history              (0 = No, 1 = Yes)
"""

import sqlite3
import random
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lung_cancer.db")

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


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    con = get_connection()
    cur = con.cursor()

    # input_data: one column per feature
    feature_cols = ",\n    ".join(f"{f} REAL" for f in FEATURES)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS input_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {feature_cols}
        )
    """)

    # predictions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id                   INTEGER PRIMARY KEY,
            prediction           INTEGER NOT NULL,
            prediction_label     TEXT    NOT NULL,
            prediction_timestamp TEXT    NOT NULL,
            FOREIGN KEY (id) REFERENCES input_data(id)
        )
    """)

    con.commit()

    # Seed with 20 realistic sample patients
    cur.execute("SELECT COUNT(*) FROM input_data")
    if cur.fetchone()[0] == 0:
        print("Seeding input_data with 20 sample patient rows...")
        cols = ", ".join(FEATURES)
        ph   = ", ".join("?" * len(FEATURES))
        for _ in range(20):
            row = [
                round(random.uniform(40, 80), 1),   # age
                random.randint(0, 1),                # gender
                round(random.uniform(0, 50), 1),     # pack_years
                random.randint(0, 1),                # radon_exposure
                random.randint(0, 1),                # asbestos_exposure
                random.randint(0, 1),                # secondhand_smoke_exposure
                random.randint(0, 1),                # copd_diagnosis
                round(random.uniform(0, 20), 1),     # alcohol_consumption
                random.randint(0, 1),                # family_history
            ]
            cur.execute(f"INSERT INTO input_data ({cols}) VALUES ({ph})", row)
        con.commit()
        print("Seeding complete.")
    else:
        print("input_data already has rows — skipping seed.")

    con.close()
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
