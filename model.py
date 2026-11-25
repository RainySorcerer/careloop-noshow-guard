import csv
import sqlite3

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from build_db import DB, OUTPUT


def main():
    if not DB.is_file():
        raise SystemExit("Run python build_db.py first.")
    with sqlite3.connect(DB) as db:
        data = pd.read_sql_query("SELECT * FROM appointments ORDER BY visit_date, id", db)

    # Train on earlier months and test on the last month.
    test_month = data["visit_date"].str[:7].max()
    test = data[data["visit_date"].str.startswith(test_month)]
    train = data[~data["visit_date"].str.startswith(test_month)]

    numbers = ["lead_days", "age", "distance_km", "fee_inr", "prior_no_shows", "reminder"]
    categories = ["channel", "visit_type"]
    prep = ColumnTransformer([
        ("numbers", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numbers),
        ("categories", OneHotEncoder(handle_unknown="ignore"), categories),
    ])
    model = make_pipeline(prep, LogisticRegression())
    model.fit(train, train["no_show"])
    probabilities = model.predict_proba(test)[:, 1]

    # Use a fixed cutoff so the test labels never influence it.
    flags = probabilities >= 0.35
    print(f"Test month: {test_month}, {len(test)} bookings")
    print(f"ROC-AUC: {roc_auc_score(test['no_show'], probabilities):.3f}")
    print(f"Precision: {precision_score(test['no_show'], flags, zero_division=0):.1%}")
    print(f"Recall: {recall_score(test['no_show'], flags, zero_division=0):.1%}")
    print(f"Flagged: {flags.sum()}")

    with (OUTPUT / "risk_scores.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["appointment_id", "no_show", "risk_probability", "flag"])
        for appointment_id, actual, probability, flag in zip(
            test["id"], test["no_show"], probabilities, flags
        ):
            writer.writerow([appointment_id, actual, probability, int(flag)])


if __name__ == "__main__":
    main()
