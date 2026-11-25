import sqlite3

from build_db import DB

REPORTS = {
    "Overall": """
        SELECT COUNT(*) AS bookings, SUM(no_show) AS missed
        FROM appointments
    """,
    "By clinic": """
        SELECT c.name, COUNT(*) AS bookings, SUM(a.no_show) AS missed,
               ROUND(100.0 * AVG(a.no_show), 1) AS missed_pct
        FROM appointments AS a
        JOIN clinics AS c ON c.id = a.clinic_id
        GROUP BY c.id, c.name
        ORDER BY AVG(a.no_show) DESC
    """,
    "By lead time": """
        SELECT CASE
                   WHEN lead_days <= 7 THEN '0-7'
                   WHEN lead_days <= 14 THEN '8-14'
                   WHEN lead_days <= 30 THEN '15-30'
                   ELSE '31+'
               END AS band,
               COUNT(*) AS bookings, SUM(no_show) AS missed,
               ROUND(100.0 * AVG(no_show), 1) AS missed_pct
        FROM appointments
        GROUP BY band
        ORDER BY MIN(lead_days)
    """,
    "By month": """
        SELECT SUBSTR(visit_date, 1, 7) AS month, COUNT(*) AS bookings,
               SUM(no_show) AS missed, ROUND(100.0 * AVG(no_show), 1) AS missed_pct
        FROM appointments
        GROUP BY month
        ORDER BY month
    """,
}


def main():
    if not DB.is_file():
        raise SystemExit("Run python build_db.py first.")
    with sqlite3.connect(DB) as db:
        for title, query in REPORTS.items():
            result = db.execute(query)
            print(f"\n{title}")
            print(" | ".join(column[0] for column in result.description))
            for row in result:
                print(" | ".join(map(str, row)))


if __name__ == "__main__":
    main()
