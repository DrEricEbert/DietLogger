import pandas as pd
from database import get_all_entries
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def export_to_csv(path):
    data = get_all_entries()
    df = pd.DataFrame(data, columns=["ID", "Datum", "Gewicht", "Zucker", "Schlaf", "Befinden", "Notizen"])
    df.to_csv(path, index=False, encoding='utf-8')

def import_from_csv(path):
    df = pd.read_csv(path)
    entries = []
    for _, row in df.iterrows():
        entries.append({
            "timestamp": row["Datum"],
            "weight": row["Gewicht"],
            "blood_sugar": row["Zucker"],
            "sleep_hours": row["Schlaf"],
            "mood": row["Befinden"],
            "notes": row["Notizen"]
        })
    return entries

def export_to_pdf(path):
    data = get_all_entries()
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Health Tracker Export")
    y -= 20

    headers = ["Datum", "Gewicht", "Zucker", "Schlaf", "Befinden", "Notizen"]
    for header in headers:
        c.drawString(50 + headers.index(header) * 80, y, header)
    y -= 20

    for row in data:
        for i, val in enumerate(row[1:]):
            c.drawString(50 + i * 80, y, str(val))
        y -= 20
        if y < 40:
            c.showPage()
            y = height - 40

    c.save()