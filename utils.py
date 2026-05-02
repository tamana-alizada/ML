"""
utils.py
CLI helper for manual testing and data management.

Commands:
    python utils.py view              — show all predictions
    python utils.py add               — insert 5 new random patient rows
    python utils.py add <n>           — insert n new random patient rows
    python utils.py add_patient       — add one specific patient interactively
    python utils.py reset             — clear predictions table (rows re-predicted next run)

Feature reference:
    age                         (float, e.g. 55.0)
    gender                      (0=Female, 1=Male)
    pack_years                  (float, e.g. 20.5)
    radon_exposure              (0=No, 1=Yes)
    asbestos_exposure           (0=No, 1=Yes)
    secondhand_smoke_exposure   (0=No, 1=Yes)
    copd_diagnosis              (0=No, 1=Yes)
    alcohol_consumption         (float drinks/week, e.g. 7.0)
    family_history              (0=No, 1=Yes)
"""

import sqlite3
import os
import random
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "lung_cancer.db")

FEATURES = [
    "age", "gender", "pack_years", "radon_exposure",
    "asbestos_exposure", "secondhand_smoke_exposure",
    "copd_diagnosis", "alcohol_consumption", "family_history",
]


def get_con():
    return sqlite3.connect(DB_PATH)


def add_rows(n=5):
    con = get_con()
    cur = con.cursor()
    cols = ", ".join(FEATURES)
    ph   = ", ".join("?" * len(FEATURES))
    for _ in range(n):
        row = [
            round(random.uniform(40, 80), 1),
            random.randint(0, 1),
            round(random.uniform(0, 50), 1),
            random.randint(0, 1),
            random.randint(0, 1),
            random.randint(0, 1),
            random.randint(0, 1),
            round(random.uniform(0, 20), 1),
            random.randint(0, 1),
        ]
        cur.execute(f"INSERT INTO input_data ({cols}) VALUES ({ph})", row)
    con.commit()
    con.close()
    print(f"Inserted {n} new patient row(s) into input_data.")


def add_patient():
    """Prompt for each feature and insert one specific patient."""
    print("\nEnter patient data (press Enter to leave blank / use NULL):")
    values = []
    for feat in FEATURES:
        raw = input(f"  {feat}: ").strip()
        values.append(float(raw) if raw else None)

    con = get_con()
    cur = con.cursor()
    cols = ", ".join(FEATURES)
    ph   = ", ".join("?" * len(FEATURES))
    cur.execute(f"INSERT INTO input_data ({cols}) VALUES ({ph})", values)
    new_id = cur.lastrowid
    con.commit()
    con.close()
    print(f"Patient inserted with id={new_id}. Run predict.py to generate prediction.")


def view_predictions():
    con = get_con()
    cur = con.cursor()
    cur.execute("""
        SELECT
            p.id,
            i.age, i.gender, i.pack_years, i.copd_diagnosis, i.family_history,
            p.prediction_label,
            p.prediction_timestamp
        FROM predictions p
        JOIN input_data i ON i.id = p.id
        ORDER BY p.id
    """)
    rows = cur.fetchall()
    con.close()

    if not rows:
        print("No predictions yet. Run: python predict.py")
        return

    print(f"\n{'ID':>4}  {'Age':>5}  {'Gender':>6}  {'PkYrs':>6}  {'COPD':>5}  {'FamHx':>6}  {'Result':<18}  Timestamp")
    print("-" * 90)
    for row in rows:
        pid, age, gender, pack_years, copd, fam_hx, label, ts = row
        g = "M" if gender == 1 else "F"
        c = "Yes" if copd == 1 else "No"
        f = "Yes" if fam_hx == 1 else "No"
        print(f"{pid:>4}  {age:>5.1f}  {g:>6}  {pack_years:>6.1f}  {c:>5}  {f:>6}  {label:<18}  {ts}")

    print(f"\nTotal: {len(rows)} prediction(s).")

    # Summary stats
    at_risk = sum(1 for r in rows if r[6] == "At Risk ⚠️")
    print(f"At Risk: {at_risk} | No Risk: {len(rows) - at_risk}")


def reset_predictions():
    con = get_con()
    cur = con.cursor()
    cur.execute("DELETE FROM predictions")
    con.commit()
    con.close()
    print("Predictions table cleared. Rows will be re-predicted on next run.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "view"

    if cmd == "add":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        add_rows(n)
    elif cmd == "add_patient":
        add_patient()
    elif cmd == "reset":
        reset_predictions()
    else:
        view_predictions()
