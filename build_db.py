import csv
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
DB = OUTPUT / "careloop.sqlite"


def read_csv(name):
    with (ROOT / "data" / name).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def clean_appointments(clinics):
    rows = []
    seen = set()
    for row in read_csv("appointments.csv"):
        appointment_id = row["appointment_id"]
        if appointment_id in seen:
            continue
        if row["clinic_id"] not in clinics or row["status"] not in {"Attended", "No-Show"}:
            continue
        try:
            booked = date.fromisoformat(row["booked_on"])
            visit = date.fromisoformat(row["appt_date"])
            age = int(row["age"]) if row["age"] else None
            distance = float(row["distance_km"]) if row["distance_km"] else None
            fee = int(row["fee_inr"])
            prior = int(row["prior_no_shows"])
        except ValueError:
            continue
        if visit < booked or row["reminder_sent"] not in {"Yes", "No"}:
            continue
        seen.add(appointment_id)
        rows.append((
            appointment_id, row["patient_id"], row["clinic_id"], visit.isoformat(),
            (visit - booked).days, age if age is not None and 1 <= age <= 100 else None,
            distance, fee, row["booking_channel"].strip().title(), row["visit_type"],
            int(row["reminder_sent"] == "Yes"), prior, int(row["status"] == "No-Show"),
        ))
    return rows


def main():
    clinics = {row["clinic_id"]: row for row in read_csv("clinics.csv")}
    rows = clean_appointments(clinics)
    OUTPUT.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS clinics (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY, patient_id TEXT NOT NULL,
                clinic_id TEXT NOT NULL REFERENCES clinics(id),
                visit_date TEXT NOT NULL, lead_days INTEGER NOT NULL,
                age INTEGER, distance_km REAL, fee_inr INTEGER NOT NULL,
                channel TEXT NOT NULL, visit_type TEXT NOT NULL,
                reminder INTEGER NOT NULL, prior_no_shows INTEGER NOT NULL,
                no_show INTEGER NOT NULL
            );
        """)
        db.execute("DELETE FROM appointments")
        db.execute("DELETE FROM clinics")
        db.executemany("INSERT INTO clinics VALUES (?, ?, ?)", [
            (key, row["clinic_name"], row["city"]) for key, row in clinics.items()
        ])
        db.executemany(
            "INSERT INTO appointments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    print(f"Saved {len(rows)} appointments and {len(clinics)} clinics to {DB.name}")


if __name__ == "__main__":
    main()
