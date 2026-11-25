# CareLoop No-Show Guard

CareLoop looks at missed clinic appointments and estimates which upcoming bookings may need a confirmation call.

## Run the local reports

From the project folder, run these with Python 3.

```sh
python build_db.py
python report.py
```

The first script loads the supplied CSVs into `output/careloop.sqlite` using Python's built-in SQLite library. It keeps one usable row per appointment ID and leaves missing ages and distances empty. The second prints counts by clinic, lead time, and month. Run the first script again whenever the CSVs change.

The supplied data gives 990 bookings and 218 missed visits. Hadapsar had 39 missed visits out of 143 bookings. Across all clinics, 26 of the 43 bookings made at least 31 days ahead were missed.

## Try the risk model

```sh
python -m pip install pandas scikit-learn
python model.py
```

The model trains on earlier months and tests on the last month. It fills missing numeric values using medians from training and writes predictions to `output/risk_scores.csv`. The demo uses a fixed cutoff of 0.35. The score assumes reminders have already been sent or skipped.

June had 165 test bookings. The model flagged 37 and caught 19 of the 35 no-shows. A clinic could start with confirmation calls for the highest scores and record whether patients confirm or reschedule. The data does not establish that sending a reminder causes attendance to improve.

## Optional follow-up notes

Install `google-genai`, set `GEMINI_API_KEY` and `GEMINI_MODEL` to an available model ID, then run `python followup.py`. The script sends the first ten supplied notes to Gemini, skipping blanks and notes without a matching missed appointment. Use only notes you are allowed to send to the service. Check the per-row status in `output/followup.csv`. The replies are for review and stay out of the risk model.

## Credit

Original project and supplied data credited to RainySorcerer. This SQLite rebuild was written with AI assistance.
