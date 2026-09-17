import io
import csv
from datetime import datetime

def generate_timesheet_csv(records) -> io.BytesIO:
    """Generates an Excel-ready UTF-8 CSV timesheet with BOM."""
    output = io.StringIO()
    # Write UTF-8 BOM so Excel opens Cyrillic properly
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "Табельдік №",
        "Т.А.Ә. (ФИО)",
        "Лауазымы",
        "Күні",
        "Кірген уақыты",
        "Шыққан уақыты",
        "Жалпы жұмыс сағаты",
        "Статусы",
        "Тексеру тәсілі"
    ])

    for r in records:
        writer.writerow([
            r.get("emp_num", ""),
            r.get("full_name", ""),
            r.get("position", ""),
            r.get("date", ""),
            r.get("check_in", "—"),
            r.get("check_out", "—"),
            r.get("hours", "—"),
            r.get("status", "Жұмыста"),
            r.get("method", "Face ID + QR")
        ])

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    return mem
