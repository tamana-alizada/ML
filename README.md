# Lung Cancer Risk — Batch Prediction Pipeline

A production-style ML batch prediction system using **SQLite**, **scikit-learn**, and **APScheduler**.

The model is a `Pipeline(SimpleImputer → LogisticRegression)` that predicts **lung cancer risk** from 9 clinical features.

| Output | Meaning |
|--------|---------|
| `0` — No Risk ✅ | Patient shows low risk indicators |
| `1` — At Risk ⚠️ | Patient shows elevated risk indicators |

---

## Project Structure

```
lung_cancer_pipeline/
├── model.joblib      # Trained sklearn Pipeline (9 features)
├── lung_cancer.db    # SQLite database (auto-created by init_db.py)
├── init_db.py        # Creates tables + seeds 20 sample patients
├── predict.py        # Core batch prediction script
├── scheduler.py      # Runs predict.py on a schedule (every 5 min)
├── utils.py          # CLI helper: add / view / reset
├── requirements.txt
└── README.md
```

---

## Database Schema

```sql
CREATE TABLE input_data (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    age                         REAL,
    gender                      REAL,   -- 0=Female, 1=Male
    pack_years                  REAL,
    radon_exposure              REAL,   -- 0=No, 1=Yes
    asbestos_exposure           REAL,   -- 0=No, 1=Yes
    secondhand_smoke_exposure   REAL,   -- 0=No, 1=Yes
    copd_diagnosis              REAL,   -- 0=No, 1=Yes
    alcohol_consumption         REAL,   -- drinks per week
    family_history              REAL    -- 0=No, 1=Yes
);

CREATE TABLE predictions (
    id                   INTEGER PRIMARY KEY,
    prediction           INTEGER NOT NULL,   -- 0 or 1
    prediction_label     TEXT    NOT NULL,   -- "No Risk ✅" or "At Risk ⚠️"
    prediction_timestamp TEXT    NOT NULL,
    FOREIGN KEY (id) REFERENCES input_data(id)
);
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialise the database
```bash
python init_db.py
```

### 3. Run a single prediction batch
```bash
python predict.py
```

### 4. Start the scheduler (runs every 5 minutes)
```bash
python scheduler.py
```

Override interval:
```bash
set PREDICT_INTERVAL_MINUTES=10 && python scheduler.py   # Windows
PREDICT_INTERVAL_MINUTES=10 python scheduler.py          # Mac/Linux
```

---

## Managing Data

```bash
python utils.py view              # view all predictions
python utils.py add               # add 5 random patient rows
python utils.py add 10            # add 10 random patient rows
python utils.py add_patient       # add one specific patient (prompted)
python utils.py reset             # clear predictions (re-run next batch)
```

### Adding a real patient (example)
```
python utils.py add_patient

  age: 63
  gender: 1
  pack_years: 30
  radon_exposure: 1
  asbestos_exposure: 0
  secondhand_smoke_exposure: 0
  copd_diagnosis: 1
  alcohol_consumption: 5
  family_history: 1

Patient inserted with id=21. Run predict.py to generate prediction.
```

---

## Scheduling via System Cron (alternative)

```bash
crontab -e
```

```cron
*/5 * * * * python3 /path/to/lung_cancer_pipeline/predict.py >> /path/to/predict.log 2>&1
```

---

## How It Works

```
┌──────────────────────────────────────────────────────┐
│                   scheduler.py                       │
│           (APScheduler — every 5 min)                │
└───────────────────────┬──────────────────────────────┘
                        │ calls
                        ▼
┌──────────────────────────────────────────────────────┐
│                    predict.py                        │
│                                                      │
│  1. Connect to lung_cancer.db (SQLite)               │
│  2. SELECT rows from input_data with no prediction   │
│  3. Load model.joblib (Pipeline)                     │
│  4. model.predict(features) → [0, 1, ...]           │
│  5. INSERT into predictions with timestamp           │
└──────────────────────────────────────────────────────┘
              │
  ┌───────────┴────────────┐
  ▼                        ▼
input_data table      predictions table
(9 clinical cols)     (id, prediction,
                       prediction_label,
                       prediction_timestamp)
```

---

## Model Details

| Property     | Value                              |
|--------------|------------------------------------|
| Type         | sklearn Pipeline                   |
| Step 1       | SimpleImputer (strategy=median)    |
| Step 2       | LogisticRegression (balanced, L2)  |
| Features     | 9 clinical risk factors            |
| Classes      | 0 = No Risk, 1 = At Risk           |
| Framework    | scikit-learn                       |
